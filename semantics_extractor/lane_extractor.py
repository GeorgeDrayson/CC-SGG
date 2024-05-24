from collections import defaultdict
import numpy as np
import math

class LaneExtractor():

    def __init__(self):
        self.road_naming_conventions = {i[0]:i[1] for i in [['Sidewalk','pavement'],['Driving','lane'],['Shoulder', 'shoulder']]}
        self._correct_lane = True #used to keep track of whether ego is in incoming or outgoing lane
        self._previous_lane_waypoint = None

    def build_dict_lane_single(self, lane_waypoint,preface=""):
        return {
            'lane_id': lane_waypoint.lane_id,
            'road_id': lane_waypoint.road_id, 
            'right_lane_marking_type': lane_waypoint.right_lane_marking.type.name, 
            'left_lane_marking_type': lane_waypoint.left_lane_marking.type.name,
            'category': self.road_naming_conventions[lane_waypoint.lane_type.name],
            'name': preface + self.road_naming_conventions[lane_waypoint.lane_type.name],
            'lane_change': lane_waypoint.lane_change.name,
            'is_junction': lane_waypoint.is_junction,
        }
    
    def build_dict_lane(self, lane_waypoint, preface):
        lane_dict = defaultdict()
        if lane_waypoint.lane_type.name in ['Sidewalk','Shoulder']: preface = preface + 'lane ' 
        lane_name = preface + self.road_naming_conventions[lane_waypoint.lane_type.name]
        lane_dict[lane_name]  = [self.build_dict_lane_single(lane_waypoint,preface)]
        return lane_dict
    
    def build_lanes(self, original_lane, prefaces, direction="left"):
        direction = 1 if direction=="left" else -1
        lanes = []
        cur_lane = original_lane
        while True:
            lane = cur_lane.get_left_lane() if direction == 1 else cur_lane.get_right_lane()
            if lane is None: break #break loop if there are no more lanes
            if cur_lane.lane_id * lane.lane_id < 0: direction *= -1  #switch the direction if changing to opposite lane
            # set preface based on the side of the road relative to the original lane
            preface = prefaces[1] if (lane.lane_id * original_lane.lane_id) < 0 else prefaces[0]
            if lane.lane_type.name != 'NONE': lanes.append(self.build_dict_lane(lane,preface))
            cur_lane = lane
        return lanes
    
    def build_ego_lane(self, lane_waypoint):
        prefaces = ['Outgoing ','Incoming ']  if self._correct_lane else  ['Incoming ','Outgoing ']
        ego_lane = [self.build_dict_lane(lane_waypoint, prefaces[0])]
        left_lanes = self.build_lanes(lane_waypoint, prefaces)[::-1]
        right_lanes = self.build_lanes(lane_waypoint, prefaces, direction="right")
        return left_lanes + ego_lane + right_lanes

    def wrong_lane_test(self, waypoint, max_angle=100):    
        if self._previous_lane_waypoint != None:
            if self._previous_lane_waypoint.is_junction: return True

            previous_lane_direction = self._previous_lane_waypoint.transform.get_forward_vector()
            current_lane_direction = waypoint.transform.get_forward_vector()

            p_lane_vector = np.array([previous_lane_direction.x, previous_lane_direction.y])
            c_lane_vector = np.array([current_lane_direction.x, current_lane_direction.y])

            waypoint_angle = math.degrees(
                math.acos(np.clip(np.dot(p_lane_vector, c_lane_vector) /
                                (np.linalg.norm(p_lane_vector) * np.linalg.norm(c_lane_vector)), -1.0, 1.0)))

            if waypoint_angle > max_angle: self._correct_lane = not self._correct_lane
        self._previous_lane_waypoint = waypoint
