from util import Configuration
from scene_graph_extractor import SceneGraphExtractor

def main():
    scenegraph_extraction_config = Configuration(r"sg_config.yaml") #create scenegraph extraction config object
    sg_extraction_object = SceneGraphExtractor(scenegraph_extraction_config, extract_shoulders=True,extract_incoming_lanes=True) #creating Carla Extractor using config
    sg_extraction_object.load_json('../dataset/CyclistCrashLeft') #process each frame
    scenegraph_dataset = sg_extraction_object.get_dataset() #get scenegraph dataset
    #scenegraph_dataset.save_pkl() #save dataset as .pkl
    scenegraph_dataset.visualize(save_sg_path=scenegraph_dataset.images_path,show=True) #visualize and save scene graphs as pngs
    scenegraph_dataset.save_pt() #save scene graphs as pytorch tensors

if __name__ == "__main__":
    main()
 
    