import logging
from random import sample

from p2psimpy.config import ConnectionConfig
from p2psimpy.messages import Hello, PeerList, Ping, RequestPeers, Pong
from p2psimpy.peer import Peer
from p2psimpy.services.base import BaseHandler, BaseRunner


class ConnectionManager(BaseHandler, BaseRunner):
    """
    Service  to
     - ping peers
     - disconnect unresponsive peers
     - request and manage list of known peers
    """

    def __init__(self, peer: Peer, config: ConnectionConfig):
        BaseRunner.__init__(self, peer, config)
        self.last_seen = dict()  # a map: peer -> timestamp
        self.known_peers = set()  # All known peers
        self.disconnected_peers = set()  # Connected in past, now disconnected
        self.logger = logging.getLogger(repr(self))

        def disconnect_cb(p, other):
            assert p == self.peer
            self.disconnected_peers.add(other)

        self.peer.disconnect_callbacks.append(disconnect_cb)

    @property
    def messages(self):
        return Hello, RequestPeers, PeerList, Ping, Pong,

    def handle_message(self, msg):
        """
        Respond to the arriving messages
        """
        self.last_seen[msg.sender] = self.env.now
        if isinstance(msg, Hello):
            self.recv_hello(msg)
        if isinstance(msg, PeerList):
            self.recv_peerlist(msg)
        if isinstance(msg, Ping):
            self.peer.send(msg.sender, Pong(self.peer))
        if isinstance(msg, RequestPeers):
            peer_sample = sample(self.peer.connections.keys(),
                                 min(self.config.peer_list_number, len(self.peer.connections.keys())))
            reply = PeerList(self.peer, peer_sample)
            # self.sample_peers(self.config.peer_list_number))
            self.peer.send(msg.sender, reply)

    def ping_peers(self):
        """
        ping peers that are connected
        """
        for other in self.peer.connections:
            if self.env.now - self.last_seen.get(other, 0) > self.config.ping_interval:
                self.peer.send(other, Ping(sender=self.peer))

    def recv_hello(self, msg):
        """
        Receive introduction message
        """
        other = msg.sender
        if other not in self.peer.connections:
            self.peer.connect(other)
            self.peer.send(other, Hello(self.peer))
            self.peer.send(other, RequestPeers(self.peer))

    def recv_peerlist(self, msg):
        """
        Receive list of peers
        """
        peers = msg.data
        peers.discard(self.peer)  # discard own peer
        self.known_peers.update(peers)

    def disconnect_unresponsive_peers(self):
        now = self.env.now
        for other in list(self.connected_peers):
            if other not in self.last_seen:
                self.last_seen[other] = now  # assume it was recently added
            elif now - self.last_seen[other] > self.config.max_silence:
                self.logger.warning("%s: %s not responding", self.env.now, repr(other))
                self.peer.disconnect(other)

    def sample_peers(self, f):
        s_peers = list(self.known_peers.difference(self.disconnected_peers))
        return sample(s_peers, min(f, len(s_peers)))

    @property
    def connected_peers(self):
        return self.peer.connections.keys()

    @property
    def peer_candidates(self):
        candidates = self.known_peers.difference(set(self.connected_peers))
        return candidates.difference(self.disconnected_peers)

    def disconnect_slowest_peer(self):
        """
        Try to disconnect the slowest peer
        be tolerant, so that a PeerList can be sent
        """
        bw = lambda other_peer: self.peer.connections[other_peer].bandwidth
        if self.connected_peers:
            # get worst peer (based on latency)
            sorted_peers = sorted([(bw(p), p) for p in self.connected_peers
                                   if p not in self.disconnected_peers])
            for bw, other in sorted_peers:
                start_time = self.peer.connections[other].start_time
                if self.env.now - start_time > self.config.min_keep_time:
                    self.logger.warning("%s: %s too slow", self.env.now, repr(other))
                    self.peer.disconnect(other)
                    self.disconnected_peers.add(other)
                    break

    def monitor_connections(self):
        # CASE: too few peers
        if len(self.connected_peers) < self.config.min_peers:
            needed = self.config.min_peers - len(self.connected_peers)
            self.logger.warning("%s: Not enough peers, fetching more (%s, %s)",
                                self.env.now, len(self.connected_peers), self.config.min_peers)
            candidates = self.peer_candidates
            if len(candidates) < needed:
                self.peer.gossip(RequestPeers(self.peer), self.config.peer_batch_request_number)
            for other in list(candidates)[:needed]:
                self.peer.bootstrap_connect(other)

        # CASE: too many peers
        if len(self.connected_peers) > self.config.max_peers:
            self.logger.warning("%s: Too many peers connected (%s, %s)",
                                self.env.now, len(self.connected_peers), self.config.max_peers)
            num = max(0, len(self.connected_peers) - self.config.max_peers)
            for i in range(num):
                self.disconnect_slowest_peer()

    def run(self):
        while True:
            self.ping_peers()
            self.disconnect_unresponsive_peers()
            self.monitor_connections()
            yield self.env.timeout(self.config.ping_interval)
