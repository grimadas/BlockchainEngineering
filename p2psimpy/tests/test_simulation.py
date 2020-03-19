import unittest
from random import choice

from p2psimpy.config import Config, Dist, PeerType
from p2psimpy.consts import MBit
from p2psimpy.services.connection_manager import BaseConnectionManager

import networkx as nx

from p2psimpy.simulation import BaseSimulation


class Locations(Config):
    locations = ['Ohio', 'Ireland', 'Tokyo']
    latencies = {
        'Ohio': {'Ohio': Dist('invgamma', (5.54090, 0.333305, 0.987249)),
                 'Ireland': Dist('norm', (73.6995, 1.19583092197097127)),
                 'Tokyo': Dist('norm', (156.00904977375566, 0.09469886668079797))
                 },
        'Ireland': {'Ireland': Dist('invgamma', (6.4360455224301525, 0.8312748033308526, 1.086191852963273)),
                    'Tokyo': Dist('norm', (131.0275, 0.25834811785650774))
                    },
        'Tokyo': {'Tokyo': Dist('invgamma', (11.104508341331055, 0.3371934865734555, 2.0258998705983737))}
    }


# Define peer
class PeerConfig(Config):
    location = Dist('sample', Locations.locations)
    bandwidth_ul = Dist('norm', (50 * MBit, 10 * MBit))
    bandwidth_dl = Dist('norm', (50 * MBit, 10 * MBit))


def prepare_peer_types():
    return {'peer': PeerType(PeerConfig, {BaseConnectionManager: None})}


def prepare_topology(num_peers=25):
    # Create network topology
    G = nx.erdos_renyi_graph(num_peers, 0.3)
    nx.relabel_nodes(G, {k: k + 1 for k in G.nodes()}, copy=False)
    types_map = {k: 'peer' for k in G.nodes()}
    # Assign a peer type to the peers
    nx.set_node_attributes(G, types_map, 'type')
    return G


class ConnectionTests(unittest.TestCase):

    def test_run_simulation(self):
        net_sim = BaseSimulation(Locations, prepare_topology(25), prepare_peer_types(), logger_dir='test_logs')
        net_sim.run(5_000)
