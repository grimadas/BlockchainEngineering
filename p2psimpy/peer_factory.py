from p2psimpy.peer import Peer
from p2psimpy.services.connection_manager import ConnectionManager
from p2psimpy.services.disruption import Downtime, Slowdown

from p2psimpy.config import load_from_config, PeerConfig, PeerNameGenerator, ConnectionConfig, \
    SlowdownConfig, DisruptionConfig

CONFIG_CLASS_MAP = {
    'ConnectionConfig': ConnectionConfig,
    'DowntimeConfig': DisruptionConfig,
    'SlowdownConfig': SlowdownConfig
}


class PeerFactory:

    def __init__(self, raw_peer_config_map: dict):
        self.raw_map = raw_peer_config_map
        self.name_generator = PeerNameGenerator()

    def _load_data_classes(self, p_type: str, raw_config: dict):
        data_map = dict()
        for service in raw_config[p_type]:
            if service == "PeerConfig":
                data_map[service] = PeerConfig.from_config(self.name_generator, p_type,
                                                           raw_config[p_type][service])
            else:
                data_map[service] = load_from_config(CONFIG_CLASS_MAP.get(service),
                                                     raw_config[p_type][service])
        return data_map

    def update_peer_type(self, key: str, full_config: dict):
        self.raw_map[key] = full_config

    def create_peer(self, env, peer_type: str, additional_services: dict = None):
        if peer_type not in self.raw_map:
            return None
        # Load peer config
        peer_config = self._load_data_classes(peer_type, self.raw_map)

        p = Peer(env, peer_config['PeerConfig'])
        p.services['connection_manager'] = ConnectionManager(p, peer_config["ConnectionConfig"])
        p.services['downtime'] = Downtime(p, peer_config["DowntimeConfig"])
        p.services['slowdown'] = Slowdown(p, peer_config["SlowdownConfig"])
        if additional_services:
            p.services.update(additional_services)
        return p
