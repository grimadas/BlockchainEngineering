class PeerSelectionStrategy(object):

    def choose_peers(self, candidates, num=1):
        """This method returns num peers from candidates list of peers """
        pass


class SlowPeerSelectionStrategy(PeerSelectionStrategy):

    def choose_peers(self, candidates, num=1):
        return candidates[:num]
