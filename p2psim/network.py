import random

import networkx as nx
import simpy

from .consts import MBit, NUM_PEERS, VISUALIZATION, SIM_DURATION, PEER_BANDWIDTH_MAX, PEER_LATENCY_MIN, PEER_BANDWIDTH_MODEL
from .peer import Peer
from .peermanager import ConnectionManager
from .peermanager import PingHandler
from .peermanager import PeerRequestHandler
from .disruptions import Downtime
from .disruptions import Slowdown


class SimNetwork(object):

    def __init__(self):
        self.graph = nx.Graph()
        # Simulator environment
        # create env
        env = simpy.Environment()

        # bootstrapping peer
        pserver = self.managed_peer('PeerServer')
        pserver.bandwidth_ul = pserver.bandwidth_dl = 100 * MBit

        # other peers
        self.create_peers(pserver, NUM_PEERS)
        print("Starting simulation")

        self.env = simpy.Environment()

    def managed_peer(self, name):
        """
        Create a peer with services
        :param name: peer name
        :param env: Simulator environment
        :return:
        """
        p = Peer(name, env)
        p.services.append(ConnectionManager(p))
        p.services.append(PeerRequestHandler())
        p.services.append(PingHandler())
        p.services.append(Downtime(env, p))
        p.services.append(Slowdown(env, p))
        return p

    def create_peers(self, bootstrap_peer, num):
        """
        Create a network with peers
        :param bootstrap_peer: entry peer
        :param num: number of peers in the simulation
        :param env: environment of the simulation
        :return: list of peers
        """
        for i in range(num):
            p = self.managed_peer('P%d' % i, env)
            # initial connect to peerserver
            connection_manager = p.services[0]
            connection_manager.connect_peer(bootstrap_peer)
            self.graph.add_node(p, label=p.name)

        # set peers bandwidth
        #for p in peers:
        #    p.bandwidth_dl = p.bandwidth_ul = max(10, random.gauss(100, 50)) * MBit

        #return peers

    def _update_graph(self):
        G = nx.Graph()
        for peer in self.graph.nodes():
            for other, cnx in peer.connections.items():
                G.add_edge(peer, other, weight=cnx.bandwidth)
