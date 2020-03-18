from p2psimpy.config import *
from p2psimpy.consts import MBit

from p2psimpy.services.connection_manager import P2PConnectionManager, BaseConnectionManager


class BootstrapPeerConfig(Config):
    bandwidth_ul = 100 * MBit
    bandwidth_dl = 100 * MBit


class ConnectionConfig(Config):
    max_peers = 100000


def get_default_bootstrap_type(locations, active_p2p=False):
    BootstrapPeerConfig.location = Dist('sample', locations)
    services = {P2PConnectionManager: ConnectionConfig} if active_p2p else (BaseConnectionManager,)
    return PeerType(BootstrapPeerConfig, services)
