

class Storage:

    def __init__(self):
        self.txs = dict()
        self.times_seen = dict()

    def add(self, tx_id, tx):
        if tx_id not in self.txs:
            self.txs[tx_id] = tx
            self.times_seen[tx_id] = 1
        else:
            self.times_seen[tx_id] += 1
