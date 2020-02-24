import simpy

from .consts import MBit, PEER_LATENCY_MIN, PEER_BANDWIDTH_MAX
from .messages import BaseMessage


class Connection(object):
    """
    Models the data transfer between peers and the implied latency
    """

    def __init__(self, env, sender, receiver):
        self.env = env
        self.sender = sender
        self.receiver = receiver
        self.start_time = env.now

    def __repr__(self):
        return '<Connection %r -> %r>' % (self.sender, self.receiver)

    @property
    def round_trip(self):
        # basically backbone latency
        # evenly distributed pseudo random round trip times
        return self.random_uniform_latency()

    def random_uniform_latency(self):
        rt_min, rt_max = PEER_LATENCY_MIN, PEER_BANDWIDTH_MAX  # ms
        return (rt_min + (id(self.sender) + id(self.receiver)) % (rt_max - rt_min)) / 1000.

    @property
    def bandwidth(self):
        return min(self.sender.bandwidth_ul, self.receiver.bandwidth_dl)

    def send(self, msg, connect=False):
        """
        fire and forget
        i.e. we don't get notified if the message was not delivered

        connect : deliver message even if not connected yet, similar to UDP
        """

        def _transfer():
            bytes = msg.size
            delay = bytes / self.sender.bandwidth_ul
            delay += bytes / self.receiver.bandwidth_dl
            delay += self.round_trip / 2
            yield self.env.timeout(delay)
            if self.receiver.is_connected(msg.sender) or connect:
                self.receiver.msg_queue.put(msg)

        self.env.process(_transfer())


class BaseService(object):
    """
    Added to Peers to provide services like
    - connection management
    - monitoring
    - working on tasks

    """
    def handle_message(self, receiving_peer, msg):
        "this callable is added as a listener to Peer.listeners"
        pass


class Peer(object):
    # Default bandwidth value
    bandwidth_ul = 2.4 * MBit  # bytes/sec
    bandwidth_dl = 16 * MBit  # bytes/sec

    def __init__(self, name, env):
        self.name = name
        self.env = env
        # Message queue
        self.msg_queue = simpy.Store(env)
        self.connections = dict()
        self.active = True
        self.services = []  # Service.handle_message(self, msg) called on message
        self.disconnect_callbacks = []
        env.process(self.run())

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def __lt__(self, other):
        return self.name < other.name

    def connect(self, other):
        if not self.is_connected(other):
            self.connections[other] = Connection(self.env, self, other)
            if not other.is_connected(self):
                other.connect(self)

    def disconnect(self, other):
        if self.is_connected(other):
            del self.connections[other]
            if other.is_connected(self):
                other.disconnect(self)
            for cb in self.disconnect_callbacks:
                cb(self, other)

    def is_connected(self, other):
        return other in self.connections

    def receive(self, msg):
        assert isinstance(msg, BaseMessage)
        for s in self.services:
            assert isinstance(s, BaseService)
            s.handle_message(self, msg)

    def send(self, receiver, msg):
        # fire and forget
        assert msg.sender == self
        self.connections[receiver].send(msg)

    def broadcast(self, msg):
        for other in self.connections:
            self.send(other, msg)

    def run(self):
        while True:
            # check network for new messages
            msg = yield self.msg_queue.get()
            self.receive(msg)
