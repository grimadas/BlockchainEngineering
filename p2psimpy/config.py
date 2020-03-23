import inspect
from ast import literal_eval as make_tuple
from collections import namedtuple
from random import choices

import scipy.stats
import yaml

PeerType = namedtuple('PeerType', ('config', 'service_map'), defaults=(None, {}))


class Dist:

    def __init__(self, name: str, params):
        self.name = name
        self.params = params

    def to_repr(self):
        return {self.__class__.__name__: {'name': self.name, 'params': str(self.params)}}

    @classmethod
    def from_repr(cls, yaml_dict):
        return cls(**yaml_dict)

    def generate(self, n=1):
        """
        Generate 'n' random values with given distribution
        """
        if self.name == 'sample':
            weights = self.params['weights'] if 'weights' in self.params else None
            values = self.params['values'] if 'values' in self.params \
                else self.params
            weights = make_tuple(weights) if type(weights) == str else weights
            values = make_tuple(values) if type(values) == str else values
            res = choices(values, weights=weights, k=n)
            return res if n != 1 else res[0]

        dist = getattr(scipy.stats, self.name)
        param = make_tuple(self.params) if type(self.params) == str else self.params
        res = dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)
        return res if n != 1 else res[0]

    def get(self):
        return self.generate(1)


class DistAttr(Dist):

    def __get__(self, inst, obj):
        return self.generate(1)


class Wrap:
    def __init__(self, cls):
        self._wrap = cls

    def to_repr(self):
        return {self._wrap.__class__.__name__: self._wrap.to_repr()}

    @classmethod
    def from_repr(cls, yaml_dict):
        return cls(**yaml_dict)

    def __str__(self):
        return str(self._wrap)

    def get(self):
        return self._wrap.__get__(None, None)

    def generate(self, n=1):
        return self._wrap.generate(n)


class ConfigAttr:
    def __init__(self, cls):
        self.cls = cls

    def to_repr(self):
        return self.cls.repr()

    def __str__(self):
        return str(self.cls.repr())

    def get(self):
        return self.cls.get()


class Config:
    @classmethod
    def save_to_yaml(cls, yaml_file):
        with open(yaml_file, 'w') as s:
            yaml.dump(cls.repr(), s)

    @classmethod
    def _serialize(cls, val):
        if isinstance(val, (tuple, list, dict)):
            if type(val) == dict:
                return {cls._serialize(k): cls._serialize(v) for k, v in val.items()}
            else:
                return list(cls._serialize(k) for k in val)
        else:
            if type(val) == Dist or type(val) == ConfigAttr:
                return val.to_repr()
            else:
                return val

    @classmethod
    def _deserialize(cls, val):
        if type(val) == dict:
            if 'Dist' in val:
                return Dist(**val['Dist'])
            else:
                return {k: cls._deserialize(v) for k, v in val.items()}
        else:
            return val

    @classmethod
    def get_attr_repr(cls):
        for i in inspect.getmembers(cls):
            if not i[0].startswith('_') and not callable(i[1]):
                yield cls._serialize(i)

    @classmethod
    def repr(cls):
        root = dict()
        root[str(cls.__name__)] = dict()
        main = root[cls.__name__]
        v = cls.get_attr_repr()
        main.update(cls.get_attr_repr())
        return root

    @classmethod
    def _get(cls, val):
        if type(val) == dict:
            return {k: cls._get(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [cls._get(v) for v in val]
        if type(val) == Dist or type(val) == ConfigAttr:
            return val.get()
        else:
            return val

    @classmethod
    def get(cls):
        full_dict = dict()
        for i in inspect.getmembers(cls):
            if not i[0].startswith('_') and not callable(i[1]):
                full_dict[i[0]] = cls._get(i[1])
        return full_dict

    @classmethod
    def from_repr(cls, cls_name, yaml_dict):
        cls.__name__ = cls_name
        cls.__qualname__ = cls_name
        for k, v in cls._deserialize(yaml_dict).items():
            setattr(cls, k, v)


def load_config_from_yaml(yaml_file):
    with open(yaml_file) as s:
        raw = yaml.safe_load(s)
    return load_config_from_repr(raw)

def load_config_from_repr(raw_repr):
    class NewConfig(Config): pass

    cls_name = list(raw_repr.keys())[0]
    NewConfig.from_repr(cls_name, raw_repr[cls_name])
    return NewConfig


