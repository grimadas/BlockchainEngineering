from itertools import product


def make_symmetric(matrix):
    vals = matrix.keys()
    comb = product(vals, vals)

    for c in comb:
        if c[0] not in matrix or c[1] not in matrix[c[0]]:
            matrix[c[0]][c[1]] = matrix[c[1]][c[0]]

class Cached:

    def __init__(self, generator):
        self._gen = generator
        self._cache = {}

    def get(self, *args):
        for k in args:


        if len(args) > 0:
            # there is more arguments
            if key not in self._cache or :
                # Trigger create
