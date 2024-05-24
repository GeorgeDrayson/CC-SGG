from pathlib import Path
import carla

class World():

    def __init__(self, args, save_path=""):
        self.args = args
        self.client = carla.Client(args.host, args.port)
        self.client.set_timeout(20.0)
        self.world = self.client.get_world()
        self.map = self.world.get_map()
        self.ego_actor = self.get_ego_actor()
        if save_path != "":
            Path(save_path).resolve().mkdir(exist_ok=True)
            self.root_path = Path(save_path)  
            self.num_of_existing_datapoints = len(list(self.root_path.glob('*')))      

    def get_ego_actor(self):
        actor_list = self.world.get_actors()
        for actor in actor_list: 
            if "role_name" in actor.attributes:
                if(actor.attributes["role_name"] == 'hero'):
                    return actor
        raise ValueError('Could not find the ego actor')
    
    def get_ego_actor_velocity(self):
        velocity = self.ego_actor.get_velocity()
        abs_velocity = (velocity.x**2 + velocity.y**2)**0.5
        return abs_velocity