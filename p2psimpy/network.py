from p2psimpy.utils import get_latency_delay


class Connection:

    def __init__(self, sender, receiver):
        """ Class to represent connection between two peers
        :param locations: Map that contains the latencies between locations
        """
        self.env = sender.env
        self.locations = sender.sim.locations
        self.get_latency = self.sender.sim.get_latency_delay

        self.sender = sender
        self.receiver = receiver

    def __repr__(self):
        return '<Connection %r -> %r>' % (self.sender, self.receiver)

    @property
    def latency(self):
        return self.get_latency(self.sender.location, self.receiver.location)

    @property
    def bandwidth(self):
        return min(self.sender.bandwidth_ul, self.receiver.bandwidth_dl)

    def send(self, msg, connect=False):
        """
        Simulate fire and forget send.
        i.e. we don't get notified if the message was not delivered

        :param msg: Message tuple to deliver
        :param connect : deliver message even if not connected yet, similar to UDP
        """

        def _transfer():
            bytes = msg.size
            delay = bytes / self.sender.bandwidth_ul
            delay += bytes / self.receiver.bandwidth_dl
            delay += self.latency / 2
            yield self.env.timeout(delay)
            if self.receiver.is_connected(msg.sender) or connect:
                self.receiver.msg_queue.put(msg)

        self.env.process(_transfer())
