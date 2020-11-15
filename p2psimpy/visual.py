import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
from networkx.drawing.nx_pydot import graphviz_layout


def visualize_peer_client_network(G):
    # Draw client/ peer network using matplotlib
    fig = plt.figure(figsize=(10,10))
    master_nodes = [n for (n,ty) in \
        nx.get_node_attributes(G,'type').items() if ty == 'peer']
    client_nodes = [n for (n,ty) in \
        nx.get_node_attributes(G,'type').items() if ty == 'client']

    pos = graphviz_layout(G)

    nx.draw_networkx_nodes(G, pos, nodelist=master_nodes, \
        node_color='blue', node_shape='o', node_size=500)
    nx.draw_networkx_nodes(G, pos, nodelist=client_nodes,  \
        node_color='green', node_shape='^', node_size=100, label=1)

    nx.draw_networkx_labels(G, pos, labels={k:k for k in master_nodes}, font_color='w')

    nx.draw_networkx_edges(G, pos, edgelist=G.subgraph(master_nodes).edges(), width=1.5)
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(nbunch=client_nodes),  style='dotted')

class VisualSimulation(object):

    def __init__(self, simulation, delta=50, total_run=3000):
        # interval: draws a new frame every *interval* milliseconds
        self.sim = simulation
        self.delta = delta
        self.total_run = total_run
        self.anim = FuncAnimation(fig, self.update, interval=delta, blit=False)

    def start(self):
        self.anim.event_source.start()

    def update(self):
        if self.sim.env.now > self.total_run:
            self.anim.event_source.stop()
        self.sim.run(self.env.now+self.delta)
        G = self.sim.get_graph()
        visualize_peer_client_network(G)
        plt.show()
