from pytorch_lightning.loggers import WandbLogger
import dataloader
import torch
import pytorch_lightning as pl
import model as m
from sklearn.preprocessing import OneHotEncoder

def predict(FLAGS):
    wandb_logger = WandbLogger(save_dir="") # add path to the dir
    
    train_dataloader, val_dataloader, pred_dataloader = dataloader.load_single_data(FLAGS)

    torch.set_float32_matmul_precision('high')
    model = m.ModelTrainer(model=m.GModel()).load_from_checkpoint(FLAGS.checkpoint)
    trainer = pl.Trainer(accelerator='gpu', devices=[0], log_every_n_steps=5,
                         val_check_interval=len(train_dataloader), logger=wandb_logger)

    # predict with the model
    output = trainer.predict(model, pred_dataloader)
    return output

def get_lane_topology(x_list):
    no_of_lanes = 0
    for i in range(len(x_list)):
        if x_list[i] in ['lane','pavement','shoulder']:
            no_of_lanes += 1
    n = int(no_of_lanes/2)
    topology = [-i for i in range(-n, n + 1) if i != 0]
    print(topology)
    return topology

def extract_location_relation(edge_categories, binary_values, edge_idx, x_list, lane_top):
    location_array = {}
    for i in range(len(edge_categories)):
        node = edge_idx[:,i][0]
        key = x_list[node]
        if x_list[node] != 'ego_car': key += str(node.item())
        relation = edge_categories[i]

        if relation == 'location':
            v = binary_values[i,:].numpy()
            v = v.astype(int)
            if key not in location_array: location_array[key] = {}
            location_array[key]['location']  = [v[0],-v[1]]
        
        if edge_categories[i] == 'isIn' and x_list[edge_idx[:,i][1]] != 'road':
            if key not in location_array: location_array[key] = {}
            location_array[key]['laneId'] = lane_top[edge_idx[:,i][1]-1]
            
    return location_array

def get_edge_values(edge_categories, binary_values, config, edge_idx):
    edge_values = []
    nodes_with_velocity_edges = []

    for i in range(len(edge_categories)):
        v = binary_values[i,:].numpy()
        v = v.astype(int)

        if edge_idx[:,i][0] != edge_idx[:,i][1]:
            binary_relations = config.edge_extraction_settings[edge_categories[i]]["binary_relations"]
            v = [key for key, value in binary_relations.items() if (value == v).all()]
        elif edge_categories[i] == 'location':
            v = [v]
        else:
            v = [v]
            nodes_with_velocity_edges.append(edge_idx[:,i][0])
        edge_values.append(v[0])

    return edge_values, nodes_with_velocity_edges

def load_ontologies(config, x, edge_categories, poss_edge_categories):
    # load the ontologies
    actor_list = [x for x in map(lambda el: [el], config.node_extraction_settings["NODE_CATEGORIES"])]
    edge_list = [x for x in map(lambda el: [el], config.edge_extraction_settings['EDGE_CATEGORIES'])]

    # reverse the one hot encoding to get the strings
    encoder_x = OneHotEncoder().fit(actor_list)
    encoder_edge = OneHotEncoder().fit(edge_list)
    x = encoder_x.inverse_transform(x).ravel()
    edge_categories = encoder_edge.inverse_transform(edge_categories).ravel()
    poss_edge_categories = encoder_edge.inverse_transform(poss_edge_categories).ravel()
    
    return x, edge_categories, poss_edge_categories