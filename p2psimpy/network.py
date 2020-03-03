import logging

from p2psimpy.utils import get_latency_delay


class Connection:

    def __init__(self, sender, receiver):
        """ Class to represent connection between two peers
        :param locations: Map that contains the latencies between locations
        """
        self.env = sender.env
        self.locations = self.env.locations

        self.sender = sender
        self.receiver = receiver
        self.start_time = self.env.now

    def __repr__(self):
        return '<Connection %r -> %r>' % (self.sender, self.receiver)

    @property
    def latency(self):
        return get_latency_delay(
            self.locations, self.sender.config.location, self.receiver.config.location)

    @property
    def bandwidth(self):
        return min(self.sender.config.bandwidth_ul, self.receiver.config.bandwidth_dl)

    def send(self, msg, connect=False):
        """
        Simulate fire and forget send.
        i.e. we don't get notified if the message was not delivered

        :param msg: Message tuple to deliver
        :param connect : deliver message even if not connected yet, similar to UDP
        """

        def _transfer():
            bytes = msg.size
            delay = bytes / self.sender.config.bandwidth_ul
            delay += bytes / self.receiver.config.bandwidth_dl
            delay += self.latency / 2
            yield self.env.timeout(delay)
            if self.receiver.is_connected(msg.sender) or connect:
                self.receiver.msg_queue.put(msg)

        self.env.process(_transfer())
