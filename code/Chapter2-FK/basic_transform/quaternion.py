"""
Quaternion module for FK.

Provides quaternion-based utilities for computing forward kinematics (FK)
of a serial manipulator: converting joint angles to end-effector pose by
composing per-joint rotations as quaternions.
"""

import numpy as np
from scipy.spatial.transform import Rotation as R

def quaternion(axis,angle):
    """Build a quaternion (w, x, y, z) from an axis-angle rotation.

    Parameters:
        axis: 3-element rotation axis (need not be pre-normalized).
        angle_deg: rotation angle in degrees.
    """

    axis = np.array(axis,dtype=np.float64)
    axis = axis/np.linalg.norm(axis)
    angle = np.deg2rad(angle)
    half_angle = angle/2.0
    w = np.cos(half_angle)
    xyz = axis*np.sin(half_angle)

    return np.array([w, xyz[0], xyz[1], xyz[2]])


def quat_normalized(q_xyz):
    """
    Normalizes a quaternion to unit length.
    """
    return q_xyz / np.linalg.norm(q_xyz)


print(quaternion([0,0,1],90))
print(R.from_euler('z', 90, degrees=True).as_quat())
print(quat_normalized(quaternion([0,0,1],90)))

r1 = R.from_euler('z', 90, degrees=True)
r2 = R.from_euler('y', 90, degrees=True)
combined = r1 * r2
print(combined.as_quat())