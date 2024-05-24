# some_file.py
import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, '../model')
from dataloader import Configuration
import argparse
from PIL import Image
from networkx.drawing import nx_pydot
from util.util import get_edge_values, get_lane_topology, load_ontologies, extract_location_relation
from util.scene_graph import NXSceneGraph, NXExtendedSceneGraph
from util.corner_case import CornerCase
import matplotlib.pyplot as plt
from io import BytesIO


#TODO add check for vehicle category

#nice to have
#TODO distinguish location and velocity self edges on graph


def extract_scenario_information(output, show_sg=False, show_cc=False):

    # get the prediction and knowledge graph
    edge_idx = output[0]['edge_idx']
    edge_attr = output[0]['edge_attr']
    y_pred = output[0]['y_pred']
    x_tensor = output[0]['x']
    poss_edge_idx = output[0]['poss_edge_idx']
    poss_edge_attr = output[0]['poss_edge_attr']
    repeated_edges = output[0]['repeated_edges']

    # separate the edge attributes
    edge_binary_values = edge_attr[:, :2]
    edge_cat_tensor = edge_attr[:, 2:]
    poss_edge_binary_values = poss_edge_attr[:, :2]
    poss_edge_cat_tensor = poss_edge_attr[:, 2:]

    # load the ontologies
    config = Configuration('C:/Users/drays/Documents/Coding/4yp-cornercases/scene_graph_extractor/sg_config.yaml')
    x, edge_categories, poss_edge_categories = load_ontologies(config, x_tensor, edge_cat_tensor, poss_edge_cat_tensor)
    x_list = x.tolist()
    print(x_list)

    #get lane topology
    lane_topology = get_lane_topology(x_list)

    #get location information from sg
    location_array = extract_location_relation(edge_categories, edge_binary_values, edge_idx, x_list, lane_topology)

    # get the edge values as strings
    poss_edge_values, throw = get_edge_values(poss_edge_categories, poss_edge_binary_values, config, poss_edge_idx)
    edge_values, nodes_with_velocity_edges = get_edge_values(edge_categories, edge_binary_values, config, edge_idx)

    # convert to networkx
    kg = NXExtendedSceneGraph(x, poss_edge_idx, config, repeated_edges)

    #create corner case scene graph by removing nodes with low prediction score
    corner_case = CornerCase(y_pred, poss_edge_idx, poss_edge_values, kg)
    # cc information in the form [laneIdEgo, laneIdAdv, safeDistance?, orientation]
    cc_information = corner_case.extract_corner_case_information(x_list, lane_topology, location_array)

    if show_sg==True:
        scene_graph = NXSceneGraph(x, edge_idx, config)
        scene_graph.add_velocity_edges(nodes_with_velocity_edges)
        scene_graph.add_edge_attributes(edge_values)

        sg = nx_pydot.to_pydot(scene_graph.sg)
        sg_img = sg.create_png()
        sg_img = Image.open(BytesIO(sg_img))

        plt.plot()
        plt.imshow(sg_img)
        plt.axis('off')
        plt.show()
    
    if show_cc==True:

        cc_sg = nx_pydot.to_pydot(corner_case.cc_sg)
        cc_sg_img = cc_sg.create_png()
        cc_sg_img = Image.open(BytesIO(cc_sg_img))
        
        plt.plot()
        plt.imshow(cc_sg_img)
        plt.axis('off')
        plt.show()

    return location_array, cc_information