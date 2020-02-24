class BaseMessage(object):
    base_size = 20

    def __init__(self, sender, data=None):
        self.sender = sender
        self.data = data

    @property
    def size(self):
        return self.base_size + len(repr(self.data))

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


###### Messages ###############

class Ping(BaseMessage):
    pass


class Pong(BaseMessage):
    pass


class RequestPeers(BaseMessage):
    pass


class PeerList(BaseMessage):
    def __init__(self, sender, peers):
        super().__init__(sender)
        self.sender = sender
        self.data = set(peers)


class Hello(BaseMessage):
    "Offer a peer to connect"
    pass
