import os
import random

from simpy import Store

from p2psimpy.logger import setup_logger
from p2psimpy.messages import BaseMessage, Hello
from p2psimpy.network import Connection
from p2psimpy.services.base import BaseHandler, BaseRunner


class Peer:

    def __init__(self, sim, peer_id: int, peer_type: str,
                 location: str, bandwidth_ul: float, bandwidth_dl: float, **kwargs):
        """
        Physical representation of a Peer
        :param sim: Simulation environment
        :param name:
        :param location:
        """
        self.sim = sim
        self.env = sim.env
        self.peer_type = peer_type
        self.peer_id = peer_id
        self.name = str(peer_id) + ":" + str(peer_type)
        self.location = location
        self.bandwidth_ul = bandwidth_ul
        self.bandwidth_dl = bandwidth_dl
        self.__dict__.update(kwargs)

        peer_repr = repr(self)
        if sim.sim_dir:
            self.log_name = os.path.join(sim.sim_dir, peer_repr + ".log")
            self.logger = setup_logger(peer_repr, self.log_name)
        else:
            self.log_name = None
            self.logger = None

        # Message queue for the received messages
        self.msg_queue = Store(self.env)

        # Network connections
        self.online = True
        self.connections = dict()

        # Known peers
        self.disconnect_callbacks = []

        # Peer services
        self.handlers = {}  # Service.handle_message(self, msg) called on message
        self.mh_map = {}  # Message -> Handler map
        self.runners = {}  # Peer service runners

        # Storage
        self.storage = {}

        # Start peer as it is created
        self.env.process(self.run())

    def __repr__(self):
        return '%s_%s' % (self.__class__.__name__, self.name)

    def __lt__(self, other):
        return self.name < other.name

    def run(self):
        while True:
            # Receive message and 
            msg = yield self.msg_queue.get()
            num_bytes = msg.size
            sender = msg.sender
            delay = num_bytes / self.bandwidth_dl
            yield self.env.timeout(delay)
            
            self.receive(msg)

    def is_connected(self, other):
        return other in self.connections

    def bootstrap_connect(self, other):
        """
        Create ad-hoc connection and send Hello
        :param other: peer object
        """
        #
        cnx = Connection(self, other)
        cnx.send(Hello(self), connect=True)

    def connect(self, other):
        """
        Add peer to the connections and repeat the same with other peer
        :param other: peer object
        """
        if not self.is_connected(other):
            if self.logger:
                self.logger.info("%s: Connecting to %s", self.env.now, repr(other))
            self.connections[other] = Connection(self, other)
            # We create bilateral connection
            if not other.is_connected(self):
                other.connect(self)

    def disconnect(self, other):
        """
        Disconnect with previously connected peer
        :param other: peer object
        """
        if self.is_connected(other):
            if self.logger:
                self.logger.warning("%s: Breaking connection with %s", self.env.now, repr(other))
            del self.connections[other]
            if other.is_connected(self):
                other.disconnect(self)
            for cb in self.disconnect_callbacks:
                cb(self, other)

    def receive(self, msg):
        """
        Receive message, will trigger handlers on the message
        :param msg:
        :return:
        """
        msg_type =  type(msg)
        msg_sender =  msg.sender
        if self.online:
            if self.logger:
                self.logger.info("%s: Received message <%s> from %s", self.env.now, repr(msg), msg_sender)

            if msg_type not in self.mh_map:
                if self.logger:
                    self.logger.error("No handler for the message %s", msg_type)
                raise Exception("No handler for the message %s at peer %s", msg_type, repr(self))
            for service_id in self.mh_map[msg_type]:
                self.handlers[service_id].handle_message(msg)

    def send(self, receiver, msg):
        """
        Send to a receiver peer in a fire-and-forget fashion.
        If receiver is not connected will raise and exception
        """
        # fire and forget
        if receiver not in self.connections:
            if self.logger:
                self.logger.error("%s: Sending message to a not connected peer %s",
                                  self.env.now, repr(receiver))
            raise Exception("Not connected")
        if self.logger:
            self.logger.info("%s: Sending message <%s> to %s", self.env.now, repr(msg), receiver)
        self.connections[receiver].send(msg)

    def _get_connections(self, exclude_bootstrap=True, except_set: set = None, except_type: set = None):
        if except_set is None:
            except_set = set()
        if except_type is None:
            except_type = set()
        if exclude_bootstrap:
            except_type.add('bootstrap')
        conn_set = set(self.connections.keys()) - except_set
        return (p for p in conn_set if p.peer_type not in except_type)

    def gossip(self, msg, f, exclude_bootstrap=True, except_peers: set = None, except_type: set = None):
        """
        Send to f neighbours selected randomly
        :param msg: Message
        :param f: the fanout parameter (number of peers to gossip to)
        :param exclude_bootstrap: Exclude bootstrap from gossip
        :param except_peers: connected peers to exclude from gossip
        :param except_type: exclude from gossip type of peers
        """
        gossip_set = list(self._get_connections(exclude_bootstrap, except_peers, except_type))

        for other in random.sample(gossip_set, min(f, len(gossip_set))):
            self.send(other, msg)

    def broadcast(self, msg, exclude_bootstrap=True, except_set: set = None, except_type: set = None):
        """Send to all connected peers except given """
        for other in self._get_connections(exclude_bootstrap, except_set, except_type):
            self.send(other, msg)

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

    def store(self, storage_name, msg_id, msg):
        if storage_name not in self.storage:
            if self.logger:
                self.logger.error("No storage %s found", storage_name)
            raise Exception("No storage %s found", storage_name)
        self.storage[storage_name].add(msg_id, msg)

    def add_storage(self, storage_name, storage):
        self.storage[storage_name] = storage
