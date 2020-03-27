from p2psimpy.logger import setup_logger


class BaseService(object):
    def __init__(self, peer,  **kwargs):
        self.peer = peer
        self.__dict__.update(kwargs)

        self.logger = peer.logger

    @property
    def env(self):
        return self.peer.env

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.peer.name)


class BaseHandler(BaseService):
    """
    BaseService that will trigger on a event handle_message
    """

    def handle_message(self, msg):
        """this callable is added as a listener to Peer.listeners"""
        raise NotImplementedError

    @property
    def messages(self):
        # Specify what messages will be processed by the service
        raise NotImplementedError


class BaseRunner(BaseService):

    def start(self):
        """Start service run"""
        self.env.process(self.run())

    def run(self):
        """The main running function"""
        raise NotImplementedError

class ScheduledRunner(BaseRunner):

    def next(self):
        raise NotImplementedError

    def run_script(self):
        raise NotImplementedError

    def run(self):
        while self.next():
            self.run_script()
            


class MockHandler(BaseHandler):
    """
    BaseService that will trigger on a event handle_message
    """

    def __init__(self, peer, **kwargs):
        super().__init__(peer, **kwargs)
        self._messages = kwargs.pop('messages', [])

    def handle_message(self, msg):
        """this callable is added as a listener to Peer.listeners"""
        pass

    @property
    def messages(self):
        # Specify what messages will be processed by the service
        return self._messages


class MockRunner(BaseRunner):

    def start(self):
        """Start service run"""
        pass

    def run(self):
        """The main running function"""
        pass
