import unittest

from p2psimpy.config import PeerConfig
from p2psimpy.network import Connection
from p2psimpy.peer import Peer
from simpy import Environment


def setup_latencies():
    return dict(LocA=dict(LocA={"name": "invgamma",
                                     "parameters": "(11.104508341331055, 0.3371934865734555, 2.0258998705983737)"},
                               LocB={"name": "norm",
                                     "parameters": "(131.0275, 0.25834811785650774)"}),
                     LocB=dict(LocA={"name": "norm",
                                     "parameters": "(105.4275, 0.25834811785650774)"},
                               LocB={"name": "invgamma",
                                     "parameters": "(6.4360455224301525, 0.8312748033308526, 1.086191852963273)"})
                     )



class ConnectionTests(unittest.TestCase):

    def setUp(self):
        # Create simulation environment
        self.env = Environment()
        # Put latencies between the locations
        self.env.locations = setup_latencies()

    def test_connection_latency(self):
        """
        Test constant latency connections.
        """
        a = PeerConfig('peer_a', 'LocA', 100, 100)
        b = PeerConfig('peer_b', 'LocB', 100, 100)
        peerA = Peer(self.env, a)
        peerB = Peer(self.env, b)
        conn = Connection(peerA, peerB)
        print(conn.latency)
        self.assertGreater(conn.latency, 0.1)
