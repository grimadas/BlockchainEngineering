import os
import random

from copy import deepcopy

import networkx as nx
from simpy import Environment

from p2psimpy.config import load_config_from_yaml, load_config_from_repr, PeerType
from p2psimpy.defaults import get_default_bootstrap_type
from p2psimpy.logger import setup_logger
from p2psimpy.peer_factory import PeerFactory
from p2psimpy.utils import Cache


class BaseSimulation(object):
    """
    Main class to run simulation.
    """
    cash_val = 50

    def __init__(self, locations, topology, peer_types_map,
                 servs_impl=None, enable_logger=False, logger_dir='logs', **kwargs):
        """
            Initialize simulation with known locations, topology and services.
            locations: Known locations. Either a yaml file_name, or a Config class.
            topology: subscribable object map: peer_id -> type, optionally also connections to other peers
            peer_types_map: A map with 'type' -> PeerType objects
            logger_dir: directory to store peer logs. default: './logs/'
            random_seed: for reproducibility for your experiments.
        """

        if 'random_seed' in kwargs:
            self.random_seed = kwargs.get('random_seed', 42)
            random.seed(self.random_seed)
        self.sim_time = kwargs.get('sim_time', None)

        # Setup logging directory
        if enable_logger or logger_dir != 'logs':
            self.sim_dir = logger_dir
            if not os.path.exists(self.sim_dir):
                os.mkdir(self.sim_dir)
            self.sim_log_name = os.path.join(self.sim_dir, "sim.log")
            self.logger = setup_logger(__name__, self.sim_log_name, clean_up=True)
        else:
            self.sim_dir = None
            self.logger = None

        # Initialize the simulation environment
        self.env = Environment()

        self._locs = locations
        self._top = topology

        # Initialize locations and latencies
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
        self.types_peers = {}
        for k,v in self.peers_types.items():              
            self.types_peers.setdefault(v, set()).add(k)
        
        self._servs = dict()
        
        if servs_impl:
            # Load services 
            for type_name, peer_type in peer_types_map.items():
                s_map = peer_types_map[type_name].service_map
                smap_keys = s_map.keys() if type(s_map) == dict else s_map
                new_map = dict() 
                for k in smap_keys:
                    if type(k) == str:
                        new_map[servs_impl[k]] = s_map[k] if type(s_map) == dict else None
                    else:
                        new_map[k] = s_map[k] if type(s_map) == dict else None
                self._servs[type_name] = PeerType(peer_types_map[type_name].config, new_map)
        else:
            self._servs = deepcopy(peer_types_map)

        
        self.peer_types_configs = self._servs
        
        self.peer_factory = PeerFactory()
        # Create peers for this simulation
        for p in list(self.peers.keys()):
            peer_type_name = self.peers_types[p]
            peer_type = self.peer_types_configs[peer_type_name]
            self.peers[p] = self.peer_factory.create_peer(self, peer_type_name, peer_type, p)

        # Bootstrap connect to peers
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

    def save_experiment(self, expr_dir='expr', include_module_classes=False):
        '''Save your experiment configurations to yaml files'''
        import yaml
        # Save locations 
        if not os.path.exists(expr_dir):
            os.mkdir(expr_dir)
        loc_file = os.path.join(expr_dir, "locations.yaml")
        top_file = os.path.join(expr_dir, 'topology.yaml')
        serv_file = os.path.join(expr_dir, 'services.yaml')

        self._locs.save_to_yaml(loc_file)
        if type(self._top) == dict:
            # Save dict
            with open(top_file, 'w') as s:
                yaml.dump(self._top, s)
        else:
            # This is networkx file
            nx.write_yaml(self._top, top_file)

        dump_serv = {}
        services = dict()
        for k, pt in self._servs.items():
            new_pt = pt.config.repr()
            if type(pt.service_map) == dict:
                serv = dict()
                for sk, sc in pt.service_map.items():
                    if not sc:
                        serv[sk.__name__] = sc
                    else:
                        serv[sk.__name__] = sc.repr()
                        
                    services[sk.__name__] = sk if include_module_classes else None
            else:
                serv = tuple(k.__name__ for k in pt.service_map)
                if include_module_classes:
                    services.update({k.__name__: k for k in pt.service_map})
                else:
                    services.update({k.__name__: None for k in pt.service_map})

            dump_serv[k] = PeerType(new_pt, serv)

        with open(serv_file, 'w') as s:
            yaml.dump([dump_serv, services], s)

    @staticmethod
    # Load the experiment - obtain peer locations and services from the saved yaml files
    def load_experiment(expr_dir='expr', load_modules=False):
        import yaml
        loc_file = os.path.join(expr_dir, "locations.yaml")
        top_file = os.path.join(expr_dir, 'topology.yaml')
        serv_file = os.path.join(expr_dir, 'services.yaml')

        locs = load_config_from_yaml(loc_file)
        with open(top_file) as s:
            top = yaml.load(s)

        with open(serv_file) as s:
            servs, services = yaml.load(s)
        for sk, pt in list(servs.items()):

            peer_config = load_config_from_repr(pt.config)
            if type(pt.service_map) == dict:
                new_services = dict()
                for k, v in pt.service_map.items():
                    k = services[k] if load_modules else k
                    new_services[k] = load_config_from_repr(v) if v else v
            else:
                new_services = [services[k] for k in pt.service_map] if load_modules else pt.service_map
            servs[sk] = PeerType(peer_config, new_services)
        return locs, top, servs, services

    # Add peer p
    def _add_peer(self, p):
        self.peers[p.peer_id] = p
        self.peers_types[p.peer_id] = p.peer_type
        if p.peer_type not in self.types_peers:
            self.types_peers[p.peer_type] = set()
        self.types_peers[p.peer_type].add(p.peer_id)

    def _init_default_bootstrap_servers(self, locations, num=1, active_p2p=False):
        """
        Initialize bootstrap servers: create bootstrap peers and start them immediately.
        num: number of servers
        """
        if self.logger:
            self.logger.warning("Init default bootstrap servers")
        bpt = get_default_bootstrap_type(locations, active_p2p=active_p2p)

        for i in range(num):
            p = self.peer_factory.create_peer(self, 'bootstrap', bpt)
            self._add_peer(p)

    # Get names of all peers connected
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
        '''Get current topology of the simulation'''
        G = nx.Graph()
        online_map = dict()
        for p in self.peers_types.keys():
            if not include_bootstrap_peers and self.peers_types[p] == 'bootstrap':
                continue
            G.add_node(int(p))
            peer = self.peers[p]
            if peer.online:
                for other, cnx in peer.connections.items():
                    if other.online and (include_bootstrap_peers or other.peer_type != 'bootstrap'):
                        G.add_edge(int(p), int(other.peer_id), weight=cnx.bandwidth)
            online_map[int(p)] = peer.online

        nx.set_node_attributes(G, self.peers_types, 'type')
        nx.set_node_attributes(G, online_map, 'is_online')
        return G

    # Get average bandwidh of all the peer connections
    def avg_bandwidth(self):
        bws = []
        for peer in self.peers.items():
            for c in peer.connections.values():
                bws.append(c.bandwidth)
        return sum(bws) / len(bws)

    # Get median bandwidh of all the peer connections
    def median_bandwidth(self):
        bws = []
        for peer in self.peers.items():
            for c in peer.connections.values():
                bws.append(c.bandwidth)
        bws.sort()
        return bws[int(len(bws) / 2)]

    # Run the peer with a time limit of until
    def run(self, until):
        self.env.run(until)

    # Stop the peer simulation
    def stop(self):
        self.env.exit(0)
