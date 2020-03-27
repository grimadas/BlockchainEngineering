from p2psimpy.services.base import BaseHandler, BaseRunner
from p2psimpy.messages import GossipMessage, SyncPing, SyncPong, MsgRequest, MsgResponse
from p2psimpy.storage import Storage, RangedStorage

from p2psimpy.utils import Cache
from p2psimpy.config import Dist

from re import split 
from copy import copy

# Define a special message GossipMessage: Message with ttl
        
class GossipService(BaseHandler):
    """
    Simple gossip service to handle gossip messages and rely them to neighbors. 
    """

    def _store_message(self, msg, msg_id=None):
        if not msg_id:
            msg_id = msg.id

        self.peer.store('msg_time', msg_id, self.peer.env.now)
        self.peer.store('msg_data', msg_id, msg)

    def __init__(self, peer, fanout=3, exclude_peers: set=None, 
                 exclude_types: set=None):
        super().__init__(peer)
        
        self.fanout = fanout
        if exclude_peers is None:
            self.exclude_peers = set() 
        else:
            self.exclude_peers = exclude_peers
        self.exclude_types = exclude_types
            
        self.peer.add_storage('msg_time', Storage())
        self.peer.add_storage('msg_data', Storage())

    def handle_message(self, msg):
        # Store message localy 
        self._store_message(msg)
        if msg.ttl > 0:
            # Rely message further, modify the message
            exclude_peers = {msg.sender} | self.exclude_peers
            # Use peer gossip - it will sample self.config.fanout and exclude sender
            # If you need to exclude some peers: add it to the set
            self.peer.gossip( GossipMessage(self.peer, msg.id, msg.data, msg.ttl-1), 
                             self.fanout, except_peers=exclude_peers, except_type=self.exclude_types)

    @property
    def messages(self):
        return GossipMessage,

class MessageResponder(BaseHandler):

    def _form_message_response(self, msg):
        response = {}
        for k in msg.data:
            response[k] = self.peer.get_storage('msg_data').get(k)
        return response


    def handle_message(self, msg):
        self.peer.send(msg.sender, MsgResponse(self.peer, self._form_message_response(msg)))


    @property
    def messages(self):
        return MsgRequest, 


class PullGossipService(MessageResponder, BaseRunner):

    def __init__(self, peer, 
             exclude_types: set=None, exclude_peers: set=None, 
             fanout=3, round_time=500, 
             init_timeout=Dist('norm', (200, 100))):
        super().__init__(peer)
        
        self.fanout = fanout
        if exclude_peers is None:
            self.exclude_peers = set() 
        else:
            self.exclude_peers = exclude_peers
        self.exclude_types = exclude_types

        self.sync_time = round_time
        self._init_stores()
        self.strg = self.peer.get_storage('msg_data')

        self.ini_time = abs(Cache(init_timeout).fetch())

    def _init_stores(self):
        self.peer.add_storage('msg_time', Storage())
        self.peer.add_storage('msg_data', Storage())


    def _get_sync_indexes(self):
        """ Will return all known indexes 
        """
        return self.strg.get_known_tx_ids()


    def run(self):
        yield self.env.timeout(self.ini_time)
        while True:
            # choose random peers and perioducally synchronize the data - by filling out the missing links
            yield self.env.timeout(self.sync_time)

            
            self.peer.gossip( SyncPing(self.peer, self._get_sync_indexes()), self.fanout, 
                except_peers=self.exclude_peers, except_type=self.exclude_types)

    def _self_missing(self, msg):
        known = self.strg.get_known_tx_ids()

        me_missing = set(msg.data) - set(known)
        if len(me_missing) > 0:
            # Request missing messages
            self.peer.send(msg.sender, MsgRequest(self.peer, me_missing))

    def _peer_missing(self, msg):
        known = self.strg.get_known_tx_ids()
        peer_missing = set(known) - set(msg.data)
        if len(peer_missing) > 0:
            self.peer.send(msg.sender, SyncPong(self.peer, peer_missing))

    def _store_message(self, msg, msg_id=None):
        if not msg_id:
            msg_id = msg.id

        self.peer.store('msg_time', msg_id, self.peer.env.now)
        self.peer.store('msg_data', msg_id, msg)

    def handle_message(self, msg):
        
        if type(msg) == GossipMessage:
            self._store_message(msg)
        elif type(msg) == SyncPing:
            # Send sync pong if there more known messages 
            self._peer_missing(msg)
            self._self_missing(msg)
        elif type(msg) == SyncPong:
            self._self_missing(msg)
        elif type(msg) == MsgRequest:
            # Answer with message response 
            MessageResponder.handle_message(self, msg)
        elif type(msg) == MsgResponse:
            # Apply to the local storage 
            for k,v in msg.data.items():
                self._store_message(v, k)

    @property
    def messages(self):
        return GossipMessage, SyncPing, SyncPong, MsgRequest, MsgResponse

class RangedPullGossipService(PullGossipService):

    def _init_stores(self):
        self.peer.add_storage('msg_time', Storage())
        self.peer.add_storage('msg_data', RangedStorage())

    def _get_sync_indexes(self):
        # return the last index of known peers
        return self.strg.get_all_last()

    def _self_missing(self, msg):
        # msg contains dict of form {c_id: last}
        missing = set()
        for k,v in msg.data.items():
            self.strg.pre_add(k, v)
            for h in self.strg.get_holes(k):
                missing.add(str(h)+'_'+str(k))

        if len(missing) > 0:
            # Request missing messages
            self.peer.send(msg.sender, MsgRequest(self.peer, missing))
    
    def _peer_missing(self, msg):

        peer_missing = dict()
        my_last = self.strg.get_all_last()
        for k,v in my_last.items():
            if not msg.data.get(k) or msg.data[k] < v:
                peer_missing[k] = v

        if len(peer_missing) > 0:
            self.peer.send(msg.sender, SyncPong(self.peer, peer_missing))

    def _store_message(self, msg, msg_id=None):
        if msg:
            super()._store_message(msg, msg_id)


class PushPullGossipService(PullGossipService, GossipService):

    def handle_message(self, msg):

        if type(msg) == GossipMessage:
            GossipService.handle_message(self, msg)
        else:
            PullGossipService.handle_message(self, msg)
