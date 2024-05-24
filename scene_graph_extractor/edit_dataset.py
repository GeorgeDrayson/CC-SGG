#load pickle file
#convert networkx to pytorch
from util import Configuration
import dataset as ds
from torch_geometric.data import Data
import torch
from pathlib import Path
from util import convert_to_pytorch
from util import Configuration
from scene_graph_extractor import SceneGraphExtractor


if __name__ == "__main__":
    dataset_path = "C:/Users/drays/Documents/Coding/4yp-cornercases/dataset"
    assert Path(dataset_path).exists(), f"{dataset_path} does not exist"
    folder_names = sorted((Path(dataset_path)).glob("*"))
    for folder in folder_names:
        print(str(folder))
        scenegraph_extraction_config = Configuration(r"sg_config.yaml") #create scenegraph extraction config object
        sg_extraction_object = SceneGraphExtractor(scenegraph_extraction_config, input_path=dataset_path) #creating Carla Extractor using config
        sg_extraction_object.load_json([folder.stem]) #preprocesses sequences by extracting frame data for each sequence
        scenegraph_dataset = sg_extraction_object.get_dataset() #returned scenegraphs from extraction
        scenegraph_dataset.visualize(save_sg_path=str(folder))
        print('saving')
        scenegraph_dataset.save_pt(str(folder) + '/tensors')
