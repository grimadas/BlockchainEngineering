class BaseService(object):
    """
    BaseService that will trigger on a event handle_message
    """

    def handle_message(self, receiving_peer, msg):
        """this callable is added as a listener to Peer.listeners"""
        pass
