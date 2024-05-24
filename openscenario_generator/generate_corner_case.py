from scenario import Scenario
from scenariogeneration import prettyprint
from extract_scenario_information import extract_scenario_information
from util.util import predict
import argparse

#TODO extract lane info from scene graph
#TODO use this lane info to code the lane changing maneuver
#TODO tweak lane maneuver so it works for all cases


parser = argparse.ArgumentParser()
parser.add_argument('--project', '-p', type=str, required=False, default="cornercases",
                    help='Wandb project name')
parser.add_argument('--entity', '-e', type=str, required=False, default="george-drayson",
                    help='Wandb entity name')
parser.add_argument('--dataset', '-d', type=str, required=False, default="../ddataset",
                    help='Path to your dataset')
parser.add_argument('--sweep_config', '-s', type=str, required=False, default="./sweep_config.yaml",
                    help='Sweep configuration file location')
parser.add_argument('--output_folder', '-o', type=str, required=False, default="",
                    help='Where to save the WANDB output')
parser.add_argument('--checkpoint', '-c', type=str, required=False, default="../model/last.ckpt",
                    help='Model checkpoint')
parser.add_argument('--motorway', '-m', type=bool, required=False, default=True,
                    help='Motorway scenarios')

FLAGS, unparsed = parser.parse_known_args()


if __name__ == "__main__":

    #make prediction
    output = predict(FLAGS)

    #extract location information from scene graph and corner case
    sg_information, cc_information = extract_scenario_information(output, show_sg=True, show_cc=True)

    if FLAGS.motorway==True:
        town_map="Town04"
        for key in cc_information:
            cc_information[key]['laneId'][0] += 1
            sg_information[key]['laneId'] +=1
        offset=50
    else:
        town_map="Town01"
        offset=150

    print(sg_information)
    print(cc_information)

    #sg_information = {'ego_car': [142, -133], 'car8': [177, -133]}
    #cc_information = {'ego_car': {'category': 'ego_car', 'laneId': -1, 'safeDistance': False}, 'car8': {'category': 'bicycle', 'laneId': -1, 'orientation': 'inFrontOf', 'safeDistance': False}}
    
    #generate and print openscenario file
    sce = Scenario(sg_information, cc_information,town=town_map, offset=offset)
    #prettyprint(sce.scenario().get_element())    
    sce.generate(".")

    print('Generated scenario')
