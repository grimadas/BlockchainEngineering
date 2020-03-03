import logging
import random

import networkx as nx
from simpy import Environment

from p2psimpy.config import ConfigLoader
from p2psimpy.logger import init_log
from p2psimpy.peer_factory import PeerFactory


class BaseSimulation(object):
    """ Class to represent different topologies and p2p network simulation
    """

    def __init__(self, num_bootstrap_servers=1):
        self.current_graph = nx.Graph()
        init_log()
        self.logger = logging.getLogger(__name__)
        # Starting simulation
        self.env = Environment()
        # other peers
        self.bootstrap_peers = list()
        self.peers = list()
        self.peer_factory = PeerFactory(ConfigLoader.load_services())
        self.locations = ConfigLoader.load_latencies()
        self.env.locations = self.locations
        self.logger.info("Start simulation")
        self.init_bootstrap_servers(num_bootstrap_servers)

    def init_bootstrap_servers(self, num=1, additional_services: dict = None):
        # bootstrapping peer
        self.logger.info("Init bootstrap servers")
        for i in range(num):
            self.bootstrap_peers.append(self.peer_factory.create_peer(self.env, 'bootstrap', additional_services))

    def add_peers(self, peer_num, peer_type: str = 'basic', additional_services: dict = None):
        self.logger.info("Adding peers %s", peer_num)
        for i in range(peer_num):
            p = self.peer_factory.create_peer(self.env, peer_type, additional_services)
            # Select random bootstrap server
            bootstrap_server = random.choice(self.bootstrap_peers)
            p.bootstrap_connect(bootstrap_server)
            self.peers.append(p)

    def get_graph(self, include_bootstrap_peers=False):
        G = nx.Graph()
        current_peers = self.peers
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

