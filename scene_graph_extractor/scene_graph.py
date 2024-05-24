import matplotlib
matplotlib.use("Tkagg")
import networkx as nx
from util import Node

class SceneGraph:
    def __init__(self, edge_extractor, framedict= None):
        self.edge_extractor = edge_extractor
        self.g = nx.MultiDiGraph()
        self.lanes = []
        self.extract_scene_graph(framedict)

    def get_actor_type(self, label):
        actors = self.edge_extractor.node_categories
        for actor in range(len(actors)):
            if label == actors[actor] or label.lower() == actors[actor]:
                return actors[actor]
            elif f"{self.edge_extractor.node_categories[actor].upper()}_NAMES" in self.edge_extractor.get_config().edge_extraction_settings:
                for actor_names in self.edge_extractor.get_config().edge_extraction_settings[f"{actors[actor].upper()}_NAMES"]:
                    if actor_names in label:
                        return actors[actor]
                    elif actor_names in label.lower():
                        return actors[actor]
        raise NameError("Actor name not found for actor with name: " + label)

    def add_relation(self, relation):
        if relation != []:
            node1, edge, node2, edge_type, value = relation
            if node1 in self.g.nodes and node2 in self.g.nodes:
                self.g.add_edge(node1,node2,category=edge_type, label=edge,color=self.edge_extractor.edge_colours[edge_type], value=value)
            else:
                print(node1.name, node1 in self.g.nodes)
                print(node2.name, node2 in self.g.nodes)
                raise NameError("One or both nodes in relation do not exist in graph. Relation: " + str(node1.name) + str(edge) + str(node2.name))

    def add_relations(self, relations_list):
        for relation in relations_list:
            self.add_relation(relation)

    def add_node(self, node):
        self.g.add_node(node, attr=node.attr, label=node.name, value=node.label, style='filled', fillcolor=self.edge_extractor.node_colours[node.label] )

    def add_actor(self,attr,actor_id=None,name=None, label=None):
        n = Node(None, attr, None)
        n.label =  self.get_actor_type(attr['name']) if label==None else label
        n.name = n.label.lower() + "_" + actor_id if name==None else name
        self.add_node(n)

    def add_actors(self, actordict):
        for actor_id, attr in actordict.items():
            if attr['lane_name'] is not None: self.add_actor(attr,actor_id)

    def extract_scene_graph(self, framedict):
        # Add the road as the root node
        self.road_node = Node("Root Road", {"name":"Root Road"}, "road")
        self.add_node(self.road_node)

        # Add the ego vehicle
        self.edge_extractor.extract_lanes(self, framedict['lanes'])
        self.add_actor(name='ego car',attr=framedict['ego'], label='ego_car', )

        # Add all actors
        for key, attrs in framedict.items():   
            if key in ['actors','signs', 'trafficlights', 'pedestrians','objects']:
                self.add_actors(attrs)
            
        # Extract relations
        self.edge_extractor.extract_relations(self)