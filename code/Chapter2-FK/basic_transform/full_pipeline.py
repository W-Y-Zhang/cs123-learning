import numpy as np
from rotation_basics import rot_x, rot_z
from homo_transform import make_transform, transform_point, invert_transform, chain_transforms
from scipy.spatial.transform import Rotation as R

np.set_printoptions(suppress=True)

def pixel_to_cameara_point(u,v,depth,intrinsic):
    """
    Converts pixel coordinates to camera coordinates using the intrinsic matrix.

    Parameters:
        u: Pixel x-coordinate.
        v: Pixel y-coordinate.
        depth: Depth value at the pixel (distance from the camera).
        intrinsic: 3x3 camera intrinsic matrix.
    Returns:
        3-element point in camera coordinates.
    """
    fx, fy = intrinsic[0, 0], intrinsic[1, 1]
    cx, cy = intrinsic[0, 2], intrinsic[1, 2]
    x = (u - cx) *depth / fx
    y = (v - cy) *depth / fy
    z = depth

    return np.array([x, y, z])

def transform_pose(T, position_xyz, rotation_matrix):
    """
    Transforms a pose from one coordinate system to another.

    Parameters:
        T: 4x4 homogeneous transformation matrix.
        position_xyz: 3-element position vector.
        rotation_matrix: 3x3 rotation matrix.

    Returns:
        4x4 homogeneous transformation matrix representing the transformed pose.
    """
    # Create the homogeneous transformation matrix for the input pose
    pose = make_transform(rotation_matrix, position_xyz) #T_camera_grasp

    # Transform the pose using the provided transformation matrix 
    transformed_pose = chain_transforms(pose, T) #T_base_grasp = T_base_camera * T_camera_grasp

    return transformed_pose

"""1. pixel to camera coordinates"""
intrinsic = np.array([[800, 0, 320],
                        [0, 800, 240],
                        [0, 0, 1]])
u, v = 320, 240  # Pixel coordinates
depth = 2.0  # Depth value in meters
camera_point = pixel_to_cameara_point(u, v, depth, intrinsic)
print("Camera coordinates:", camera_point)

"""2. Transform a pose from camera coordinates to base coordinates"""
# Define the camera extrinsic matrix (camera to world)
tilt_angle = np.deg2rad(30)
rot_ex = rot_x(tilt_angle)  # rotation matrix for tilt
t = np.array([1, 0, 0])
extrinsic = make_transform(rot_ex, t)  # T_world_camera
#T_base_camera = T_base_world * T_world_camera
base_yaw = np.deg2rad(45)
rot_base = rot_z(base_yaw)
T_world_base = make_transform(rot_base, np.array([0, 1, 0]))  # T_world_base
T_base_world = invert_transform(T_world_base)  # T_base_world
T_base_camera = chain_transforms(extrinsic, T_base_world)  

point_in_camera = camera_point  # Position in camera coordinates
pose_rotation = R.from_euler('xyz', [0, 0, 0], degrees=True).as_matrix()  # Rotation in camera coordinates
pose= make_transform(pose_rotation, point_in_camera)  # Position in camera coordinates
grasp_base = T_base_camera @ pose
print("Transformed pose (base coordinates):", grasp_base)

"""3.transform grasp pose from base coordinates to world coordinates"""
#T_world_grasp = T_world_base * T_base_grasp
T_world_grasp = chain_transforms(grasp_base, T_world_base)
print("Transformed pose (world coordinates):", T_world_grasp)
#end_to_end T_world_grasp = T_world_camera * T_camera_grasp
T_world_grasp_e2e = extrinsic @ make_transform(pose_rotation, point_in_camera)
print("End-to-end T_world_grasp:", T_world_grasp_e2e)