import math
import itertools
import math
from util import Node

class EdgeExtractor:
    def __init__(self, config,extract_shoulders,extract_incoming_lanes):
        self._conf = config
        self.extract_shoulders = extract_shoulders
        self.extract_incoming_lanes = extract_incoming_lanes
        self.edge_extraction_settings = config.edge_extraction_settings
        self.node_categories = self._conf.node_extraction_settings["NODE_CATEGORIES"]
        self.node_colours = self._conf.node_extraction_settings["NODE_COLOURS"]
        self.edge_categories = self.edge_extraction_settings["EDGE_CATEGORIES"]
        self.edge_colours = self.edge_extraction_settings["EDGE_COLOURS"]
        self._unsafe_distance = 7
    
#~~~~~~~~~PUBLIC FUNCTIONS~~~~~~~~~~~~

    def get_config(self):
        return self._conf
    
    def get_binary_relation(self, edge_category, edge_value):
        return self.edge_extraction_settings[edge_category]["binary_relations"][edge_value]
    
    def extract_lanes(self, scene_graph, lane_list, edge_category="isIn"):
        for lane, name in itertools.chain.from_iterable(((lane, name) for name in lane) for lane in lane_list):
            attr = lane[name][0]
            if attr['category'] != 'shoulder' or self.extract_shoulders:
                if attr['name'][:8] != 'Incoming' or self.extract_incoming_lanes or attr['category'] == 'shoulder':
                    n = Node(name + '_' + str(abs(attr['lane_id'])),attr,attr['category'])
                    scene_graph.lanes.append(n)
                    scene_graph.add_node(n)
                    scene_graph.add_relation([n, edge_category, scene_graph.road_node, edge_category, self.get_binary_relation(edge_category,edge_category)])

    def extract_relations(self, scene_graph):
        for actor1, actor2 in itertools.combinations(scene_graph.g.nodes, 2):
            scene_graph.add_relations(self.extract_pairwise_relations(actor1, actor2))
        for actor in scene_graph.g.nodes:
            scene_graph.add_relations(self.extract_lane_relation(scene_graph, actor))
            scene_graph.add_relations(self.extract_self_relations(actor))

    def extract_pairwise_relations(self, actor1, actor2):
        direction = None
        relations_list = []
        if actor2.label in self.edge_extraction_settings["relativePosition"]["relation_pairs"][actor1.label]:
            relation = self.extract_directional_relation(actor1, actor2, edge_category="relativePosition")
            if relation: direction = relation[0][1]
            relations_list += relation
        if actor1.label in self.edge_extraction_settings["relativePosition"]["relation_pairs"][actor2.label]:
            relation = self.extract_directional_relation(actor2, actor1, edge_category="relativePosition")
            if relation: direction = relation[0][1]
            relations_list += relation
            actor1, actor2 = actor2, actor1
        if actor2.label in self.edge_extraction_settings["safeDistance"]["relation_pairs"][actor1.label]:
            relations_list += self.extract_distance_relation(actor1, actor2, direction, edge_category="safeDistance")
        return relations_list
    
    def extract_lane_relation(self, scene_graph, object_node, edge_category="isIn"):
        for node in scene_graph.lanes:
            if node.label in self.edge_extraction_settings[edge_category]["relation_pairs"][object_node.label]:
                if node.name == object_node.attr["lane_name"] + "_" + str(abs(object_node.attr["lane_id"])):
                    return [[object_node, edge_category, node, edge_category, self.get_binary_relation(edge_category,edge_category)]]
        return []

    def extract_self_relations(self, actor):
        relations_list = []
        if actor.label in self.edge_extraction_settings['velocity']['node_categories']:
            relations_list += self.extract_velocity_relation(actor, edge_category='velocity')
        if actor.label in self.edge_extraction_settings['location']['node_categories']:
            relations_list += self.extract_location_relation(actor, edge_category='location')
        if actor.label in self.edge_extraction_settings['braking']['node_categories']:
            relations_list += self.extract_brake_relation(actor, edge_category='braking')
        if actor.label in self.edge_extraction_settings['trafficLightState']['node_categories']:
            relations_list += self.extract_traffic_light_relation(actor, edge_category='trafficLightState')
        return relations_list
    
#~~~~~~~~~SELF RELATIONS~~~~~~~~~~~~
    
    def extract_brake_relation(self, actor,edge_category):
        braking_state = "Braking" if actor.attr['brake_light_on'] else "notBraking"
        return [[actor, braking_state, actor, edge_category, self.get_binary_relation(edge_category,braking_state)]]
    
    def extract_velocity_relation(self, actor,edge_category):
        velocity = [actor.attr['velocity'][0], actor.attr['velocity'][1]]
        return [[actor, velocity, actor, edge_category, velocity]]
    
    def extract_location_relation(self, actor, edge_category):
        location = [actor.attr['location'][0],actor.attr['location'][1]]
        return [[actor, location, actor, edge_category, location]]

    def extract_traffic_light_relation(self,actor,edge_category):
        light_state = "is" + actor.attr['state']
        return [[actor, light_state, actor, edge_category, self.get_binary_relation(edge_category,light_state)]]
    
#~~~~~~~~~PAIR RELATIONS~~~~~~~~~~~~

    def extract_distance_relation(self, actor1, actor2, direction, edge_category):
        if direction == 'inFrontOf':
            return self.create_proximity_relations(actor2, actor1, edge_category)
        if direction == 'atRearOf' and actor1.label in ['car','ego_car']:
            return self.create_proximity_relations(actor1, actor2, edge_category)
        if actor2.label == 'light':
            return self.create_proximity_relations(actor1, actor2, edge_category)
        return []
    
    def extract_directional_relation(self, actor1, actor2, edge_category):
        # Gives directional relations between actors based on their 2D absolute positions
        x1, y1 = actor1.attr['location'][0] - actor2.attr['location'][0], actor1.attr['location'][1] - actor2.attr['location'][1]
        degree =  math.degrees(math.atan2(y1, x1)) - actor2.attr['rotation'][0]
        degree = (degree % 360 + 360) % 360
             
        for direction_rel in self.edge_extraction_settings[edge_category]["relation_thresholds"]:
            list_of_ranges = direction_rel[1]
            for ranges in list_of_ranges:
                if degree >= ranges[0] and degree <= ranges[1]:
                    return [[actor1, direction_rel[0], actor2, edge_category, self.get_binary_relation(edge_category,direction_rel[0])]]          
        return []
    
#~~~~~~~~~~~~~~~~~~UTILITY FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~
    def create_proximity_relations(self, actor1, actor2, edge_category):
        stopping_distance = 0.01533*(self.get_velocity_mph(actor1)**2) - 0.1333
        if self.euclidean_distance(actor1, actor2) <= stopping_distance:
            edge_value="unsafeDistance"
        elif self.euclidean_distance(actor1, actor2) <= self._unsafe_distance and actor2.attr['name'] != "Traffic Light":
            edge_value="unsafeDistance"
        else:
            edge_value="safeDistance"
        return [[actor1, edge_value, actor2, edge_category, self.get_binary_relation(edge_category,edge_value)]]

    def euclidean_distance(self, actor1, actor2):
        l1 = actor1.attr['location']
        l2 = actor2.attr['location']
        return math.sqrt((l1[0] - l2[0])**2 + (l1[1]- l2[1])**2 + (l1[2] - l2[2])**2)

    def get_velocity_mph(self, actor):
        velocity = (actor.attr['velocity'][0]**2 + actor.attr['velocity'][1]**2)**(1/2)
        # Convert to mph
        velocity = round(2.23693629 * velocity)
        return velocity