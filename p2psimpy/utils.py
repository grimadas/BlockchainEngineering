from itertools import product
from copy import deepcopy


def make_symmetric(matrix):
    vals = matrix.keys()
    comb = product(vals, vals)

    for c in comb:
        if c[0] not in matrix or c[1] not in matrix[c[0]]:
            matrix[c[0]][c[1]] = matrix[c[1]][c[0]]


class Cache:

    def __init__(self, generator, cache_num=20, symmetric=True):
        self.gen = generator
        self.cache = deepcopy(generator)
        self.num = cache_num
        self.symmetric = symmetric

    def __call__(self, *args):
        return self.fetch(*args)

    def fetch(self, *args):
        try:
            val = self._pop(*args)
        except (IndexError, AttributeError, TypeError):
            generator = self._get(self.gen, *args)

            if hasattr(generator, "params"):
                self._set(generator.generate(self.num), *args)
            else:
                self._set( [generator] * self.num, *args)
            val = self._pop(*args)
        return val

    def _set(self, value, *args):
        if self.symmetric and len(args) == 2:
            if args[0] not in self.cache or args[1] not in self.cache.get(args[0]):
                self.cache[args[1]][args[0]] = value
            else:
                self.cache[args[0]][args[1]] = value
        elif len(args) == 0:
            self.cache = value
        else:
            self.cache[args[0]] = value

    def _get(self, val, *args):
        if self.symmetric and len(args) == 2:
            if args[0] not in val or args[1] not in val.get(args[0]):
                return val.get(args[1]).get(args[0])
            else:
                return val.get(args[0]).get(args[1])
        for attr in args:
            val = val.get(attr)
        return val

    def _pop(self, *args):
        last = None
        if len(args) == 0:
            last, self.cache = self.cache[-1], self.cache[:-1]
        elif len(args) == 1:
            last, self.cache[args[0]] = self.cache[args[0]][-1], self.cache[args[0]][:-1]
        elif self.symmetric and len(args) == 2:
            if args[0] not in self.cache or args[1] not in self.cache.get(args[0]):
                last, self.cache[args[1]][args[0]] = self.cache[args[1]][args[0]][-1], \
                                                     self.cache[args[1]][args[0]][:-1]
            else:
                last, self.cache[args[0]][args[1]] = self.cache[args[0]][args[1]][-1], \
                                                     self.cache[args[0]][args[1]][:-1]
        return last
