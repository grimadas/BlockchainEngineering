import random

from p2psimpy.config import DisruptionConfig, SlowdownConfig
from p2psimpy.peer import Peer
from p2psimpy.services.base import BaseService


class BaseDisruption(BaseService):
    """
    Disruption in the network
    """
    is_disrupted = False

    def __init__(self, peer: Peer, config: DisruptionConfig):
        self.peer = peer
        self.config = config
        self.env.process(self.run())

    @property
    def env(self):
        return self.peer.env

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.peer.config.name)

    def disruption_start(self):
        pass

    def disruption_end(self):
        pass

    def probe_status_change(self):
        if not self.is_disrupted:
            if random.random() <= self.config.interval / self.config.mtbf:
                self.is_disrupted = True
                self.disruption_start()
        else:
            avg_disruption_duration = self.config.mtbf * (1 - self.config.availability)
            if random.random() > self.config.interval / avg_disruption_duration:
                self.is_disrupted = False
                self.disruption_end()

    def run(self):
        while True:
            self.probe_status_change()
            yield self.env.timeout(self.config.interval)


class Downtime(BaseDisruption):
    """
    temporarily deactivates the peer
    """
    def __init__(self, peer, config):
        super(Downtime, self).__init__(peer, config)
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
    def __init__(self, peer, config: SlowdownConfig):
        self.config = config
        self.original_dl_bandwidth = peer.config.bandwidth_dl
        self.original_ul_bandwidth = peer.config.bandwidth_ul
        super(Slowdown, self).__init__(peer, config)

    def disruption_start(self):
        self.peer.config.bandwidth_ul *= self.config.slowdown
        self.peer.config.bandwidth_dl *= self.config.slowdown

    def disruption_end(self):
        self.peer.bandwidth_dl = self.original_dl_bandwidth
        self.peer.bandwidth_ul = self.original_ul_bandwidth
