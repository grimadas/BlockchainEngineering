class Connection:

    def __init__(self, sender, receiver):
        """ Class to represent connection between two peers
        :param locations: Map that contains the latencies between locations
        """
        self.env = sender.env
        self.sender = sender
        self.receiver = receiver

        self.get_latency = self.sender.sim.get_latency_delay
        self.start_time = self.env.now

    def __repr__(self):
        return '<Connection %r -> %r>' % (self.sender, self.receiver)

    @property
    def latency(self):
        return max(self.get_latency(self.sender.location, self.receiver.location), 0)

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
            num_bytes = msg.size
            sender = msg.sender
            delay = num_bytes / self.sender.bandwidth_ul
            delay += self.latency / 2
            yield self.env.timeout(delay)
            if self.receiver.is_connected(sender) or connect:
                self.receiver.msg_queue.put(msg)

        self.env.process(_transfer())
