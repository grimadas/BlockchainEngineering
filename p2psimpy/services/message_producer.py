from p2psimpy.services.base import BaseRunner
from p2psimpy.messages import GossipMessage
from p2psimpy.storage import Storage

import random
import string


class MessageProducer(BaseRunner):

    def __init__(self, peer, init_timeout=1000, msg_rate=5, 
                 init_fanout=5, init_ttl=4):
        super().__init__(peer)
        # calculate tx_interval
        self.init_timeout = init_timeout
        self.init_fanout = init_fanout
        self.init_ttl = init_ttl
        
        self.tx_interval = 1000 / msg_rate
        self.counter = 1 
        
        # Let's add a storage layer to store messages
        self.peer.add_storage('msg_time', Storage())
        self.peer.add_storage('msg_data', Storage())

    def produce_transaction(self):
        
        # generate new data 
        data = ''.join(random.choices(string.ascii_uppercase, k=20))
        msg_id = '_'.join((str(self.counter), str(self.peer.peer_id)))
        msg_ttl = self.init_ttl
        msg = GossipMessage(self.peer, msg_id, data, msg_ttl)
        self.peer.gossip(msg, 
                         self.init_fanout)
        self.peer.store('msg_time', str(self.counter), self.peer.env.now)
        self.peer.store('msg_data', str(self.counter), msg)
        self.counter+=1
        

    def run(self):
        yield self.env.timeout(self.init_timeout)
        while True:
            self.produce_transaction()
            yield self.env.timeout(self.tx_interval)