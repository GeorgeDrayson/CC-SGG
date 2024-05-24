#load pickle files of dataset entries
#convert networkx to pytorch
from util import Configuration
import dataset as ds
from torch_geometric.data import Data
import torch
from pathlib import Path
from util import convert_to_pytorch


if __name__ == "__main__":
    scenegraph_extraction_config = Configuration(r"sg_config.yaml")
    dataset = ds.SceneGraphDataset(scenegraph_extraction_config)
    dataset_path = "C:/Users/drays/Documents/Coding/4yp-cornercases/dataset"

    assert Path(dataset_path).exists(), f"{dataset_path} does not exist"
    folder_names = sorted((Path(dataset_path)).glob("*"))
    for folder in folder_names:
        pickle_file = list(sorted(Path(folder).glob("*.pkl")))
        dataset = dataset.load_pkl(pickle_file[0])
        save_folder = str(folder) + '/non_sparse_tensors'
        Path(save_folder).resolve().mkdir(exist_ok=True)
        dataset.save_pt(save_folder)