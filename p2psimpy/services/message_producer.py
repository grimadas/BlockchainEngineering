from p2psimpy.services.base import BaseRunner
from p2psimpy.messages import GossipMessage
from p2psimpy.storage.simple import RangedStorage

import random
import string


# Class that handles producing and gossip. 
# msg_rate: Number of messages per second
# init_timeout: Initial timeout before first message
# init_fanout: Factor to determine how many peer connections to gossip  
class MessageProducer(BaseRunner):

    def __init__(self, peer, init_timeout=1000, msg_rate=5,
                 init_fanout=5, init_ttl=4, pre_task=None, post_task=None):
        super().__init__(peer)
        # calculate tx_interval
        self.init_timeout = init_timeout
        self.init_fanout = init_fanout
        self.init_ttl = init_ttl

        self.pre_task = pre_task
        self.post_task = post_task

        self.tx_interval = 1000 / msg_rate
        self.counter = 1

        # Let's add a storage layer to store messages
        self.peer.add_storage('msg_time', RangedStorage())
        self.peer.add_storage('msg_data', RangedStorage())

    def produce_transaction(self):
        # generate new data
        data = ''.join(random.choices(string.ascii_uppercase, k=20))
        msg_id = '_'.join((str(self.peer.peer_id), str(self.counter)))
        msg_ttl = self.init_ttl
        msg = GossipMessage(self.peer, msg_id, data, msg_ttl,
                            pre_task=self.pre_task, post_task=self.post_task)

        self.peer.gossip(msg,
                         self.init_fanout)
        self.peer.store('msg_time', msg_id, self.peer.env.now)
        self.peer.store('msg_data', msg_id, msg)
        self.counter += 1

    def run(self):
        yield self.env.timeout(self.init_timeout)
        while True:
            self.produce_transaction()
            yield self.env.timeout(self.tx_interval)


class LimitedMessageProducer(MessageProducer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.times = kwargs.pop('times', 1)

    def run(self):
        yield self.env.timeout(self.init_timeout)
        for _ in range(self.times):
            self.produce_transaction()
            yield self.env.timeout(self.tx_interval)
