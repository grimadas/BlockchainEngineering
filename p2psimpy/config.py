from attr import dataclass, fields

from p2psimpy.utils import PeerNameGenerator, get_random_values
import yaml


def load_config_parameter(config):
    if type(config) is dict and 'name' in config and 'parameters' in config:
        return get_random_values(config)[0]
    else:
        return config


def load_from_config(cls, config):
    return cls(*(load_config_parameter(config[field.name]) for field in fields(cls)))


class ConfigLoader:

    @staticmethod
    def load_services():
        with open('/Users/bulat/projects/tudelft/BlockchainEngineering/p2psimpy/input/config.yml') as s:
            return yaml.safe_load(s)

    @staticmethod
    def load_latencies():
        with open('/Users/bulat/projects/tudelft/BlockchainEngineering/p2psimpy/input/locations.yml') as s:
            return list(yaml.safe_load_all(s))[1]


@dataclass
class ConnectionConfig:
    ping_interval: int
    max_silence: int
    min_keep_time: int
    min_peers: int
    max_peers: int
    peer_list_number: int
    peer_batch_request_number: int


@dataclass
class DisruptionConfig:
    mtbf: int  # Mean time between failures = 24. * 60 * 60  # secs (mean time between failures)
    availability: float  # = 0.97  # Average availability of the service
    interval: int  # = 1.  # tick interval


@dataclass
class SlowdownConfig(DisruptionConfig):
    slowdown: float  # 0.2


@dataclass
class PeerConfig:
    name: str
    location: str
    bandwidth_ul: int
    bandwidth_dl: int

    @classmethod
    def from_config(cls, name_gen: PeerNameGenerator, peer_type: str, config: dict):
        params = [name_gen.generate_name(peer_type)]
        params.extend([load_config_parameter(config[field]) for field in ('location', 'bandwidth_ul', 'bandwidth_dl')])
        return cls(*params)
