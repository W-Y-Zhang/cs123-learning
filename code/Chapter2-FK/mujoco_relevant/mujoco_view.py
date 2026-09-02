import mujoco
import mujoco.viewer
import numpy as np

def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    T = np.eye(4)
    # The upper-left 3x3 block of the homogeneous matrix stores the rotation;
    # this is a 2D planar rotation about the z-axis.
    T[:3, :3] = [[c, -s, 0],
                 [s,  c, 0],
                 [0,  0, 1]]
    return T

def trans(x, y, z):
    T = np.eye(4)
    # The first three entries of the fourth column store the translation
    # vector, which is the position of the child coordinate frame's origin.
    T[:3, 3] = [x, y, z]
    return T

def fk_planar(thetas, L=(0.3, 0.25, 0.15)):
    t1, t2, t3 = thetas
    # Each group rot_z(theta_i) @ trans(L_i, 0, 0)
    # represents one link: first rotate about the joint, then move L_i along
    # the current link's x-axis.
    T = rot_z(t1) @ trans(L[0], 0, 0) \
        @ rot_z(t2) @ trans(L[1], 0, 0) \
        @ rot_z(t3) @ trans(L[2], 0, 0)
    return T     # Read the end-effector position from T[:3, 3] and its
                 # orientation from T[:3, :3].


model = mujoco.MjModel.from_xml_path('planar_3dof.xml')
data  = mujoco.MjData(model)
# The comparison below uses end_site's world coordinates, so first get its
# ID in the MuJoCo model.
end_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, 'end_site')
max_err = 0.0
for _ in range(100):
    # Randomly sample joint angles to cover different poses, rather than testing only the zero position.
    q = np.random.uniform(-np.pi, np.pi, size=3)
    data.qpos[:3] = q
    mujoco.mj_forward(model, data)           # MuJoCo's forward kinematic
    p_mj = data.site_xpos[end_id]            # The end_site world coordinates computed by MuJoCo

    p_ours = fk_planar(q)[:3, 3]             # The first three entries of the fourth column of our FK matrix

    max_err = max(max_err, np.linalg.norm(p_mj - p_ours))

print(f'max |p_ours - p_mj| = {max_err:.2e}')



with mujoco.viewer.launch_passive(model, data) as v:
    while v.is_running():
        # 假设我们在 Python 里用自己的 FK 算末端位置
        p = fk_planar(data.qpos[:3])[:3, 3]

        # 清空旧的调试几何再画
        v.user_scn.ngeom = 0
        mujoco.mjv_initGeom(
            v.user_scn.geoms[0],
            type=mujoco.mjtGeom.mjGEOM_SPHERE,
            size=[0.02, 0, 0], pos=p, mat=np.eye(3).flatten(),
            rgba=[1, 0.3, 0.3, 1],
        )
        v.user_scn.ngeom = 1

        mujoco.mj_step(model, data)
        v.sync()