import numpy as np

import omnigibson as og
from omnigibson.macros import create_module_macros
from omnigibson.object_states.object_state_base import BooleanState, AbsoluteObjectState
from omnigibson.object_states.pose import Pose
from omnigibson.object_states.room_states import InsideRoomTypes
from omnigibson.utils.constants import MAX_INSTANCE_COUNT


# Create settings for this module
m = create_module_macros(module_path=__file__)

m.IN_REACH_DISTANCE_THRESHOLD = 2.0
m.IN_FOV_PIXEL_FRACTION_THRESHOLD = 0.05


def _get_robot(idn=0):
    """
    Grabs the requested @idn'th robot from the simulator

    Args:
        idn (int): Which robot (the idn'th) to grab from the simulator

    Returns:
        None or BaseRobot: If found, the @idn'th robot in the simulator
    """
    valid_robots = og.sim.scene.robots
    if len(valid_robots) <= idn:
        return None

    return valid_robots[idn]


class InReachOfRobot(AbsoluteObjectState, BooleanState):
    @staticmethod
    def get_dependencies():
        return AbsoluteObjectState.get_dependencies() + [Pose]

    def _get_value(self):
        robot = _get_robot()
        if not robot:
            return False

        robot_pos = robot.get_position()
        object_pos, _ = self.obj.states[Pose].get_value()
        return np.linalg.norm(object_pos - np.array(robot_pos)) < m.IN_REACH_DISTANCE_THRESHOLD

    def _set_value(self, new_value):
        raise NotImplementedError("InReachOfRobot state currently does not support setting.")


class InSameRoomAsRobot(AbsoluteObjectState, BooleanState):
    @staticmethod
    def get_dependencies():
        return AbsoluteObjectState.get_dependencies() + [Pose, InsideRoomTypes]

    def _get_value(self):
        robot = _get_robot()
        if not robot:
            return False

        scene = self._simulator.scene
        if not scene or not hasattr(scene, "get_room_instance_by_point"):
            return False

        robot_pos = robot.get_position()
        robot_room = scene.get_room_instance_by_point(np.array(robot_pos[:2]))
        object_rooms = self.obj.states[InsideRoomTypes].get_value()

        return robot_room is not None and robot_room in object_rooms

    def _set_value(self, new_value):
        raise NotImplementedError("InSameRoomAsRobot state currently does not support setting.")


class InHandOfRobot(AbsoluteObjectState, BooleanState):
    def _get_value(self):
        robot = _get_robot()
        if not robot:
            return False

        # We import this here to avoid cyclical dependency.
        from omnigibson.robots.manipulation_robot import IsGraspingState

        return any(
            robot.is_grasping(arm=arm, candidate_obj=bid) == IsGraspingState.TRUE
            for bid in self.obj.get_body_ids()
            for arm in robot.arm_names
        )

    def _set_value(self, new_value):
        raise NotImplementedError("InHandOfRobot state currently does not support setting.")


class InFOVOfRobot(AbsoluteObjectState, BooleanState):
    @staticmethod
    def get_optional_dependencies():
        return AbsoluteObjectState.get_optional_dependencies() + [ObjectsInFOVOfRobot]

    def _get_value(self):
        robot = _get_robot()
        if not robot:
            return False

        body_ids = set(self.obj.get_body_ids())
        return not body_ids.isdisjoint(robot.states[ObjectsInFOVOfRobot].get_value())

    def _set_value(self, new_value):
        raise NotImplementedError("InFOVOfRobot state currently does not support setting.")


class ObjectsInFOVOfRobot(AbsoluteObjectState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_value(self):
        # Pass the FOV through the instance-to-body ID mapping.
        seg = self._simulator.renderer.render_single_robot_camera(self.obj, modes="ins_seg")[0][:, :, 0]
        seg = np.round(seg * MAX_INSTANCE_COUNT).astype(int)
        body_ids = self._simulator.renderer.get_pb_ids_for_instance_ids(seg)

        # Pixels that don't contain an object are marked -1 but we don't want to include that
        # as a body ID.
        return set(np.unique(body_ids)) - {-1}

    def _set_value(self, new_value):
        raise NotImplementedError("ObjectsInFOVOfRobot state currently does not support setting.")
