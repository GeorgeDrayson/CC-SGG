import torch
import networkx as nx

class CornerCase:

    def __init__(self, y_pred, poss_edge_idx, poss_edge_values, extended_scene_graph):
        self.poss_edge_idx = poss_edge_idx
        self.poss_edge_values = poss_edge_values
        self.cc_sg = self.create_cc_from_kg(extended_scene_graph, y_pred)

    def create_cc_from_kg(self, extended_sg, y_pred):
        cc_sg = extended_sg.sg.copy()

        for node1, node2, edge in extended_sg.sg.edges(keys=True):
            column = torch.tensor([node1, node2])
            index = torch.where(torch.all(self.poss_edge_idx == column.reshape(-1, 1), dim=0))

            prediction = round(y_pred[index[0][edge]].item(),3)
            if prediction >= 0.3:
                nx.set_edge_attributes(cc_sg, {(node1, node2, edge): {'label': self.poss_edge_values[index[0][edge]]}})
            else:
                cc_sg.remove_edge(node1,node2,edge)
        return cc_sg
    
    def extract_neighbor_info(self,category, node, lane_top):
        #create a new entry in the cc_information dict
        info = {}
        info['category'] = category
        info['safeDistance'] = True
        info['laneId'] = []

        #find the neighbors of the node
        neighbors = self.cc_sg[node]

        #loop through the neighbors
        for neighbor_node, edge in neighbors.items():
            #loop through the relations
            for _, relation_dict in edge.items():
                relation = relation_dict['label']
                if relation == 'isIn':
                    info['laneId'].append(lane_top[neighbor_node-1])
                elif relation == 'unsafeDistance' or relation == 'safeDistance':
                    info['safeDistance'] = (relation == 'safeDistance')
                else:
                    info['orientation'] = relation
        return info
            
    
    def extract_corner_case_information(self, x_list, lane_topology, start_location):
        cc_information = {}
        lane_index = 0
        # get ego info
        for node in self.cc_sg.nodes():
            # get node category
            category = x_list[node]

            if category == 'ego_car':
                cc_information[category] = self.extract_neighbor_info(category, node, lane_topology)

                #if there are multiple options for the ego lane, assume it stays in the same lane as the original sg
                lanes = cc_information[category]['laneId']
                if len(lanes) > 1:
                    for n in range(len(lanes)):
                        if lanes[n] == start_location[category]['laneId']:
                            lane_index = n
                            cc_information[category]['laneId'] = [cc_information[category]['laneId'][lane_index]]

        # get info of other vehicles
        for node in self.cc_sg.nodes():
            # get node category
            category = x_list[node]
            key = category + str(node)

            # if it is a dynamic vehicle
            if category in ['car','bicycle','pedestrian','object']:
                cc_information[key] = self.extract_neighbor_info(category, node, lane_topology)
                if len(cc_information[key]['laneId']) > 1:
                    cc_information[key]['laneId'] = [cc_information[key]['laneId'][lane_index]]

        return cc_information