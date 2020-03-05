import logging
import random

import networkx as nx
from simpy import Environment

from p2psimpy.config import ConfigLoader
from p2psimpy.logger import reset_log
from p2psimpy.peer_factory import PeerFactory


class BaseSimulation(object):
    """ Class to represent different topologies and p2p network simulation
    """

    def __init__(self, num_bootstrap_servers=1):
        self.current_graph = nx.Graph()
        # reset_log()
        self.logger = logging.getLogger(__name__)
        # Starting simulation
        self.env = Environment()
        # other peers
        self.bootstrap_peers = list()
        self.peers = dict()
        # Create peer factory from config file
        self.peer_factory = PeerFactory(ConfigLoader.load_services())
        self.locations = ConfigLoader.load_latencies()
        self.env.locations = self.locations
        self.logger.info("Start simulation")

    def init_bootstrap_servers(self, num=1):
        """
        Initialize bootstrap servers: create bootstrap peers and start them immediately.
        :param num: number of servers
        """
        self.logger.info("Init bootstrap servers")
        for i in range(num):
            p = self.peer_factory.create_peer(self.env, 'bootstrap')
            self.bootstrap_peers.append(p)
            # Bootstrap servers start immediately
            p.start_all_runners()

    def get_peers_names(self, peer_type):
        if peer_type not in self.peers:
            return None
        return (p.name for p in self.peers[peer_type])

    def add_peer_service_with_conf(self, peer_type: str, service_class, service_config_class, config):
        """
        Add peer service for the type of peer. Load configuration that might contain distribution samples.
        :param peer_type: type of the peer
        :param service_class: Class with a service implementation
        :param service_config_class: configuration dataclass for the service class
        :param config: the actual configuration for peer as a dictionary
        """
        self.peer_factory.add_service_with_conf(peer_type, service_class, service_config_class, config)

    def add_peer_service(self, peer_type, service_class, service_config):
        """
        Add peer service for the type of peer
        :param peer_type: type of the peer
        :param service_class: Class with a service implementation
        :param service_config: configuration object for this service
        """
        self.peer_factory.add_service(peer_type, service_class, service_config)

    def start_all_peers(self):
        """
        Start all peers' runners.
        """
        for t in self.peers.keys():
            for p in self.peers[t]:
                p.start_all_runners()

    def add_peers(self, peer_num: int, peer_type: str = 'basic'):
        """
        Create and add peers to the simulation environment.
        Peers will connect to a random bootstrap server and start all services.
        :param peer_num: number of peers to create
        :param peer_type: Type of peers to create
        """
        self.logger.info("Creating %s peers of type %s", peer_num, peer_type)
        for i in range(peer_num):
            p = self.peer_factory.create_peer(self.env, peer_type)
            # Select random bootstrap server
            bootstrap_server = random.choice(self.bootstrap_peers)
            p.bootstrap_connect(bootstrap_server)
            if peer_type not in self.peers:
                self.peers[peer_type] = list()
            self.peers[peer_type].append(p)

    def get_graph(self, include_bootstrap_peers=False):
        G = nx.Graph()
        current_peers = [p for peer_type in self.peers.values() for p in peer_type]
        if include_bootstrap_peers:
            current_peers.extend(self.bootstrap_peers)
        for peer in current_peers:
            G.add_node(peer.name)
            for other, cnx in peer.connections.items():
                if include_bootstrap_peers or not str.startswith(other.name, 'bootstrap'):
                    G.add_edge(peer.name, other.name, weight=cnx.bandwidth)
        return G

    def avg_bandwidth(self):
        bws = []
        for peer in self.peers:
            for c in peer.connections.values():
                bws.append(c.bandwidth)
        return sum(bws) / len(bws)

    def median_bandwidth(self):
        bws = []
        for peer in self.peers:
            for c in peer.connections.values():
                bws.append(c.bandwidth)
        bws.sort()
        return bws[int(len(bws) / 2)]

    def run(self, until=None):
        self.env.run(until)

    def stop(self):
        self.env.exit(0)

