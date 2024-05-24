import matplotlib
import matplotlib.pyplot as plt
from PIL import Image
from networkx.drawing import nx_pydot
from io import BytesIO
from torch_geometric.data import Data
import torch
matplotlib.use('Tkagg')
from sklearn.preprocessing import OneHotEncoder
import torch_geometric.transforms as T
import yaml
from pathlib import Path

#~~~~~~~~~UTILITY CLASSES~~~~~~~~~~~~

class Node:
    def __init__(self, name, attr, label=None):
        self.name = name
        self.attr = attr
        self.label = label  # Actor Category (ie "car")

class Configuration:
    def __init__(self, args):
        self.yaml_path = Path(args).resolve()
        with open(self.yaml_path, 'r') as f:
            self.args = yaml.safe_load(f)
            for arg_name, arg_value in self.args.items():
                self.__dict__[arg_name] = arg_value

#~~~~~~~~~UTILITY FUNCTIONS~~~~~~~~~~~~

def draw_scenegraph_pydot(sg):
    A = nx_pydot.to_pydot(sg)
    img = A.create_png()
    return Image.open(BytesIO(img))

def visualize(sg, key, save_sg_path = None, show = False):
    sg_img = draw_scenegraph_pydot(sg[key].g)
    plt.plot()
    plt.imshow(sg_img)
    plt.axis('off')

    if save_sg_path is not None: 
        plot_filename = save_sg_path + '/' + str(key) + '.png'
        plt.savefig(plot_filename, format="png")

    if show: plt.show()

def convert_to_pytorch(scene_graph,actor_categories,edge_categories):
    x, edge_index, edge_value, edge_category = [], [], [], []

    # Get category lists in the correct form for one hot encoding
    actor_categories = [x for x in map(lambda el: [el], actor_categories)]
    edge_categories = [x for x in map(lambda el: [el], edge_categories)]

    # Get nodes
    for node in enumerate(scene_graph.nodes(data=True)):
        x.append([node[1][1]['value']])

    # Get edges
    node_name2idx = {node:idx for idx, node in enumerate(scene_graph.nodes)}

    for node1, node2, edge in scene_graph.edges(data=True):
        edge_index.append((node_name2idx[node1], node_name2idx[node2]))
        edge_value.append([edge['value'][0], edge['value'][1]])
        edge_category.append([edge['category']])

    # One hot encode x
    encoder_x = OneHotEncoder().fit(actor_categories)
    x = encoder_x.transform(x).toarray()

    # One hot encode edge category
    encoder_edge = OneHotEncoder().fit(edge_categories)
    edge_category = encoder_edge.transform(edge_category).toarray()

    # Convert arrays to tensors
    x = torch.tensor(x)
    edge_index = torch.tensor(edge_index).T
    edge_value = torch.tensor(edge_value)
    edge_category = torch.tensor(edge_category)
    edge_attr = torch.cat((edge_value,edge_category), -1)

    # Create dataset and convert the edge attributes into a sparse tensor
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

    data = T.ToSparseTensor(attr='edge_attr')(data)
    row, col, edge_attr = data.adj_t.coo()
    return data
    