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

    def batch_add(self, batch_txs):
        self.txs.update(batch_txs)

    def remove(self, tx_id):
        self.txs.pop(tx_id)
        self.times_seen.pop(tx_id)

    def clear_all(self):
        self.txs.clear()
        self.times_seen.clear()

    def get_known_tx_ids(self):
        return self.txs.keys()

    def get(self, msg_id):
        return self.txs.get(msg_id)

    def get_all_by_prefix(self, prefix):
        return {k: v for k, v in self.txs.items() if str(k).startswith(prefix)}


class RangedStorage(Storage):

    def __init__(self):
        super().__init__()
        self.index = dict()

    def get_all_last(self):
        return {k: self.index[k]['last'] for k in self.index}

    def get_last(self, p_id):
        return self.index[p_id]['last'] if p_id in self.index else 0

    def get_holes(self, p_id):
        return self.index[p_id]['holes'] if p_id in self.index else {}

    def pre_add(self, p_id, tx_id):
        if p_id not in self.index:
            self.index[p_id] = {'holes': set(), 'last': 0}

        for k in range(self.index[p_id]['last'] + 1, tx_id + 1):
            # Adding holes
            self.index[p_id]['holes'].add(k)

    def add(self, tx_id, tx):
        p_id, c = str(tx_id).split('_')
        p_id, c = int(p_id), int(c)

        self.pre_add(p_id, c)
        if c > self.index[p_id]['last']:
            self.index[p_id]['last'] = c

        if c in self.index[p_id]['holes']:
            # Fill in the hole
            self.index[p_id]['holes'].remove(c)
        super().add(tx_id, tx)
