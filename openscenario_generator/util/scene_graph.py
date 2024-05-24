import torch
import networkx as nx
from torch_geometric.data import Data
from torch_geometric.utils import to_networkx

class NXSceneGraph:
    def __init__(self, x,edge_idx, config):
        self.x = x
        self.edge_idx = edge_idx
        self.config = config
        data_sg = Data(x=x, edge_index=edge_idx)
        sg = to_networkx(data_sg)
        self.sg = nx.MultiDiGraph(sg.to_directed())
        self.add_node_attributes()
    
    def add_velocity_edges(self, nodes):
        for i in range(len(nodes)):
            self.sg.add_edge(nodes[i].item(), nodes[i].item())

    def add_node_attributes(self):
        x_list = self.x.tolist()
        nx.set_node_attributes(self.sg, 'filled', name='style')
        for i in range(len(x_list)):
            nx.set_node_attributes(self.sg, {i: x_list[i]}, name='label')
            nx.set_node_attributes(self.sg, {i: self.config.node_extraction_settings['NODE_COLOURS'][x_list[i]]}, name='fillcolor')

    def add_edge_attributes(self, edge_values):
        for node1, node2, edge in self.sg.edges(keys=True):
            column = torch.tensor([node1, node2])
            index = torch.where(torch.all(self.edge_idx == column.reshape(-1, 1), dim=0))
            nx.set_edge_attributes(self.sg, {(node1, node2, edge): {'label': edge_values[index[0][edge]]}})

class NXExtendedSceneGraph(NXSceneGraph):
    def __init__(self, x, edge_idx, config, repeated_edges):
        NXSceneGraph.__init__(self, x, edge_idx, config)
        self.add_repeated_edges(repeated_edges)

    def add_repeated_edges(self, repeated_edges):
        for i in range(repeated_edges.shape[1]):
            # Get start and end of repeated edge class but with different edge attributes
            start = repeated_edges[0][i].item()
            end = repeated_edges[1][i].item()
            for i in range(start,end,1):
                e = self.edge_idx[:,i+1]
                self.sg.add_edge(e[0].item(),e[1].item())
        self.sg.add_edge(e[0].item(),e[1].item())