from collections import defaultdict

class Actor():
    def __init__(self, actor, lanedict, waypoint, dynamic=False, name=None):
        self.actor = actor
        self.attributes = self.get_static_attributes(lanedict,waypoint,name)
        if dynamic: self.get_dynamic_attributes()

    def get_actor_display_name(self, truncate=250):
        name = ' '.join(self.actor.type_id.replace('_', '.').title().split('.')[1:])
        return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name

    def get_actor_location(self, transform):
        l_3d = transform.location
        return int(l_3d.x), int(l_3d.y), int(l_3d.z)
    
    def get_brake_attribute(self):
        self.attributes['brake_light_on'] = True if (str(self.actor.get_light_state()) == 'Brake') else False
    
    def get_traffic_light_attribute(self):
        self.attributes['state'] = str(self.actor.get_state())
    
    def get_waypoint_attributes(self, wp, lanedict):
        lane_id = wp.lane_id
        road_id = wp.road_id
        lane_name = ""
        for idx, lane in enumerate(lanedict):
            for key, lane_list in lane.items():
                for lane_dict in lane_list:
                    if lane_dict['lane_id'] == lane_id and lane_dict['road_id'] == road_id:
                        '''
                        if lane_dict['category']=="shoulder":
                            #just put the actor on the lane
                            lane_name = lane_dict['name'][:-9]
                            lane_id -= 1
                        '''
                        lane_name = key
        return lane_id, road_id, lane_name

    def get_static_attributes(self, lanedict, wp=None, name=None):
        return_dict = defaultdict()
        t_3d = self.actor.get_transform()
        return_dict['location'] = self.get_actor_location(t_3d)
        return_dict['name'] = self.get_actor_display_name() if name==None else name
        if(wp): 
            return_dict['lane_id'], return_dict['road_id'], return_dict["lane_name"] = self.get_waypoint_attributes(wp, lanedict)
        return return_dict
    
    def get_dynamic_attributes(self):
        v_3d = self.actor.get_velocity()
        t_3d = self.actor.get_transform()
        r_3d = t_3d.rotation
        self.attributes['velocity'] = int(v_3d.x), int(v_3d.y), int(v_3d.z)
        self.attributes['rotation'] =  int(r_3d.yaw), int(r_3d.roll), int(r_3d.pitch)

    def get_attributes(self):
        return self.attributes