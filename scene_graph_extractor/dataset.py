from pathlib import Path
from abc import ABC
import pickle as pkl
from util import visualize, convert_to_pytorch
import torch

class Dataset(ABC):

    def __init__(self, config = None, scene_graphs= {}):
        self.dataset_save_path, self.images_path, self.pt_path = self.create_new_save_path(config.location_data["save_path"])
        self.dataset_filename = None
        self.scene_graphs = scene_graphs

    def create_new_save_path(self,dataset_save_path):
        root_path = Path(dataset_save_path).resolve()
        root_path.mkdir(exist_ok=True)
        num_of_existing_datapoints = len(list(root_path.glob('*')))
        dataset_save_path = "%s\\%s" % (str(root_path), num_of_existing_datapoints)

        images_path = dataset_save_path + '/images'
        pt_path = dataset_save_path + '/tensors'
        Path(dataset_save_path).resolve().mkdir(exist_ok=True)
        Path(images_path).resolve().mkdir(exist_ok=True)
        Path(pt_path).resolve().mkdir(exist_ok=True)

        return dataset_save_path, images_path, pt_path

    def save_pkl(self):
        with open(self.dataset_save_path + '/sg.pkl', 'wb') as f:
            pkl.dump(self, f)

    def load_pkl(self,filename):
        with open(filename, 'rb') as f:
            return pkl.load(f)
        
    def visualize(self, specific_frame = None, save_sg_path=None, show = False):
        for folder_name in self.scene_graphs:
            sg = self.scene_graphs[folder_name]
        if specific_frame == None:
            for key in sg: visualize(sg,key,save_sg_path,show)
        else:
            visualize(sg,specific_frame,save_sg_path,show)

    def save_pt(self, save_sg_path=None):
        if save_sg_path == None: save_sg_path = self.pt_path
        Path(save_sg_path).resolve().mkdir(exist_ok=True)

        for folder_name in self.scene_graphs:
            sg = self.scene_graphs[folder_name]
        for key in sg:
            filename = save_sg_path + '/' + str(key) + '.pt'
            data = convert_to_pytorch(sg[key].g, sg[key].edge_extractor.node_categories, sg[key].edge_extractor.edge_categories)
            torch.save(data,filename)
