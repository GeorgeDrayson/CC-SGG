import carla
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
from actor import Actor
from lane_extractor import LaneExtractor

class SemanticsExtractor():

    def __init__(self, ego, store_path, tlight_detection, max_count=30):
        self.lane_extractor = LaneExtractor()
        self.ego = ego
        t = self.ego.get_transform()
        self.distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
        self.frame_count = 0
        self.max_count = max_count
        self.output_dir = Path(store_path).resolve()
        self.output_dir.mkdir(exist_ok=True)
        self.max_distance = 100
        self.max_vehicle_distance = 200
        self.framedict=defaultdict()
        self.traffic_light_detection = tlight_detection #choose whether dataloader takes traffic lights into account

    def get_ego_vehicle(self, waypoint, lanedict):
        ego = Actor(self.ego, lanedict, waypoint, dynamic=True)
        ego.get_brake_attribute()
        return ego.get_attributes()

    def get_vehicles(self, map, vehicles, lanedict):
        vehicle_dict=defaultdict()
        for vehicle in vehicles: 
            if vehicle.id != self.ego.id and self.distance(vehicle.get_location()) < self.max_vehicle_distance:
                vehicle_wp = map.get_waypoint(vehicle.get_location(), project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
                vehicle_instance = Actor(vehicle, lanedict, vehicle_wp, dynamic=True)
                vehicle_instance.get_brake_attribute()
                vehicle_dict[vehicle.id] = vehicle_instance.get_attributes()
        return vehicle_dict
    
    def get_pedestrians(self, map, pedestrians, lane_dict):
        pedestrian_dict=defaultdict()
        for pedestrian in pedestrians:
            if pedestrian.get_location().distance(self.ego.get_location()) < self.max_distance:
                pedestrian_wp = map.get_waypoint(pedestrian.get_location(), project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
                pedestrian_instance = Actor(pedestrian, lane_dict, pedestrian_wp, dynamic=True, name='Pedestrian')
                pedestrian_dict[pedestrian.id] = pedestrian_instance.get_attributes()
        return pedestrian_dict

    def get_traffic_lights(self, waypoint, traffic_lights, lane_dict, light_dict=defaultdict()):
        for traffic_light in traffic_lights:
            traffic_light_instance = Actor(traffic_light, lane_dict, waypoint, dynamic=False, name='Traffic Light')
            traffic_light_instance.get_traffic_light_attribute()
            light_dict[traffic_light.id]=traffic_light_instance.get_attributes()
        return light_dict
    
    def get_signs(self, waypoint, signs, lane_dict):
        sign_dict=defaultdict()
        for sign in signs:
            if sign.get_location().distance(self.ego.get_location()) < (self.max_distance/2):
                sign_instance = Actor(sign, lane_dict, waypoint, dynamic=False, name='Sign')
                sign_dict[sign.id]=sign_instance.get_attributes()
        return sign_dict
    
    def get_objects(self, map, objects, lane_dict):
        object_dict=defaultdict()
        for object in objects:
            if object.get_location().distance(self.ego.get_location()) < self.max_distance:
                object_wp = map.get_waypoint(object.get_location(), project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
                object_instance = Actor(object, lane_dict, object_wp, dynamic=False)
                object_dict[object.id] = object_instance.get_attributes()
        return object_dict

    def tick(self,world, map, timestamp):

        # Get ego waypoint
        waypoint = map.get_waypoint(self.ego.get_location(), project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Shoulder | carla.LaneType.Sidewalk))
        
        # Check whether ego is in the correct lane
        self.lane_extractor.wrong_lane_test(waypoint)

        # Extract lanes, vehicles and pedestrians
        lane_dict = self.lane_extractor.build_ego_lane(waypoint)
        ego_dict = self.get_ego_vehicle(waypoint, lane_dict)
        vehicle_dict = self.get_vehicles(map, world.get_actors().filter('vehicle.*'), lane_dict)
        ped_dict = self.get_pedestrians(map, world.get_actors().filter('walker.*'), lane_dict)

        # Extract traffic lights
        if self.lane_extractor._correct_lane and self.traffic_light_detection: 
            # Only get traffic lights that are affecting the waypoint of the ego vehicle
            traffic_lights = world.get_traffic_lights_from_waypoint(waypoint, 50)
            light_dict = self.get_traffic_lights(waypoint, traffic_lights, lane_dict)
        else:
            light_dict = defaultdict()

        # Extract signs and miscellaneous objects
        sign_dict = self.get_signs(waypoint, world.get_actors().filter('traffic.traffic_sign'), lane_dict)
        object_dict = self.get_objects(map, world.get_actors().filter('static.prop.streetbarrier'), lane_dict)

        # Add to framedict
        self.framedict[timestamp.frame]={"ego": ego_dict,"actors": vehicle_dict,"pedestrians": ped_dict,"trafficlights": light_dict,"signs": sign_dict, "objects": object_dict, "lanes": lane_dict}
        
        # Increase recording count by 1
        self.frame_count += 1

        # Export data
        self.export_data()
        return self.frame_count >= self.max_count

    def export_data(self):
        with open(self.output_dir / 'semantics.json', 'w') as file:
            file.write(json.dumps(self.framedict))
