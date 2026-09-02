import numpy as np


def rot_x(theta):
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s, c],
    ])

def rot_y(theta):

    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c],
    ])

def rot_z(theta):
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [c, -s, 0],
        [s, c, 0],
        [0, 0, 1],
    ])


# print(rot_x(np.deg2rad(45)))
# print(rot_y(np.deg2rad(45)))
# print(rot_z(np.deg2rad(45)))

def euler_to_rot(roll, pitch, yaw):
    """
    calculates the rotation matrix from roll, pitch, yaw angles (in radians) using the ZYX convention.
    """
    return rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)

