import scipy.stats
from ast import literal_eval as make_tuple
from random import choices


class PeerNameGenerator:

    def __init__(self):
        self.peer_indexes = dict()  # type -> number map

    def generate_name(self, peer_type: str):
        if peer_type not in self.peer_indexes:
            # New peer type => Init
            self.peer_indexes[peer_type] = 0
        self.peer_indexes[peer_type] += 1
        return peer_type + "_" + str(self.peer_indexes[peer_type])


def get_random_values(distribution: dict, n=1):
    """Receives a `distribution` and outputs `n` random values
    Distribution format: { \'name\': str, \'parameters\': tuple }"""

    if distribution['name'] == 'sample':
        weights = distribution['parameters']['weights'] if 'weights' in distribution['parameters'] else None
        values = distribution['parameters']['values'] if 'values' in distribution['parameters'] \
            else distribution['parameters']
        return choices(values, weights=weights, k=n)

    dist = getattr(scipy.stats, distribution['name'])
    param = make_tuple(distribution['parameters'])
    return dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)


def get_latency_delay(locations: dict, origin: str, destination: str, n=1):
    """
    Get latency delay according to the latency distribution
    :param locations: map that contains distance between locations (in ms)
    :param origin: from location
    :param destination: to location
    :param n: the size of the latency vector
    :return: list of latencies
    """
    distribution = locations[origin][destination]
    # Convert latency in ms to seconds
    latencies = [
        latency for latency in get_random_values(distribution, n)]
    if len(latencies) == 1:
        return round(latencies[0], 2)
    else:
        return latencies
