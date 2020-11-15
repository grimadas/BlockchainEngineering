import random

from p2psimpy.peer import Peer
from p2psimpy.services.base import BaseRunner

from p2psimpy.config import Dist
from p2psimpy.utils import Cache


class BaseDisruption(BaseRunner):
    """
    Disruption in the network
    """

    def __init__(self, peer: Peer):
        """
        peer: Peer object
        interval: tick unit to probe disruption. Default: 10 ms
        mtbf: Mean time between failures. default: 10 seconds
        availability: peer availability [0-1] . default: 0.9
        """
        super().__init__(peer)

        self.is_disrupted = False

    def status_change(self):
        if not self.is_disrupted:
            self.is_disrupted = True
            self.disruption_start()
        else:
            self.is_disrupted = False
            self.disruption_end()

    def disruption_start(self):
        raise NotImplemented

    def disruption_end(self):
        raise NotImplemented

# Define intervals for scheduled disruptions
class ScheduledDisruption(BaseDisruption):

    def __init__(self, peer: Peer, schedule):
        super().__init__(peer)

        self.schedule = schedule

    def run(self):
        for event in self.schedule:
            yield self.env.timeout(event)
            self.status_change()

# Define intervals for random disruptions
class RandomDisruption(BaseDisruption):

    def __init__(self, peer,
                 start_time=Dist('norm', (1000, 70)),
                 disruption_time=Dist('norm', (400, 150)),
                 disruption_intervals=Dist('norm', (600, 200))):

        super().__init__(peer)
        self.start_time = Cache(start_time)
        self.disruption_time = Cache(disruption_time)
        self.disruption_intervals = Cache(disruption_intervals)

    def next(self):
        if self.is_disrupted:
            return abs(self.disruption_intervals())
        else:
            return abs(self.disruption_time())

    def run(self):
        yield self.env.timeout(abs(self.start_time()))
        while True:
            yield self.env.timeout(self.next())
            self.status_change()

# Define intervals for scheduled downtime
class ScheduledDowntime(ScheduledDisruption):

    def __init__(self, peer, schedule):
        super().__init__(peer, schedule)
        self.last_peers = set()

    def disruption_start(self):
        self.last_peers = self.peer.connections.keys()
        self.peer.online = False

    def disruption_end(self):
        self.peer.online = True
        for other in self.last_peers:
            self.peer.bootstrap_connect(other)

# Define intervals for random downtime
class RandomDowntime(RandomDisruption):

    def __init__(self, peer,
                 start_time=Dist('norm', (1000, 70)),
                 disruption_time=Dist('norm', (400, 150)),
                 disruption_intervals=Dist('norm', (600, 200))):
        super().__init__(peer, start_time, disruption_time, disruption_intervals)
        self.last_peers = set()

    def disruption_start(self):
        self.last_peers = self.peer.connections.keys()
        self.peer.online = False

    def disruption_end(self):
        self.peer.online = True
        for other in self.last_peers:
            self.peer.bootstrap_connect(other)
