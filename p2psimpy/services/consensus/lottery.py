from p2psimpy.services import BaseRunner, BaseHandler
from p2psimpy import BaseMessage, GossipMessage, MsgResponse, Cache
from p2psimpy.storage import DagStorage, RangedStorage  
from itertools import islice
from p2psimpy.utils import to_hash

class Block(BaseMessage):
    
    base_size = 100 # 
    
    def __init__(self, sender, block_id, prev_id, txs):        
        super().__init__(sender, data=txs)
        self.id = block_id
        self.prev_id = prev_id

class Consensus(BaseRunner, BaseHandler):
    """
    Consensus based on blocks and longest-chain rule.
    Args:
        mining_time: DistAttr, Dist or value to indicate time for a mining process. 
        conf_num: number of confirmation when transaction is considered final.
        max_txs_per_block: maximum number of transaction per block.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.mining_time = Cache(kwargs.pop('mining_time', Dist('norm', (1500, 300))))
        self.conf_num = kwargs.pop('conf_num', 6)
        self.max_txs_per_block = kwargs.pop('max_txs_per_block', 100)
        
        self.init_ttl = kwargs.pop('init_ttl', 3)
        self.init_fanout = kwargs.pop('init_fanout', 6)
        self.pre_task = kwargs.pop('pre_task', None)
        self.post_task = kwargs.pop('post_task', None)
        self.exclude_types = kwargs.pop('exclude_types', {'bootstrap', 'client'})
        
        
        # Working transaction pool
        self.tx_pool = set()
        
        # initialize storage for the map: tx_id: number of confirmations 
        self.peer.add_storage('txs_conf', RangedStorage())
        self.main_strg = self.peer.storage.get('txs_conf')
        
        # Storage for blocks
        self.peer.add_storage('blocks', DagStorage())
        self.blocks = self.peer.storage.get('blocks')
        
        # Add genesis block
        self.blocks.add(0, 'Genesis', [])
        
    def _handle_gossip_msg(self, msg):
        if isinstance(msg.data, Transaction):
            tx_conf = self.main_strg.get(msg.data)
            if not tx_conf or tx_conf <= self.conf_num:
                # add to transaction pool as either new, or potentially unconfirmed
                self.tx_pool.add(msg.data)
        elif isinstance(msg.data, Block):
            block = msg.data
            # Add block to the block storage
            self.blocks.add(block.id, block.prev_id, block.data)
        
    
    def handle_message(self, msg):
        if isinstance(msg, MsgResponse):
            for msg_id, sub_msg in msg.data.items():
                self._handle_gossip_msg(sub_msg)
        else:
            self._handle_gossip_msg(msg)
            
    @property
    def messages(self):
        return GossipMessage, MsgResponse,
    
    def validate_chain(self, chain):
        """
        Validation rules for the chain:
         - Transaction in the chain are unique 
        Returns:
            None if chain is not valid, transactions set otherwise             
        """
        full_tx_set = {'0': 1}
        block_conf = 1
        for c,p in zip(*(islice(chain, i, None) for i in range(2))):
            for tx in self.blocks.get(c).get(p)['data']:
                # validate transaction: it must be unique 
                if tx in full_tx_set:
                    # Transaction was already seen in the chain! 
                    # Double transaction detected - Invalidate the chain
                    return None
                else:
                    full_tx_set[tx.data['hash']] = block_conf
            block_conf+=1
        return full_tx_set
    
    def choose_parent_block(self):
        """
        Returns:
            Block id of the last block in the longest valid chain.
        """
        for chain in self.blocks.get_longest_chains():
            tx_set = self.validate_chain(chain)           
            if tx_set:
                # add tx_set to the working db
                self.main_strg.clear_all()
                self.main_strg.batch_add(tx_set)
                return chain[0]

    def choose_transactions_from_pool(self):
        to_remove = set()
        new_txs = set()
        for tx in self.tx_pool:
            tx_conf = self.main_strg.get(tx.data['hash'])
            if not tx_conf:
                new_txs.add(tx)
            elif tx_conf > self.conf_num:
                to_remove.add(tx)
        self.tx_pool-=to_remove
        
        # From the new transaction choose transaction based on some criteria
        # Take transactions until you hit max_size
        
        # For now we will just limit by the number of transactions
        return list(new_txs)[:self.max_txs_per_block]
    
    def produce_block(self, block_id, prev_id, data):
        """
        Creates a block message and gossips to the neighbors 
        """
        # Create block message 
        block = Block(self.peer, block_id, prev_id, data)  
        # Wrap around GossipMessage 
        msg_id = 'b_'+str(block_id)
        msg = GossipMessage(self.peer, msg_id, block, self.init_ttl,
                            pre_task=self.pre_task, post_task=self.post_task)
        # Add block to the local chain storage
        self.blocks.add(block_id, prev_id, data)
        # Store msg for the further gossip
        self.peer.store('msg_time', msg_id, self.peer.env.now)
        self.peer.store('msg_data', msg_id, msg)
        # Gossip to the network
        self.peer.gossip(msg, 
                         self.init_fanout, except_type=self.exclude_types)
                
    def run(self):
        while True:
            # Choose last id of the block
            last_id = self.choose_parent_block()
            # Choose unproccessed transactions from the tx_pool 
            new_txs = self.choose_transactions_from_pool()
            # Calculate block id with these transactions (Mining Process)
            yield self.env.timeout( self.mining_time())        
            block_id =  to_hash(str(last_id) + str(new_txs))
            if new_txs:
                self.produce_block(block_id, last_id, new_txs)


