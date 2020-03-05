

class Storage:

    txs = dict()

    def add(self, tx_id, tx):
        if tx_id not in self.txs:
            self.txs[tx_id] = tx
