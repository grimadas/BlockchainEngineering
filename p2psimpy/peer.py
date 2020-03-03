import logging
import random

from simpy import Store

from p2psimpy.config import PeerConfig
from p2psimpy.messages import BaseMessage, Hello
from p2psimpy.network import Connection
from p2psimpy.services.base import BaseService


class Peer:

    def __init__(self, env, config: PeerConfig):
        self.env = env
        self.config = config
        self.logger = logging.getLogger(repr(self))

        # Message queue for the received messages
        self.msg_queue = Store(env)
        # Network conenctions
        self.online = True
        self.connections = dict()

        # Known peers
        self.known_peers = set()
        self.disconnect_callbacks = []
        # Peer services
        self.services = {}  # Service.handle_message(self, msg) called on message

        # Start peer as it is created
        env.process(self.run())

    @property
    def name(self):
        return self.config.name

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.config.name)

    def __lt__(self, other):
        return self.name < other.name

    def is_connected(self, other):
        return other in self.connections

    def get_peer_sample(self):
        return random.sample(list(self.known_peers), min(len(self.known_peers), 5))

    def bootstrap_connect(self, other):
        # create ad-hoc connection and send Hello
        cnx = Connection(self, other)
        cnx.send(Hello(self), connect=True)

    def connect(self, other):
        if not self.is_connected(other):
            self.logger.info("Connecting to %s", repr(other))
            self.connections[other] = Connection(self, other)
            # We create bilateral connection
            if not other.is_connected(self):
                other.connect(self)

    def disconnect(self, other):
        if self.is_connected(other):
            self.logger.warning("%s: Breaking connection with %s", self.env.now, repr(other))
            del self.connections[other]
            if other.is_connected(self):
                other.disconnect(self)
            for cb in self.disconnect_callbacks:
                cb(self, other)

    def receive(self, msg):
        assert isinstance(msg, BaseMessage)
        self.logger.info("%s: Received message %s", self.env.now, type(msg))
        for s in self.services.values():
            assert isinstance(s, BaseService)
            s.handle_message(self, msg)

    def send(self, receiver, msg):
        # fire and forget
        assert msg.sender == self
        if receiver not in self.connections:
            self.logger.error("%s: Sending message to a not connected peer %s",
                              self.env.now, repr(receiver))
            raise Exception("Not connected")
        self.connections[receiver].send(msg)

    def gossip(self, msg, f):
        """
        Send to f neighbours selected randomly
        """
        for other in random.sample(self.connections, min(f, len(self.connections))):
            self.send(other, msg)

    def broadcast(self, msg):
        """Send to all """
        for other in self.connections:
            self.send(other, msg)

    def run(self):
        while True:
            # Peer is online and listens to the messages received
            msg = yield self.msg_queue.get()
            self.receive(msg)

