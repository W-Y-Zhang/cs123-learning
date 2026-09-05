import numpy as np


"""
mathematic process

1. Forward kinematics (FK) for a 3-DOF planar manipulator:
    Given joint angles θ1, θ2, θ3 and link lengths L1, L2, L3, the end-effector position (x, y)
    and the theta2 is known, the wrist point is x',y'.

    x' = L1 * cos(θ1) + L2 * cos(θ1 + θ2)
    y' = L1 * sin(θ1) + L2 * sin(θ1 + θ2)

2. cos(θ1 + θ2) = cos(θ1) * cos(θ2) - sin(θ1) * sin(θ2)

3. Inverse kinematics (IK) for a 3-DOF planar manipulator:
   x' = (L1+L2*cos(θ2))*cos(θ1) - L2*sin(θ2)*sin(θ1)
   y' = (L1+L2*cos(θ2))*sin(θ1) + L2*sin(θ2)*cos(θ1)
   A = L1 + L2*cos(θ2)
   B = L2*sin(θ2)
   x' = A*cos(θ1) - B*sin(θ1)
   y' = A*sin(θ1) + B*cos(θ1)

4. regard (A,B) as an vector, and use the angle phi
    phi = atan2(B,A) = atan2(L2*sin(θ2),L1+L2cosθ2)
    A = sqrt(A**2 + B**2)cos(phi), B = sqrt(A**2 + B**2)sin(phi)
    x' = sqrt(A**2 + B**2)(cos(phi)cos(θ1)-sin(phi)sin(θ1)) = sqrt(A**2 + B**2)cos(θ1+phi)
    y' = sqrt(A**2 + B**2)sin(θ1+phi)

5. solve the θ1
    atan2(y',x') = θ1 + phi
    θ1 = atan2(y',x') - phi = atan2(y',x') - atan2(B,A) = atan2(L2*sin(θ2),L1+L2cosθ2)
"""
def ik_analytic_planar(xy,phi,L=(0.3, 0.25, 0.15),elbow_up = True): 
    # elbow can be up or down
    X,Y = xy
    L1, L2, L3 = L
    xp = X - L3*np.cos(phi)
    yp = Y - L3*np.sin(phi)
    r2 = xp**2 + yp**2
    cos_t2 = (r2 - L1 **2 - L2 **2)/(2*L1*L2)
    if abs(cos_t2) > 1:
        return None
    if elbow_up:
        t2 = np.arccos(cos_t2)
    else:
        t2 = -np.arccos(cos_t2)
    t1 = np.arctan2(yp,xp) - np.arctan2(L2*np.sin(t2),L1+L2*np.cos(t2))
    t3 = phi - t2 - t1

    return np.array([t1, t2, t3])

def ik_dls(fk_fn, jac_fn, theta0, p_target,
           lam=0.05, step=0.3, tol=1e-4, max_iter=200):
    # Start from the initial joint angles; copy to avoid mutating caller's theta0.
    theta = theta0.copy()
    
    for k in range(max_iter):
        # Forward kinematics: current end-effector pose given current theta.
        p = fk_fn(theta)
        
        # End-effector error: how far we are from the target.
        e = p_target - p
        if np.linalg.norm(e) < tol:
            return theta, k
        
        # Jacobian maps small joint changes (dtheta) to small end-effector displacements (dp).
        J = jac_fn(theta)                          # (3, n) or (6, n)
        
        # DLS update: J^T (J J^T + lambda^2 I)^(-1) e
        # lambda^2 I is the damping term, preventing ill-conditioning near singularities.
        JJt = J @ J.T
        dtheta = J.T @ np.linalg.solve(
            JJt + (lam ** 2) * np.eye(JJt.shape[0]), e)
        
        # step is the outer step size, preventing overshoot or oscillation from too-large updates.
        theta = theta + step * dtheta
    
    return theta, max_iter                         