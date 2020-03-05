import logging
import random

from simpy import Store

from p2psimpy.config import PeerConfig
from p2psimpy.messages import BaseMessage, Hello
from p2psimpy.network import Connection
from p2psimpy.services.base import BaseHandler, BaseRunner


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
        self.handlers = {}  # Service.handle_message(self, msg) called on message
        self.mh_map = {}  # Message -> Handler map
        self.runners = {}  # Peer service runners

        # Storage
        self.storage = {}

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

    def store(self, storage_name, msg_id, msg):
        if storage_name not in self.storage:
            self.logger.error("No storage %s found", storage_name)
            raise Exception("No storage %s found", storage_name)
        self.storage[storage_name].add(msg_id, msg)

    def add_storage(self, storage_name, storage):
        self.storage[storage_name] = storage

    def add_service(self, service):
        """
        Add service to the peer
        """
        serv_name = type(service).__name__
        if isinstance(service, BaseHandler):
            self.handlers[serv_name] = service
            for m in service.messages:
                if m not in self.mh_map:
                    self.mh_map[m] = set()
                self.mh_map[m].add(serv_name)
        if isinstance(service, BaseRunner):
            self.runners[serv_name] = service

    def start_all_runners(self):
        for runner in self.runners.values():
            runner.start()

    def disconnect(self, other):
        if self.is_connected(other):
            self.logger.warning("%s: Breaking connection with %s", self.env.now, repr(other))
            del self.connections[other]
            if other.is_connected(self):
                other.disconnect(self)
            for cb in self.disconnect_callbacks:
                cb(self, other)

    def receive(self, msg):
        assert isinstance(msg, BaseMessage)  # Make sure the message is known
        self.logger.info("%s: Received message %s", self.env.now, type(msg))
        if type(msg) not in self.mh_map:
            self.logger.error("No handler for the message %s", type(msg))
            raise Exception("No handler for the message %s", type(msg))
        for service_id in self.mh_map[type(msg)]:
            self.handlers[service_id].handle_message(msg)

    def send(self, receiver, msg):
        """
        Send to a receiver peer in a fire-and-forget fashion.
        If receiver is not connected will raise and exception
        """
        # fire and forget
        assert msg.sender == self, "Sending peer should be same %s %s" % (msg.sender, self)
        if receiver not in self.connections:
            self.logger.error("%s: Sending message to a not connected peer %s",
                              self.env.now, repr(receiver))
            raise Exception("Not connected")
        self.connections[receiver].send(msg)

    def gossip(self, msg, f, except_set: set = None):
        """
        Send to f neighbours selected randomly
        :param msg: Message
        :param f: the fanout parameter (number of peers to gossip to)
        :type except_set: connected peers to exclude from gossip
        """
        if except_set is None:
            except_set = set()
        gossip_set = set(self.connections.keys()) - except_set
        for other in random.sample(list(gossip_set), min(f, len(gossip_set))):
            self.send(other, msg)

    def broadcast(self, msg):
        """Send to all connected peers """
        for other in self.connections:
            self.send(other, msg)

    def run(self):
        while True:
            # Peer is online and listens to the messages received
            msg = yield self.msg_queue.get()
            self.receive(msg)
