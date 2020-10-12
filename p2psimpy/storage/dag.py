import networkx as nx


class DagStorage(object):

    def __init__(self):
        self.dag = nx.DiGraph()

    def add(self, msg_id, parent_id, msg):
        self.dag.add_edge(msg_id, parent_id, data=msg)

    def get(self, msg_id):
        if msg_id in self.dag:
            return dict(self.dag[msg_id])
        else:
            return None

    def get_longest_chains(self):
        G1 = self.dag.copy()
        path = nx.dag_longest_path(G1)
        while len(path) > 0:
            yield path
            G1.remove_node(path[0])
            path = nx.dag_longest_path(G1)
