import random

from p2psimpy.peer import Peer
from p2psimpy.services.base import BaseRunner


class BaseDisruption(BaseRunner):
    """
    Disruption in the network
    """
    is_disrupted = False

    def __init__(self, peer: Peer, **kwargs):
        """
        :param peer: Peer object
        :param interval: tick unit to probe disruption. Default: 10 ms
        :param mtbf: Mean time between failures. default: 10 seconds
        :param availability: peer availability [0-1] . default: 0.9
        """
        super().__init__(peer, **kwargs)

        self.interval = kwargs.pop('interval', 10)
        self.mtbf = kwargs.pop('mtbf', 10000)
        self.availability = kwargs.pop('availability', 0.9)

    def disruption_start(self):
        pass

    def disruption_end(self):
        pass

    def probe_status_change(self):
        if not self.is_disrupted:
            if random.random() <= self.interval / self.mtbf:
                self.is_disrupted = True
                self.disruption_start()
        else:
            avg_disruption_duration = self.mtbf * (1 - self.availability)
            if random.random() > self.interval / avg_disruption_duration:
                self.is_disrupted = False
                self.disruption_end()

    def run(self):
        while True:
            self.probe_status_change()
            yield self.env.timeout(self.interval)


class Downtime(BaseDisruption):
    """
    temporarily deactivates the peer
    """
    def __init__(self, peer, **kwargs):
        super(Downtime, self).__init__(peer, **kwargs)
        self.last_peers = set()

    def disruption_start(self):
        self.last_peers = self.peer.connections.keys()
        self.peer.active = False

    def disruption_end(self):
        self.peer.active = True
        for other in self.last_peers:
            self.peer.bootstrap_connect(other)


class Slowdown(BaseDisruption):
    """
    temporarily reduces bandwidth
    """

    def __init__(self, peer: Peer, **kwargs):
        super(Slowdown, self).__init__(peer, **kwargs)
        self.original_dl_bandwidth = peer.bandwidth_dl
        self.original_ul_bandwidth = peer.bandwidth_ul

        self.slowdown = kwargs.pop("slowdown", 0.2)

    def disruption_start(self):
        self.peer.bandwidth_ul *= self.slowdown
        self.peer.bandwidth_dl *= self.slowdown

    def disruption_end(self):
        self.peer.bandwidth_dl = self.original_dl_bandwidth
        self.peer.bandwidth_ul = self.original_ul_bandwidth
