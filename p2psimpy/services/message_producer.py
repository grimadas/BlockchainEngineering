from p2psimpy.services.base import BaseRunner
from p2psimpy.messages import GossipMessage
from p2psimpy.storage import Storage

class MessageProducer(BaseRunner):

    def __init__(self, peer, init_timeout=1000, msg_rate=5, 
                 init_fanout=1, init_ttl=4, storage_name='msg_time',
                 message_type=GossipMessage, message_params=None):
        super().__init__(peer)
        # calculate tx_interval
        self.init_timeout = init_timeout
        self.init_fanout = init_fanout
        
        self.tx_interval = 1000 / msg_rate
        self.counter = 1 
        
        # Let's add a storage layer to store messages
        self.strg_name = storage_name
        self.peer.add_storage(self.strg_name, Storage())

        self.msg_cls = message_type
        self.msg_params = message_params if message_params else {'ttl': init_ttl}


    def produce_transaction(self):
        
        self.peer.gossip(self.msg_cls (self.peer,
                                       '_'.join((str(self.counter), str(self.peer.peer_id))), 
                                        **self.msg_params), 
                         self.init_fanout)
        self.peer.store(self.strg_name, str(self.counter), self.peer.env.now)
        self.counter+=1
        

    def run(self):
        yield self.env.timeout(self.init_timeout)
        while True:
            self.produce_transaction()
            yield self.env.timeout(self.tx_interval)