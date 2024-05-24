from carla_world import World
from semantics_extractor import SemanticsExtractor
import argparse
import time

def main():

    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '--save_path',
        default='semantic_files',
        type=str,
        help='where to save the extracted json files (default: semantic_files)')
    argparser.add_argument(
        '--traffic_light_detection',
        default=False,
        type=bool,
        help='choose whether to extract traffic light info (default: True)')
    args = argparser.parse_args()

    #Instantiate World and SemanticsExtractor
    carla_world = World(args, args.save_path)
    new_path = "%s/%s" % (str(carla_world.root_path), carla_world.num_of_existing_datapoints)
    extractor = SemanticsExtractor(carla_world.ego_actor, new_path, args.traffic_light_detection, max_count=30)

    start_time = 0
    recording_started = False
    print('WAITING FOR EGO TO MOVE')

    while True:   

        timestamp = None
        reset = False

        # Check if ego vehicle has started moving
        if (not recording_started and (carla_world.get_ego_actor_velocity() > 0.5)):
            recording_started = True
            print('RECORDING STARTED')

        carla_world.world.wait_for_tick()

        # Get timestamp of snapshot 
        if carla_world.world: 
            snapshot = carla_world.world.get_snapshot()
            if snapshot: timestamp = snapshot.timestamp

        # If ego vehicle has moved (recording_started=True) then extract frame
        if recording_started: 
            if (start_time > 0): time.sleep(0.25 - ((time.time() - start_time) % 1))
            start_time = time.time()
            print('TAKING FRAME')
            reset = extractor.tick(carla_world.world, carla_world.map, timestamp)

        # If max frames have been reached
        if reset: break

if __name__ == '__main__':
    main()
    print('DONE')
