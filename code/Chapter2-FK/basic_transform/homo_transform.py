import numpy as np


def make_transform(R,t):
    """
    Constructs a homogeneous transformation matrix from a rotation matrix and translation vector.

    Parameters:
        R: 3x3 rotation matrix.
        t: 3-element translation vector.
    Returns:
        4x4 homogeneous transformation matrix.
    """
    T = np.eye(4)
    T[:3,:3] = R
    T[:3,3] = t
    return T

def transform_point(T, p):
    """
    Transforms a point using a homogeneous transformation matrix.

    Parameters:
        T: 4x4 homogeneous transformation matrix.
        p: 3-element point vector.
    Returns:
        Transformed 3-element point vector.
    """

    p_homogeneous = np.append(p, 1)  # Convert to homogeneous coordinates
    p_transformed = T @ p_homogeneous
    return p_transformed[:3]  # Return only the x, y, z components

def invert_transform(T):
    """
    Inverts a homogeneous transformation matrix.

    Parameters:
        T: 4x4 homogeneous transformation matrix.
    Returns:
        Inverted 4x4 homogeneous transformation matrix.
    """
    R = T[:3,:3]
    t = T[:3,3]
    R_inv = R.T
    t_inv = -R_inv @ t
    T_inv = np.eye(4)
    T_inv[:3,:3] = R_inv
    T_inv[:3,3] = t_inv
    return T_inv

def chain_transforms(*transforms):
    """
    Chains multiple homogeneous transformation matrices together.

    Parameters:
        *transforms: Variable number of 4x4 homogeneous transformation matrices.
    Returns:
        Chained 4x4 homogeneous transformation matrix.
    """
    T_chain = np.eye(4)
    for T in transforms:
        T_chain = T_chain @ T
    return T_chain

