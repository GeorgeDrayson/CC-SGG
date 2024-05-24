from agents.navigation.basic_agent import BasicAgent
from semantics_extractor.carla_world import World
import argparse
import carla
from automatic_control import HUD

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
args = argparser.parse_args()

if __name__ == "__main__":

    hud = HUD(1280, 720)
    carla_world = World(args)
    ego = carla_world.ego_actor
    agent = BasicAgent(ego)
    while True:
        ego.apply_control(agent.run_step())
