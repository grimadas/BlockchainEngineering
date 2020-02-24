import random
import simpy

from .consts import MBit, NUM_PEERS, VISUALIZATION, SIM_DURATION
from .peer import Peer
from .peermanager import ConnectionManager
from .peermanager import PingHandler
from .peermanager import PeerRequestHandler
from .disruptions import Downtime
from .disruptions import Slowdown



def managed_peer(name, env):
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


def create_peers(bootstrap_peer, num):
    """
    Create a network with peers
    :param bootstrap_peer: entry peer
    :param num: number of peers in the simulation
    :return: list of peers
    """
    peers = []
    for i in range(num):
        p = managed_peer('P%d' % i, env)
        # initial connect to peerserver
        connection_manager = p.services[0]
        connection_manager.connect_peer(bootstrap_peer)
        peers.append(p)

    # set peers bandwidth
    for p in peers:
        p.bandwidth_dl = p.bandwidth_ul = max(10, random.gauss(100, 50)) * MBit

    return peers


# create env
env = simpy.Environment()

# bootstrapping peer
pserver = managed_peer('PeerServer', env)
pserver.bandwidth_ul = pserver.bandwidth_dl = 100 * MBit

# other peers
peers = create_peers(pserver, NUM_PEERS)
print("Starting simulation")

if VISUALIZATION:
    from animate import Visualizer
    Visualizer(env, peers)
else:
    env.run(until=SIM_DURATION)
