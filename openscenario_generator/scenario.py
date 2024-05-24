from scenariogeneration import xosc, ScenarioGenerator
import numpy as np

#TODO add humans to vehicle catalog
#TODO add braking at the end
#TODO fine tune scenario
#TODO scale to two vehicles

class Scenario(ScenarioGenerator):
    def __init__(self, start_location, corner_case, town="Town01", offset=150):
        super().__init__()
        self.open_scenario_version = 0
        self.start_location = start_location
        self.corner_case = corner_case
        self.town = town
        self.road_users = []
        self.offset = offset
        self.adv_offset = {True: 10, False: 1.5}#used to be 20, 10

    def scenario(self):
        ### create catalogs
        catalog = xosc.Catalog()
        catalog.add_catalog("VehicleCatalog", "../../scenarios/catalogs/vehicles")
        catalog.add_catalog("EnvironmentCatalog", "../../scenarios/catalogs/environments")
        catalog.add_catalog("MiscObjectCatalog", "../../scenarios/catalogs/objects")
    
        ### create road
        road = xosc.RoadNetwork(
            roadfile=self.town, scenegraph=""
        )
        if self.town=="Town01":
            road_id = '4'
            rotation=0.0
        else:
            road_id = '36'
            rotation=4.7

        ### define variables
        egoname = "hero"
        vehicle_catalog = {"car": "vehicle.tesla.model3_adversary", "bicycle": "vehicle.diamondback.century", "pedestrian": "vehicle.diamondback.century"}

        ### create parameters
        paramdec = xosc.ParameterDeclarations()
        paramdec.add_parameter(xosc.Parameter("roadid", xosc.ParameterType.double, road_id))


        entities = xosc.Entities()
        init = xosc.Init()

        # Ego Vehicle

        ## add parameters
        paramdec.add_parameter(xosc.Parameter("xvalue", xosc.ParameterType.double, str(self.start_location['ego_car']['location'][0])))
        paramdec.add_parameter(xosc.Parameter("yvalue", xosc.ParameterType.double, str(self.start_location['ego_car']['location'][1])))
        paramdec.add_parameter(xosc.Parameter("laneIdEgo", xosc.ParameterType.double, str(self.corner_case['ego_car']['laneId'][0])))
        paramdec.add_parameter(xosc.Parameter("offsetego", xosc.ParameterType.double, str(self.offset)))

        ## add entity
        entities.add_scenario_object(
            egoname, xosc.CatalogReference("VehicleCatalog", "vehicle.tesla.model3_ego")
        )

        init.add_init_action(egoname, xosc.TeleportAction(xosc.WorldPosition('$xvalue', '$yvalue', 0, rotation)))

        #add environment
        init.add_global_action(xosc.EnvironmentAction(xosc.CatalogReference("EnvironmentCatalog","Environment1")))

        ## create ego controller
        controller_property = xosc.Properties()
        controller_property.add_property(name="module", value="external_control")
        assign_controller_action = xosc.AssignControllerAction(xosc.Controller("HeroAgent",controller_property))

        override_controller_action = xosc.OverrideControllerValueAction()
        override_controller_action.set_throttle(active="false",value=0)
        override_controller_action.set_brake(active="false",value=0)
        override_controller_action.set_clutch(active="false",value=0)
        override_controller_action.set_parkingbrake(active="false",value=0)
        override_controller_action.set_steeringwheel(active="false",value=0)
        override_controller_action.set_gear(active="false",value=0)

        init.add_init_action(
            egoname, 
            xosc.ControllerAction(
                assignControllerAction=assign_controller_action,
                overrideControllerValueAction=override_controller_action
            )
        )

        for key in self.corner_case:
            if key != 'ego_car':
                paramdec.add_parameter(xosc.Parameter(str("laneId"+ key), xosc.ParameterType.double, str(self.start_location[key]['laneId'])))
                paramdec.add_parameter(xosc.Parameter(str("offset"+key), xosc.ParameterType.double, str(self.offset + self.adv_offset[self.corner_case[key]['safeDistance']])))

            if self.corner_case[key]['category'] in ['car', 'bicycle', 'pedestrian']:

                self.road_users.append(key)
                paramdec.add_parameter(xosc.Parameter(str("xvalue" + key), xosc.ParameterType.double, str(self.start_location[key]['location'][0])))
                paramdec.add_parameter(xosc.Parameter(str("yvalue" + key), xosc.ParameterType.double, str(self.start_location[key]['location'][1])))

                if self.corner_case[key]['category'] in ['bicycle','pedestrian']:
                    orientation = 1.8
                    if self.start_location[key]['location'][1] > self.start_location['ego_car']['location'][1]:
                        orientation *= -1
                elif np.sign(self.start_location[key]['laneId']) == 1:
                    orientation = 3.14
                else:
                    orientation = 0.0
                paramdec.add_parameter(xosc.Parameter(str("orientation"+ key), xosc.ParameterType.double, str(orientation+rotation)))

                #start proximity for synchronous action
                start_proximity = {"car":"50.0", "bicycle": "15.0", "pedestrian": "15.0"}
                paramdec.add_parameter(xosc.Parameter(str("startProximity"+ key), xosc.ParameterType.double, start_proximity[self.corner_case[key]['category']]))

                ## define init actions
                entities.add_scenario_object(
                key, xosc.CatalogReference("VehicleCatalog", vehicle_catalog[self.corner_case[key]['category']])
                )

                ## define init actions
                init.add_init_action(key, xosc.TeleportAction(xosc.WorldPosition(str('$xvalue'+key), str('$yvalue'+key), 0, str('$orientation'+key))))

                init.add_init_action(
                    key,
                    xosc.AbsoluteSpeedAction(
                        0.1,
                        xosc.TransitionDynamics(
                            xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0.0
                        ),
                    ),
                )

                if self.corner_case[key]['category'] in ['bicycle','pedestrian']:
                    adv_controller_property = xosc.Properties()
                    adv_controller_property.add_property(name="module", value="vehicle_longitudinal_control")
                    adv_assign_controller_action = xosc.AssignControllerAction(xosc.Controller("AdversaryAgent",adv_controller_property), activateLateral=True, activateLongitudinal=True)

                    init.add_init_action(
                        key, 
                        xosc.ControllerAction(
                            assignControllerAction=adv_assign_controller_action,
                            overrideControllerValueAction=override_controller_action
                        )
                    )

            if self.corner_case[key]['category'] in ['object']:
                print(key)
                entities.add_scenario_object(
                    key, xosc.CatalogReference("MiscObjectCatalog", "Barrier1")
                )
                init.add_init_action(key, xosc.TeleportAction(xosc.WorldPosition(str(self.start_location['ego_car']['location'][0]+30), '$yvalue', 0, 0)))


        ## create the story
        story = xosc.Story("mystory")

        ### create synchronize event
        for user in self.road_users:

            tar_man = xosc.Maneuver("target_man")

            #if the vehicle is in the same lane as the ego then use routing action as opposed to synchronized route
            if self.start_location[key]['laneId'] == self.start_location['ego_car']['laneId']:

                speed_event = xosc.Event("speed_event", xosc.Priority.overwrite)

                speed_action = xosc.AbsoluteSpeedAction(
                        5,
                        xosc.TransitionDynamics(
                            xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 1.0
                        ),
                )

                speed_event.add_trigger(
                    xosc.EntityTrigger(
                        "ego_start",
                        0,
                        xosc.ConditionEdge.rising,
                        xosc.RelativeDistanceCondition(str('$startProximity'+user), xosc.Rule.lessThan,xosc.RelativeDistanceType.longitudinal,user),
                        egoname
                    )
                )

                speed_event.add_action("speed_action", speed_action)
                tar_man.add_event(speed_event)

                tar_action = xosc.AcquirePositionAction(
                    xosc.LanePosition(str('$offset'+user), 0, str('$laneId'+user), '$roadid')
                )

                tar_event = xosc.Event("target_event", xosc.Priority.overwrite)
                tar_event.add_trigger(
                        xosc.ValueTrigger(
                            "AfterSynchronization",
                            0,
                            xosc.ConditionEdge.rising,
                            xosc.StoryboardElementStateCondition(xosc.StoryboardElementType.action,"speed_action",xosc.StoryboardElementState.endTransition)
                        )
                    )

                tar_event.add_action("tar_action", tar_action)
                tar_man.add_event(tar_event)

            else:

                tar_action = xosc.SynchronizeAction(
                    egoname,
                    xosc.LanePosition('$offsetego', 0, '$laneIdEgo', '$roadid'),
                    xosc.LanePosition(str('$offset'+user), 0, str('$laneId'+user), '$roadid'),
                    final_speed=xosc.AbsoluteSpeed(
                        10
                    ),
                )

                tar_event = xosc.Event("target_event", xosc.Priority.overwrite)
                tar_event.add_trigger(
                    xosc.EntityTrigger(
                        "ego_start",
                        0,
                        xosc.ConditionEdge.rising,
                        xosc.RelativeDistanceCondition(str('$startProximity'+user), xosc.Rule.lessThan,xosc.RelativeDistanceType.longitudinal,user),
                        egoname
                    )
                )

                tar_event.add_action("tar_action", tar_action)
                tar_man.add_event(tar_event)

            start_lane = self.start_location[user]['laneId']
            end_lane = self.corner_case[user]['laneId'][0]
            num_lanes = end_lane - start_lane

            current_action = 'tar_action'

            if num_lanes != 0:

                lane_change_event = xosc.Event("lane_change_event", xosc.Priority.overwrite)

                lane_change_event.add_trigger(
                        xosc.ValueTrigger(
                            "AfterSynchronization",
                            0,
                            xosc.ConditionEdge.rising,
                            xosc.StoryboardElementStateCondition(xosc.StoryboardElementType.action,"tar_action",xosc.StoryboardElementState.endTransition)
                        )
                    )

                lane_change_event.add_action(
                    "lane_change_action",
                    xosc.RelativeLaneChangeAction(
                        num_lanes,
                        user,
                        xosc.TransitionDynamics(
                            xosc.DynamicsShapes.linear, xosc.DynamicsDimension.distance, 5
                        ),
                    ),
                )

                current_action = 'lane_change_action'

                tar_man.add_event(lane_change_event)

            stop_event = xosc.Event("stop_event", xosc.Priority.overwrite)

            stop_event.add_trigger(
                xosc.ValueTrigger(
                    "AfterSynchronization",
                    0,
                    xosc.ConditionEdge.rising,
                    xosc.StoryboardElementStateCondition(xosc.StoryboardElementType.action,current_action,xosc.StoryboardElementState.endTransition)
                )
            )

            stop_event.add_action(
                "stop_event",
                xosc.AbsoluteSpeedAction(
                    0.0,
                    xosc.TransitionDynamics(
                        xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 10
                    ),
                ),
            )

            tar_man.add_event(stop_event)

            tar_man_gr = xosc.ManeuverGroup("target_man_gr")
            tar_man_gr.add_maneuver(tar_man)
            tar_man_gr.add_actor(user)

            ## act
            act = xosc.Act(
                "myact",
                xosc.ValueTrigger(
                    "start",
                    0,
                    xosc.ConditionEdge.none,
                    xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan),
                ),
            )

            act.add_maneuver_group(tar_man_gr)
            story.add_act(act)

        ## create the storyboard
        sb = xosc.StoryBoard(
            init,
            xosc.ValueTrigger(
                "stop_simulation",
                0,
                xosc.ConditionEdge.rising,
                xosc.SimulationTimeCondition(100, xosc.Rule.greaterThan),
                "stop",
            ),
        )
        sb.add_story(story)

        ## create the scenario
        sce = xosc.Scenario(
            "adapt_speed_example",
            "Mandolin",
            paramdec,
            entities=entities,
            storyboard=sb,
            roadnetwork=road,
            catalog=catalog,
            osc_minor_version=self.open_scenario_version,
        )

        return sce