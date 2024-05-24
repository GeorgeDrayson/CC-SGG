import sys
from pathlib import Path
sys.path.append(str(Path("../../")))
from scene_graph import SceneGraph
from edge_extractor import EdgeExtractor
from dataset import Dataset
from tqdm import tqdm
from glob import glob
import json
from abc import ABC

class SceneGraphExtractor(ABC):
    def __init__(self,config,input_path=None,extract_shoulders=True,extract_incoming_lanes=True):
        self.scene_graphs = {}
        self.edge_extractor = EdgeExtractor(config,extract_shoulders,extract_incoming_lanes)
        self.input_path = config.location_data['input_path'] if input_path == None else input_path
        self.dataset = Dataset(config)
    
    def get_sequences(self, specific_folders):
        if specific_folders==None:
            # Get most recent folder
            most_recent_folder = len(list(Path(self.input_path).glob('*')))-1
            return [Path("%s/%s" % (self.input_path, most_recent_folder))]
        elif specific_folders == []:
            # Get all folders
            return [x for x in Path(self.input_path).iterdir() if x.is_dir()]
        else:
            # Get specific folders
            print([Path(specific_folders)])
            return [Path(specific_folders + '/')]
        
    def load_json(self,specific_folders=None):

        all_sequence_dirs = self.get_sequences(specific_folders)

        sg_extracted = {}
        for path in tqdm(all_sequence_dirs):
              seq = path.stem.split('_')[0]
              txt_path = sorted(list(glob("%s/**/*.json" % str(path), recursive=True)))[0]

              with open(txt_path, 'r') as scene_dict_f:
                  try:
                      num_of_scene_graphs_stored = 0
                      sg_extracted[seq] = {}
                      framedict = json.loads(scene_dict_f.read()) 
                      frame_names = sorted(list(framedict.keys()))
                      
                      for frame, frame_dict in framedict.items():
                          if str(frame) in frame_names: 
                              scenegraph = SceneGraph(self.edge_extractor, framedict = frame_dict)
                              sg_extracted[seq][num_of_scene_graphs_stored] = scenegraph
                              num_of_scene_graphs_stored += 1

                  except Exception as e:
                      import traceback
                      print("We had a problem creating the Carla scenegraphs")
                      print(e)
                      traceback.print_exc()
                  
        self.dataset.scene_graphs = sg_extracted

    def get_dataset(self):
        return self.dataset
