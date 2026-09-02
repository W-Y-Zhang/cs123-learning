import numpy as np
from rotation_basics import rot_x, rot_z
from homo_transform import make_transform, transform_point, invert_transform, chain_transforms


#the camera extrinsic matrix is a 4x4 homogeneous transformation matrix 
#describes the position and orientation of the camera in the world coordinate system. It can be constructed from the rotation matrix and translation vector of the camera.
"""1. Construct the camera extrinsic matrix (camera to world)"""
tilt_angle = np.deg2rad(30)  
rot_ex= rot_x(tilt_angle)  # rotation matrix for tilt
t = np.array([1,0,0])
extrinsic = make_transform(rot_ex, t)
# print(extrinsic)

"""2. Transform a point from camera coordinates to world coordinates"""
point_in_camera = np.array([0, 0, 1])  # Point in camera coordinates
point_in_world = transform_point(extrinsic, point_in_camera)
print(point_in_world)

"""3. Transform a point from world coordinates to camera coordinates"""

T = invert_transform(extrinsic)
point_in_camera_new = transform_point(T, point_in_world)
print(point_in_camera_new)
print(np.array(point_in_camera))


"""4. camera - world - base"""

base_yaw = np.deg2rad(45)
rot_base = rot_z(base_yaw)
T_world_base = make_transform(rot_base, np.array([0, 1, 0]))

#T_base_camera = inv(T_world_base) * T_world_camera(extrinsic)

T_base_world = invert_transform(T_world_base)
T_base_camera = chain_transforms(extrinsic, T_base_world) #B@A

point_in_base = transform_point(T_base_camera, point_in_camera)
print(point_in_base)