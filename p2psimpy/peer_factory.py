from p2psimpy.config import PeerType
from p2psimpy.peer import Peer


class PeerFactory:

    def __init__(self):
        self._last = 1

    def create_peer(self, sim, type_name: str, peer_type: PeerType, peer_id: int = None):
        # Create a peer from PeerConfig
        if not peer_id:
            peer_id = self._last + 1
            self._last = peer_id
        else:
            if int(peer_id) > self._last:
                self._last = int(peer_id)

        peer_config_gen = peer_type.config
        services = peer_type.service_map.keys() if type(peer_type.service_map) == dict else peer_type.service_map
        service_configs = peer_type.service_map if type(peer_type.service_map) == dict else None

        p = Peer(sim, peer_id, type_name, **peer_config_gen.get())

        for service in services:
            if service_configs and service_configs[service]:
                args = service_configs[service].get()
                serv = service(p, **args)
            else:
                serv = service(p)
            p.add_service(serv)
        p.start_all_runners()
        return p

    def load_from_conf(self, config):
        # Parse the full configuration and add services
        for p_type in config:
            for service_name in config[p_type]:
                if service_name != 'Peer':
                    self.add_service_with_conf(p_type, self.CLASS_MAP[service_name],
                                               self.CONFIG_CLASS_MAP[service_name],
                                               config[p_type][service_name])
            # Add peer configuration
            # Exception not known service
            self.raw_configs[p_type]['Peer'] = config[p_type]['Peer']
