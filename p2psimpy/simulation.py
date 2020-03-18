import os
import random
from itertools import groupby

import networkx as nx
from simpy import Environment

from p2psimpy.config import load_config_from_yaml
from p2psimpy.defaults import get_default_bootstrap_type
from p2psimpy.logger import setup_logger
from p2psimpy.peer_factory import PeerFactory
from p2psimpy.services.connection_manager import BaseConnectionManager, P2PConnectionManager
from p2psimpy.services.disruption import Downtime, Slowdown
from p2psimpy.utils import Cache


class BaseSimulation(object):
    """
    Main class to run simulation.
    """
    known_services = [BaseConnectionManager, P2PConnectionManager, Downtime, Slowdown]
    cash_val = 50

    def __init__(self, locations, topology, peer_types_map, logger_dir='logs', **kwargs):
        """
            Initialize simulation with known locations, topology and services.
            :param locations: Known locations. Either a yaml file_name, or a Config class.
            :param topology: subscribable object map: peer_id -> type, optionally also connections to other peers
            :param peer_types_map: A map with 'type' -> PeerType objects
            :param logger_dir: directory to store peer logs. default: './logs/'
            :param random_seed: for reproducibility for your experiments.
        """

        if 'random_seed' in kwargs:
            self.random_seed = kwargs.get('random_seed', 42)
            random.seed(self.random_seed)
        self.sim_time = kwargs.get('sim_time', None)

        # Setup logging dir
        self.sim_dir = logger_dir
        if not os.path.exists(self.sim_dir):
            os.mkdir(self.sim_dir)
        self.sim_log_name = os.path.join(self.sim_dir, "sim.log")
        self.logger = setup_logger(__name__,  self.sim_log_name)

        # Init the environment
        self.env = Environment()

        # Init locations and latencies
        if type(locations) == str:
            # yaml file - try to load
            self._location_generator = load_config_from_yaml(locations).latencies
            self.all_locations = load_config_from_yaml(locations).locations
        else:
            # Load location generator
            self._location_generator = locations.latencies
            self.all_locations = locations.locations

        # Generate location to store in cache
        self.locations = Cache(self._location_generator, self.cash_val)

        # Parse topology
        self.peers_types = {}
        self.topology = {}
        self.types_peers = {}
        if type(topology) == dict:
            # The map with form peer_id -> {'type': ..., other_peer ids}
            self.peers = {p: None for p in topology.keys()}
            for k in topology.keys():
                self.peers_types[k] = topology.get(k).get('type')
                self.topology[k] = topology.get(k).get('neighbors')
        elif type(topology) == nx.Graph:
            # The graph with topology of peer_ids with peer attributes
            self.peers_types = nx.get_node_attributes(topology, 'type')
            self.topology = topology
            self.peers = {p: None for p in topology.nodes()}

        # map type -> set of peers
        self.types_peers = {k: {j for j, _ in list(v)}
                            for k, v in groupby(self.peers_types.items(), lambda x: x[1])}

        # Process given peer_types_map
        self.peer_types_configs = peer_types_map

        self.peer_factory = PeerFactory()
        # Create peers for this simulation
        for p in list(self.peers.keys()):
            peer_type_name = self.peers_types[p]
            peer_type = self.peer_types_configs[peer_type_name]
            self.peers[p] = self.peer_factory.create_peer(self, peer_type_name, peer_type, p)

        # Bootstrap connect peers
        # If there are connections =>
        for p in list(self.peers.keys()):
            if self.topology[p]:
                for c in self.topology[p]:
                    self.peers[p].bootstrap_connect(self.peers[c])
            else:
                # Connect to bootstrap server
                if 'bootstrap' not in self.types_peers:
                    # No bootstrap configuration is known - use default bootstrap
                    use_p2p = kwargs.get('bootstrap_p2p', True)
                    num_bootstrap = kwargs.get('num_bootstrap', 1)
                    self._init_default_bootstrap_servers(self.all_locations, num=num_bootstrap,
                                                         active_p2p=use_p2p)
                b_s = random.choice(list(self.types_peers['bootstrap']))
                boot_peer = self.peers[b_s]
                self.peers[p].bootstrap_connect(boot_peer)

    def get_latency_delay(self, origin: str, destination: str):
        """
        Get latency delay according to the latency distribution
        :param origin: from location
        :param destination: to location
        """
        return self.locations.fetch(origin, destination)

    def _add_peer(self, p):
        self.peers[p.peer_id] = p
        self.peers_types[p.peer_id] = p.peer_type
        if p.peer_type not in self.types_peers:
            self.types_peers[p.peer_type] = set()
        self.types_peers[p.peer_type].add(p.peer_id)

    def _init_default_bootstrap_servers(self, locations, num=1, active_p2p=False):
        """
        Initialize bootstrap servers: create bootstrap peers and start them immediately.
        :param num: number of servers
        """
        self.logger.warning("Init default bootstrap servers")
        bpt = get_default_bootstrap_type(locations, active_p2p=active_p2p)

        for i in range(num):
            p = self.peer_factory.create_peer(self, 'bootstrap', bpt)
            self._add_peer(p)

    def get_peers_names(self, peer_type):
        if peer_type not in self.peers:
            return None
        return (p.name for p in self.peers[peer_type])

    def start_all_peers(self):
        """
        Start all peers' runners.
        """
        for t in self.peers.keys():
            for p in self.peers[t]:
                p.start_all_runners()

    def get_graph(self, include_bootstrap_peers=False):
        G = nx.Graph()
        for p in self.peers_types.keys():
            if not include_bootstrap_peers and self.peers_types[p] == 'bootstrap':
                continue
            G.add_node(int(p))
            peer = self.peers[p]
            for other, cnx in peer.connections.items():
                if include_bootstrap_peers or other.peer_type != 'bootstrap':
                    G.add_edge(int(p), int(other.peer_id), weight=cnx.bandwidth)
        nx.set_node_attributes(G, self.peers_types, 'type')
        return G

    def avg_bandwidth(self):
        bws = []
        for peer in self.peers.items():
            for c in peer.connections.values():
                bws.append(c.bandwidth)
        return sum(bws) / len(bws)

    def median_bandwidth(self):
        bws = []
        for peer in self.peers.items():
            for c in peer.connections.values():
                bws.append(c.bandwidth)
        bws.sort()
        return bws[int(len(bws) / 2)]

    def run(self, until):
        self.env.run(until)

    def stop(self):
        self.env.exit(0)
