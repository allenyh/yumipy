"""
Motion planner for the YuMi
Author: Jeff Mahler
"""
import IPython
import logging
import numpy as np
try:
    import geometry_msgs
    from geometry_msgs.msg import PoseStamped
    import moveit_commander
    import moveit_msgs
    import rospy
except ImportError:
    logging.error("Unable to load ROS! Will not be able to use client-side motion planner!")

from autolab_core import RigidTransform
from yumi_state import YuMiState
from yumi_trajectory import YuMiTrajectory
from yumi_constants import YuMiConstants as ymc

class YuMiMotionPlanner:
    """ Client-side motion planner for the ABB YuMi, based on MoveIt!
    """
    
    def __init__(self, arm='left', planner='RRTConnect',
                 goal_pos_tol=0.001,
                 planning_time=0.1,
                 eef_delta=0.01,
                 jump_thresh=0.0):
        self._arm = 'right_arm'
        if arm.lower() == 'left':
            self._arm = 'left_arm'
        self._goal_pos_tol = goal_pos_tol
        self._planning_time = planning_time

        self._init_planning_interface()
        self._update_collision_object()
        self._update_planning_params()
        self.set_planner(planner)

    def _init_planning_interface(self):
        """ Initializes the MoveIn planning interface """
        self._robot_comm = moveit_commander.RobotCommander()
        self.scene = moveit_commander.PlanningSceneInterface()
        self._planning_group = moveit_commander.MoveGroupCommander(self._arm)
        self._planning_group.set_pose_reference_frame(ymc.MOVEIT_PLANNING_REFERENCE_FRAME)

    def _update_collision_object(self):
        rospy.sleep(2)
        rospy.loginfo("Update "+self._arm+" Collision Objects")
        # table
        self.scene.remove_world_object("table")
        table_name = "table"
        table_pose = PoseStamped()
        table_pose.header.frame_id = self._robot_comm.get_planning_frame()
        table_pose.pose.orientation.w = 1.0
        table_pose.pose.position.x = 0.3
        table_pose.pose.position.z = -0.02
        self.scene.add_box(table_name, table_pose, size=(0.6, 1.5, 0.02))
        # camera shelf
        self.scene.remove_world_object("camera_shelf")
        shelf_name = "camera_shelf"
        shelf_pose = PoseStamped()
        shelf_pose.header.frame_id = self._robot_comm.get_planning_frame()
        shelf_pose.pose.orientation.w = 1.0
        shelf_pose.pose.position.z = 0.62
        self.scene.add_box(shelf_name, shelf_pose, size=(0.75, 0.1, 0.05))
        # camera shelf left support
        self.scene.remove_world_object("left_support")
        left_support_name = "left_support"
        left_support_pose = PoseStamped()
        left_support_pose.header.frame_id = self._robot_comm.get_planning_frame()
        left_support_pose.pose.orientation.z = 0.3826834
        left_support_pose.pose.orientation.w = 0.9238795
        left_support_pose.pose.position.x = -0.21
        left_support_pose.pose.position.y = -0.12
        left_support_pose.pose.position.z = 0.62
        self.scene.add_box(left_support_name, left_support_pose, size=(0.28, 0.04, 0.04))
        # camera shelf right support
        self.scene.remove_world_object("right_support")
        right_support_name = "right_support"
        right_support_pose = PoseStamped()
        right_support_pose.header.frame_id = self._robot_comm.get_planning_frame()
        right_support_pose.pose.orientation.z = -0.3826834
        right_support_pose.pose.orientation.w = 0.9238795
        right_support_pose.pose.position.x = -0.21
        right_support_pose.pose.position.y = 0.12
        right_support_pose.pose.position.z = 0.62
        self.scene.add_box(right_support_name, right_support_pose, size=(0.28, 0.04, 0.04))
        # camera
        self.scene.remove_world_object("camera")
        camera_name = "camera"
        camera_pose = PoseStamped()
        camera_pose.header.frame_id = self._robot_comm.get_planning_frame()
        camera_pose.pose.orientation.w = 1.0
        camera_pose.pose.position.x = 0.343
        camera_pose.pose.position.z = 0.575
        self.scene.add_box(camera_name, camera_pose, size=(0.06, 0.2, 0.03))
        # barcode detector
        self.scene.remove_world_object("barcode_detector")
        detector_name = "barcode_detector"
        detector_pose = PoseStamped()
        detector_pose.header.frame_id = self._robot_comm.get_planning_frame()
        detector_pose.pose.orientation.w = 1.0
        detector_pose.pose.position.x = 0.47
        detector_pose.pose.position.z = 0.62
        self.scene.add_box(detector_name, detector_pose, size=(0.18, 0.08, 0.12))
        # screen and teach box
        self.scene.remove_world_object("screen_and_box")
        sab_name = "screen_and_box"
        sab_pose = PoseStamped()
        sab_pose.header.frame_id = self._robot_comm.get_planning_frame()
        sab_pose.pose.orientation.w = 1.0
        sab_pose.pose.position.x = 0.3
        sab_pose.pose.position.y = -0.48
        sab_pose.pose.position.z = 0.35
        self.scene.add_box(sab_name, sab_pose, size=(0.6, 0.01, 0.7))

    def _update_planning_params(self):
        """ Updates the parameters of the planner """
        self._planning_group.set_goal_position_tolerance(self._goal_pos_tol)
        self._planning_group.set_planning_time(self._planning_time)

    def set_planner(self, planner):
        """ Sets the motion planner for the YuMi """
        if planner not in ymc.MOVEIT_PLANNER_IDS.keys():
            raise ValueError('Planner %s not supported' %(planner))
        self._planner_id = ymc.MOVEIT_PLANNER_IDS[planner]
        self._planning_group.set_planner_id(self._planner_id)
        
    @property
    def goal_position_tolerance(self):
        return self._goal_pos_tol

    @property
    def planning_time(self):
        return self._planning_time

    @property
    def planner(self):
        return self._planner

    @property
    def planner(self):
        return self._planner

    @goal_position_tolerance.setter
    def goal_position_tolerance(self, tol):
        self._goal_pos_tol = tol
        self._update_planning_params()

    @planning_time.setter
    def planning_time(self, planning_time):
        self._planning_time = planning_time
        self._update_planning_params()

    @planner.setter
    def planner(self, planner):
        self.set_planner(planner)

    def plan_linear_path(self, start_state, start_pose, goal_pose,
                         traj_len=10, eef_delta=0.01, jump_thresh=0.0):
        """
        Plans a linear trajectory between the start and goal pose from the initial joint configuration. The poses should be specified in the frame of reference of the end effector tip. Start state must correspond to the start pose - right now this is up to the user.
        
        Parameters
        ----------
        start_state : YuMiState
            initial state of the arm
        start_pose : RigidTransform
            initial pose of end effector tip
        goal_pose : RigidTransform
            goal pose of end effector tip
        traj_len : int
            number of waypoints to use in planning
        eef_delta : float
            distance for interpolation of the final planner path in cartesian space
        jump_thresh : float
            the threshold for jumping between poses 

        Returns
        -------
        traj : YuMiTrajectory
            the planned trajectory to execute
        """
        # check valid state types
        if not isinstance(start_state, YuMiState):
            raise ValueError('Start state must be specified')

        # check valid pose types
        if not isinstance(start_pose, RigidTransform) or not isinstance(goal_pose, RigidTransform):
            raise ValueError('Start and goal poses must be specified as RigidTransformations')
        # check valid frames
        if start_pose.from_frame != 'tool' or goal_pose.from_frame != 'tool' or (start_pose.to_frame != 'world' and start_pose.to_frame != 'base') or (goal_pose.to_frame != 'world' and goal_pose.to_frame != 'base'):
            raise ValueError('Start and goal poses must be from frame \'tool\' to frame \{\'world\', \'base\'\}')
            
        # set start state of planner
        start_state_msg = moveit_msgs.msg.RobotState()
        start_state_msg.joint_state.name = ['yumi_joint_%d_r' %i for i in range(1,8)]
        if self._arm == 'left_arm':
            start_state_msg.joint_state.name = ['yumi_joint_%d_l' %i for i in range(1,8)]
        start_state_msg.joint_state.position = start_state.in_radians
        self._planning_group.set_start_state(start_state_msg)

        # convert start and end pose to the planner's reference frame
        start_pose_hand = start_pose * ymc.T_GRIPPER_HAND
        goal_pose_hand = goal_pose * ymc.T_GRIPPER_HAND

        # get waypoints
        pose_traj = start_pose_hand.linear_trajectory_to(goal_pose_hand, traj_len)
        waypoints = [t.pose_msg for t in pose_traj]
        print(waypoints)

        # plan plath
        plan, fraction = self._planning_group.compute_cartesian_path(waypoints, eef_delta, jump_thresh)
        print(plan)
        if fraction >= 0.0 and fraction < 1.0:
            logging.warning('Failed to plan full path.')
            return None
        if fraction < 0.0:
            logging.warning('Error while planning path.')
            return None

        # convert from moveit joint traj in radians
        joint_names = plan.joint_trajectory.joint_names
        joint_traj = []
        for t in plan.joint_trajectory.points:
            joints_and_names = zip(joint_names, t.positions)
            joints_and_names.sort(key = lambda x: x[0])
            joint_traj.append(YuMiState([np.rad2deg(x[1]) for x in joints_and_names]))

        return YuMiTrajectory(joint_traj)

    def plan_shortest_path(self, start_state, start_pose, goal_pose, timeout=0.1, tool='gripper'):
        """
        Plans the shortest path in joint space between the start and goal pose from the initial joint configuration. The poses should be specified in the frame of reference of the end effector tip. Start state must correspond to the start pose - right now this is up to the user.
        
        Parameters
        ----------
        start_state : YuMiState
            initial state of the arm
        start_pose : RigidTransform
            initial pose of end effector tip
        goal_pose : RigidTransform
            goal pose of end effector tip
        timeout : float
            planner timeout (shorthand for setting new planning time then planning)

        Returns
        -------
        traj : YuMiTrajectory
            the planned trajectory to execute
        """
        # check valid state types
        if not isinstance(start_state, YuMiState):
            raise ValueError('Start state must be specified')

        # check valid pose types
        if not isinstance(start_pose, RigidTransform) or not isinstance(goal_pose, RigidTransform):
            raise ValueError('Start and goal poses must be specified as RigidTransformations')

        # check valid frames
        if start_pose.from_frame != 'tool' or goal_pose.from_frame != 'tool' or (start_pose.to_frame != 'world' and start_pose.to_frame != 'base') or (goal_pose.to_frame != 'world' and goal_pose.to_frame != 'base'):
            raise ValueError('Start and goal poses must be from frame \'tool\' to frame \{\'world\', \'base\'\}')
            
        # set planning time
        self.planning_time = timeout

        # set start state of planner
        start_state_msg = moveit_msgs.msg.RobotState()
        start_state_msg.joint_state.name = ['yumi_joint_%d_r' %i for i in range(1,8)]
        if self._arm == 'left_arm':
            start_state_msg.joint_state.name = ['yumi_joint_%d_l' %i for i in range(1,8)]
        start_state_msg.joint_state.position = start_state.in_radians
        self._planning_group.set_start_state(start_state_msg)
     
        # convert start and end pose to the planner's reference frame
        start_pose_hand = start_pose * ymc.T_GRIPPER_HAND
        if tool == 'gripper':
            goal_pose_hand = goal_pose * ymc.T_GRIPPER_HAND
        elif tool == 'suction':
            goal_pose_hand = goal_pose * ymc.T_SUCTION_HAND

        # plan plath
        self._planning_group.set_pose_target(goal_pose_hand.pose_msg)
        plan = self._planning_group.plan()
        count = 0
        while count < 5 and len(plan.joint_trajectory.points) == 0:
            plan = self._planning_group.plan()
            count += 1

        if len(plan.joint_trajectory.points) == 0:
            logging.warning('Failed to plan path.')
            return None

        # convert from moveit joint traj in radians 
        joint_names = plan.joint_trajectory.joint_names
        joint_traj = []
        for t in plan.joint_trajectory.points:
        #t = plan.joint_trajectory.points[-1]
        #print("t:{}".format(t))
            joints_and_names = zip(joint_names, t.positions)
            joints_and_names.sort(key = lambda x: x[0])
            joint_traj.append(YuMiState([np.rad2deg(x[1]) for x in joints_and_names]))
        #print("joint_traj:{}".format(joint_traj))

        return YuMiTrajectory(joint_traj)
