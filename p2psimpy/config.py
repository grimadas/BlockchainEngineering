import inspect
from dataclasses import dataclass, field
import yaml

import scipy.stats
from ast import literal_eval as make_tuple
from random import choices
from typing import Any

import attr


class Yamlable:

    @classmethod
    def load(cls, yaml_file):
        cls(*(load_config_parameter(config[field.name]) for field in fields(cls)))

    def save(self, yaml_file):
        pass


@dataclass
class Dist:
    name: str = 'sample'
    params: Any = ('Other', 'Ohio')

    def generate(self, n=1):
        """
        Generate 'n' random values with given distribution
        """
        if self.name == 'sample':
            weights = self.params['weights'] if 'weights' in self.params else None
            values = self.params['values'] if 'values' in self.params \
                else self.params
            res = choices(values, weights=weights, k=n)
            return res if n != 1 else res[0]

        dist = getattr(scipy.stats, self.name)
        param = make_tuple(self.params) if type(self.params) == str else self.params
        res = dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)
        return res if n != 1 else res[0]

    def __get__(self, inst, obj):
        return self.generate(1)


class Config:
    @classmethod
    def get_attr(cls):
        return {i[0]: i[1] for i in inspect.getmembers(cls) if not i[0].startswith('_')
                and not callable(i[1])}

    @classmethod
    def repr(cls):
        root = {cls.__name__: {}}
        main = root[cls.__name__]
        main.update(cls.get_attr())
        return root

    @classmethod
    def get(cls):
        for i in inspect.getmembers(cls):
            if not i[0].startswith('_') and not callable(i[1]):
                if type(i[1]) == Wrap or type(i[1]) == Config:
                    yield i[0], i[1].get()
                else:
                    yield i[0], i[1]


class PeerNameGenerator:

    def __init__(self):
        self.peer_indexes = dict()  # type -> number map

    def generate_name(self, peer_type: str):
        if peer_type not in self.peer_indexes:
            # New peer type => Init
            self.peer_indexes[peer_type] = 0
        self.peer_indexes[peer_type] += 1
        return peer_type + "_" + str(self.peer_indexes[peer_type])


@dataclass
class ConnectionConfig:
    ping_interval: int = 500
    max_silence: int = 20
    min_keep_time: int = 20
    min_peers: int = 5
    max_peers: int = 30
    peer_list_number: int = 1
    peer_batch_request_number: int = 3


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
        with open('p2psimpy/input/config.yml') as s:
            return yaml.safe_load(s)

    @staticmethod
    def load_latencies():
        with open('p2psimpy/input/locations.yml') as s:
            return list(yaml.safe_load_all(s))[1]


@dataclass
class DisruptionConfig:
    mtbf: int  # Mean time between failures = 24. * 60 * 60  # secs (mean time between failures)
    availability: float  # = 0.97  # Average availability of the service
    interval: int  # = 1.  # tick interval


@dataclass
class SlowdownConfig(DisruptionConfig):
    slowdown: float  # 0.2


def from_config(cls, name_gen: PeerNameGenerator, peer_type: str, config: dict):
    params = [name_gen.generate_name(peer_type)]
    params.extend([load_config_parameter(config[field]) for field in ('location', 'bandwidth_ul', 'bandwidth_dl')])
    return cls(*params)
