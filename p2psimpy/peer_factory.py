import logging



from p2psimpy.config import load_from_config, PeerNameGenerator, ConnectionConfig, \
    SlowdownConfig, DisruptionConfig


class PeerFactory:
    CLASS_MAP = {
        'ConnectionManager': BaseConnectionManager,
        'Downtime': Downtime,
        'Slowdown': Slowdown
    }

    CONFIG_CLASS_MAP = {
        'ConnectionManager': ConnectionConfig,
        'Downtime': DisruptionConfig,
        'Slowdown': SlowdownConfig
    }

    def __init__(self):
        # Services of a peer type
        self.services = {}
        # Configuration data classes for each service
        self.configs_classes = {}
        # Exact configurations
        self.raw_configs = {}
        self.full_configs = {}
        self.name_generator = PeerNameGenerator()
        self.logger = logging.getLogger(repr(self))

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

    def add_service_with_conf(self, peer_type, service_class, service_config_class, raw_config):
        """
        Add service for the peer type
        :param peer_type: type of the peer
        :param service_class: Class type of the service
        :param service_config_class:
        :param raw_config:
        :return:
        """
        if peer_type not in self.services:
            self.services[peer_type] = list()
            self.configs_classes[peer_type] = dict()
            self.raw_configs[peer_type] = dict()

        # Add new service for the peer type
        self.services[peer_type].append(service_class)
        self.configs_classes[peer_type][service_class.__name__] = service_config_class
        self.raw_configs[peer_type][service_class.__name__] = raw_config

    def add_service(self, peer_type, service_class, service_config):
        if peer_type not in self.services:
            self.services[peer_type] = list()
        if peer_type not in self.full_configs:
            self.full_configs[peer_type] = dict()

        # Add new service for the peer type
        self.services[peer_type].append(service_class)
        self.full_configs[peer_type][service_class.__name__] = service_config

    def update_peer_type(self, key: str, full_config: dict):
        self.raw_configs[key] = full_config

    def create_peer(self, env, peer_type: str):
        if peer_type not in self.raw_configs:
            self.logger.error("Cannot create peer. %s not known", peer_type)
            raise Exception("Peer type not known %s", peer_type)
        if 'Peer' not in self.raw_configs[peer_type]:
            self.logger.error("Cannot create peer. 'Peer' config for known for %s", peer_type)
            raise Exception("Peer config not found %s", peer_type)

        # Create a peer from PeerConfig
        p = Peer(env, PeerConfig.from_config(self.name_generator, peer_type,
                                             self.raw_configs[peer_type]["Peer"]))
        for service in self.services[peer_type]:
            if peer_type in self.full_configs and service.__name__ in self.full_configs[peer_type]:
                p.add_service(service(p, self.full_configs[peer_type][service.__name__]))
            else:
                config_class = load_from_config(self.configs_classes[peer_type][service.__name__],
                                                self.raw_configs[peer_type][service.__name__])
                # Initialise the service and add to the peer
                p.add_service(service(p, config_class))
        return p
