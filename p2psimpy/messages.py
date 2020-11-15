from collections.abc import Iterable

class BaseMessage(object):
    __slots__ = ('sender', 'data', 'pre_task', 'post_task')
    base_size = 20

    def __init__(self, sender, data=None, **kwargs):
        self.sender = sender
        self.data = data
        self.pre_task = kwargs.pop('pre_task', None)
        self.post_task = kwargs.pop('post_task', None)

    @property
    def size(self):

        def _count_size(sub_msg):
            if isinstance(sub_msg, BaseMessage):
                return sub_msg.size
            else: 
                return len(repr(sub_msg))

        iter_size = 0 
        if isinstance(self.data, Iterable):
            # data is an iterable - go through and add to size 
            for sub_msg in self.data: 
                iter_size += _count_size(sub_msg)
            if type(self.data) == dict:
                for sub_msg in self.data.values():
                    iter_size += _count_size(sub_msg)
        else:
            iter_size += len(repr(self.data))

        return self.base_size + iter_size

    def __repr__(self):
        msg_type = '%s:' % self.__class__.__name__
        data = self.data if self.data else ""
        return msg_type + str(data)


########## Messages ###############

class Ping(BaseMessage):
    """Response to ping"""
    pass


class Pong(BaseMessage):
    """Response to pong"""
    pass


class RequestPeers(BaseMessage):
    """Request peers to connect to"""
    pass


class PeerList(BaseMessage):
    """Peer list with known peers"""

    def __init__(self, sender, peers, **kwargs):
        super().__init__(sender, set(peers), **kwargs)

    def __repr__(self):
        return 'PeerList'


class Hello(BaseMessage):
    """Offer a peer to connect"""
    pass

############ Gossip Network Messages ##############

class GossipMessage(BaseMessage):

    base_size = 250
    
    def __init__(self, sender, msg_id, data, ttl, **kwargs):
        super().__init__(sender, data, **kwargs)
        self.ttl = ttl
        self.id = msg_id

class SyncPing(BaseMessage):
    pass

class SyncPong(BaseMessage):
    pass

class MsgRequest(BaseMessage):
    pass

class MsgResponse(BaseMessage):
    pass 
