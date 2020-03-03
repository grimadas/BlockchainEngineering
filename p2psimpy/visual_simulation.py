from p2psimpy.simulation import BaseSimulation
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
from networkx.drawing.nx_agraph import graphviz_layout

from p2psimpy.consts import MBit


class VisualSimulation(BaseSimulation):

    def __init__(self, num_bootstrap=1, delta=50, total_run=3000):
        super().__init__(num_bootstrap)

        # visualize the graph
        fig = plt.figure(figsize=(8, 8))
        # interval: draws a new frame every *interval* milliseconds
        self.total_run = total_run
        self.anim = FuncAnimation(fig, self.update, interval=delta, blit=False)
        plt.show()

    def start(self):
        self.anim.event_source.start()

    def update(self):
        if self.env.now > self.total_run:
            self.anim.event_source.stop()
        self.run(self.env.now+1)
        G = self.get_graph()
