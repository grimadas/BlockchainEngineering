from random import sample

from p2psimpy.messages import Hello, PeerList, Ping, RequestPeers, Pong
from p2psimpy.peer import Peer
from p2psimpy.services.base import BaseHandler, BaseRunner


class BaseConnectionManager(BaseHandler, BaseRunner):
    def __init__(self, peer: Peer, **kwargs):
        """
        Service  to
            - ping peers
            - disconnect unresponsive peers
        Create basic peer connection manager
        Attributes
          ping_interval: int - Trigger connection verification every ms ping_interval. Default: 500 ms
          max_silence: int - Maximum time to tolerate peer being unresponsive before action. Default: 3000 ms
          min_keep_time: int - Minimum time to keep connection between peers. Default: 3000 ms
        """
        BaseRunner.__init__(self, peer, **kwargs)

        # Connection Manager Attributes
        self.ping_interval = kwargs.pop('ping_interval', 500)
        self.max_silence = kwargs.pop('max_silence', 3000)
        self.min_keep_time = kwargs.pop('min_keep_time', 3000)

        self.known_peers = set()  # All known peers
        self.disconnected_peers = set()  # Connected in past, now disconnected

        def disconnect_cb(p, other):
            assert p == self.peer
            self.disconnected_peers.add(other)

        self.peer.disconnect_callbacks.append(disconnect_cb)

    @property
    def messages(self):
        return Hello, Ping, Pong,

    def handle_message(self, msg):
        """
        Respond to the arriving messages
        """
        if isinstance(msg, Hello):
            self.recv_hello(msg)
        if isinstance(msg, Ping):
            self.peer.send(msg.sender, Pong(self.peer))

    def ping_peers(self):
        """
        ping peers that are connected
        """
        for other in self.peer.connections:
            if self.env.now - self.peer.last_seen.get(other, 0) > self.ping_interval:
                self.peer.send(other, Ping(sender=self.peer))

    def recv_hello(self, msg):
        """
        Receive introduction message
        """
        other = msg.sender
        if other not in self.peer.connections:
            self.peer.connect(other)
            self.peer.send(other, Hello(self.peer))

    def disconnect_unresponsive_peers(self):
        now = self.env.now
        for other in list(self.connected_peers):
            if other not in self.peer.last_seen:
                self.peer.last_seen[other] = now  # assume it was recently added
            elif now - self.peer.last_seen[other] > self.max_silence:
                if self.logger:
                    self.logger.warning("%s: %s not responding", self.env.now, repr(other))
                self.peer.disconnect(other)

    @property
    def connected_peers(self):
        return self.peer.connections.keys()

    def run(self):
        while True:
            self.ping_peers()
            self.disconnect_unresponsive_peers()
            yield self.env.timeout(self.ping_interval)


class P2PConnectionManager(BaseConnectionManager):

    def __init__(self, peer: Peer, **kwargs):
        """
        Service  to
            - ping peers
            - disconnect unresponsive peers
            - request and manage list of known peers

        Create basic peer connection manager
        Attributes
          ping_interval: int - Trigger connection verification every ms ping_interval. Default: 500 ms
          max_silence: int - Maximum time to tolerate peer being unresponsive before action. Default: 3000 ms
          min_keep_time: int - Minimum time to keep connection between peers. Default: 3000 ms

          peer_list_number - Number of peers in a PeerList request upon requesting peers, Default: 1
          min_peers - minimum number of peers to have in connections. Default: 15
          max_peers - maximum number of peers to have in connections. Default: 25
          peer_batch_request - number of peers to request peers at the same time. Default: 5
        """
        BaseConnectionManager.__init__(self, peer, **kwargs)

        # Connection Manager Attributes
        self.peer_list_number = kwargs.pop('peer_list_number', 1)
        self.min_peers = kwargs.pop('min_peers', 15)
        self.max_peers = kwargs.pop('max_peers', 25)
        self.peer_batch_request = kwargs.pop('peer_batch_request', 5)

    @property
    def messages(self):
        return super().messages + (RequestPeers, PeerList,)

    def handle_message(self, msg):
        """
        Respond to the arriving messages
        """
        super().handle_message(msg)
        if isinstance(msg, PeerList):
            self.recv_peerlist(msg)
        if isinstance(msg, RequestPeers):
            peer_sample = sample(self.peer.connections.keys(),
                                 min(self.peer_list_number, len(self.peer.connections.keys())))
            reply = PeerList(self.peer, peer_sample)
            # self.sample_peers(self.config.peer_list_number))
            self.peer.send(msg.sender, reply)


    def recv_peerlist(self, msg):
        """
        Receive list of peers
        """
        peers = msg.data
        peers.discard(self.peer)  # discard own peer
        self.known_peers.update(peers)

    @property
    def peer_candidates(self):
        candidates = self.known_peers.difference(set(self.connected_peers))
        return candidates.difference(self.disconnected_peers)

    def recv_hello(self, msg):
        """
        Receive introduction message
        """
        other = msg.sender
        if other not in self.peer.connections:
            self.peer.connect(other)
            self.peer.send(other, Hello(self.peer))
            self.peer.send(other, RequestPeers(self.peer))

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
                if self.env.now - start_time > self.min_keep_time:
                    if self.logger:
                        self.logger.warning("%s: %s too slow", self.env.now, repr(other))
                    self.peer.disconnect(other)
                    self.disconnected_peers.add(other)
                    break

    def monitor_connections(self):
        # CASE: too few peers
        if len(self.connected_peers) < self.min_peers:
            needed = self.min_peers - len(self.connected_peers)
            if self.logger:
                self.logger.warning("%s: Not enough peers, fetching more (%s, %s)",
                                    self.env.now, len(self.connected_peers), self.min_peers)
            candidates = self.peer_candidates
            if len(candidates) < needed:
                self.peer.gossip(RequestPeers(self.peer), self.peer_batch_request, exclude_bootstrap=False)
            for other in list(candidates)[:needed]:
                self.peer.bootstrap_connect(other)

        # CASE: too many peers
        if len(self.connected_peers) > self.max_peers:
            if self.logger:
                self.logger.warning("%s: Too many peers connected (%s, %s)",
                                    self.env.now, len(self.connected_peers), self.max_peers)
            num = max(0, len(self.connected_peers) - self.max_peers)
            for i in range(num):
                self.disconnect_slowest_peer()

    def run(self):
        while True:
            self.monitor_connections()
            self.ping_peers()
            self.disconnect_unresponsive_peers()
            yield self.env.timeout(self.ping_interval)