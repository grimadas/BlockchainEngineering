from .peer import BaseService, Connection
from .messages import Ping, Pong, RequestPeers, PeerList, Hello
from .consts import CONNECTION_PING_INTERVAL, CONNECTION_MAX_SILENCE,\
    CONNECTION_MIN_PEERS, CONNECTION_MAX_PEERS, CONNECTION_MIN_KEEP_TIME


###### Services ################

class PingHandler(BaseService):
    def handle_message(self, peer, msg):
        if isinstance(msg, Ping):
            peer.send(msg.sender, Pong(peer))


class PeerRequestHandler(BaseService):
    def handle_message(self, peer, msg):
        if isinstance(msg, RequestPeers):
            reply = PeerList(peer, peer.connections.keys())
            peer.send(msg.sender, reply)


class ConnectionManager(BaseService):
    """
    Service  to
     - ping peers
     - disconnect unresponsive peers
     - request and manage list of known peers
    """

    def __init__(self, peer):
        self.peer = peer
        self.last_seen = dict()  # peer -> timestamp
        self.env.process(self.run())
        self.known_peers = set()
        self.disconnected_peers = set()

        def disconnect_cb(peer, other):
            assert peer == self.peer
            self.disconnected_peers.add(other)

        self.peer.disconnect_callbacks.append(disconnect_cb)

    def __repr__(self):
        return "ConnectionManager(%s)" % self.peer.name

    @property
    def env(self):
        return self.peer.env

    def handle_message(self, peer, msg):
        self.last_seen[msg.sender] = self.env.now
        if isinstance(msg, Hello):
            self.recv_hello(msg)
        if isinstance(msg, PeerList):
            self.recv_peerlist(msg)

    def ping_peers(self):
        for other in self.peer.connections:
            if self.env.now - self.last_seen.get(other, 0) > CONNECTION_PING_INTERVAL:
                self.peer.send(other, Ping(sender=self.peer))

    def recv_hello(self, msg):
        other = msg.sender
        if not other in self.peer.connections:
            self.peer.connect(other)
            self.peer.send(other, Hello(self.peer))
            self.peer.send(other, RequestPeers(self.peer))

    def recv_peerlist(self, msg):
        peers = msg.data
        peers.discard(self.peer)
        self.known_peers.update(peers)

    def connect_peer(self, other):
        # create ad-hoc connection and send Hello
        cnx = Connection(self.env, self.peer, other)
        cnx.send(Hello(self.peer), connect=True)

    def disconnect_unresponsive_peers(self):
        now = self.env.now
        for other in self.peer.connections.keys():
            if not other in self.last_seen:
                # assume it was recently added
                self.last_seen[other] = now
            elif now - self.last_seen[other] > CONNECTION_MAX_SILENCE:
                self.peer.disconnect(other)

    @property
    def connected_peers(self):
        return self.peer.connections.keys()

    @property
    def peer_candidates(self):
        candidates = self.known_peers.difference(set(self.connected_peers))
        return candidates.difference(self.disconnected_peers)

    def disconnect_slowest_peer(self):
        """
        Called if we have to many connections
        Try to disconnect the slowest peer
        be tolerant, so that a PeerList can be sent
        """
        bw = lambda other: self.peer.connections[other].bandwidth
        if self.connected_peers:
            # get worst peer (based on latency)
            sorted_peers = sorted([(bw(p), p) for p in self.connected_peers
                                   if p not in self.disconnected_peers])
            for bw, other in sorted_peers:
                start_time = self.peer.connections[other].start_time
                if self.env.now - start_time > CONNECTION_MIN_KEEP_TIME:
                    self.peer.disconnect(other)
                    self.disconnected_peers.add(other)
                    break

    def monitor_connections(self):
        # CASE: too few peers
        if len(self.connected_peers) < CONNECTION_MIN_PEERS:
            needed = CONNECTION_MIN_PEERS - len(self.connected_peers)
            candidates = self.peer_candidates
            if len(candidates) < needed:
                self.peer.broadcast(RequestPeers(self.peer))
            for other in list(candidates)[:needed]:
                self.connect_peer(other)

        # CASE: too many peers
        if len(self.connected_peers) > CONNECTION_MAX_PEERS:
            num = max(0, len(self.connected_peers) - CONNECTION_MAX_PEERS)
            for i in range(num):
                self.disconnect_slowest_peer()

    def run(self):
        while True:
            self.ping_peers()
            self.disconnect_unresponsive_peers()
            self.monitor_connections()
            yield self.env.timeout(CONNECTION_PING_INTERVAL)
