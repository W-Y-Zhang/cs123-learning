
## 环境准备

用 [uv](https://docs.astral.sh/uv/) 管理依赖。在本目录下执行：

```bash
uv sync
```

`uv sync` 会按 `.python-version` 自动准备 Python 3.12，创建 `.venv` 并安装 `pyproject.toml` 里锁定的依赖（mujoco、gymnasium、matplotlib、pillow）。

之后用 `uv run` 执行脚本，无需手动激活环境：

```bash
uv run python xxx.py
```

macOS 上跑交互式 viewer 必须用 `mjpython`，Linux / Windows 用 `python` 即可：

```bash
uv run mjpython xxx.py
```

## 运行指南

所有命令都在 `cs123` 目录下执行。

### 1.pid-control

单摆 PD 位置控制，杆摆到目标角并稳住（交互窗口）：

```bash
uv run python 1.pid-control/pd_single_joint.py
# MacOS 上开窗口必须用 mjpython，Linux / Windows 换成 python
# uv run mjpython 1.pid-control/pd_single_joint.py
```

离屏渲染单摆 PD 响应，导出 GIF：

```bash
uv run python 1.pid-control/render_pd_single_joint_gif.py
```

### 2.forward-kinematics

手写 NumPy 正运动学与 MuJoCo 对拍，打印最大误差：

```bash
uv run python 2.forward-kinematics/fk_numpy_mujoco_check.py
```

### 3.inverse-kinematics

DLS 数值 IK 跟踪三角轨迹，打印跟踪误差：

```bash
uv run python 3.inverse-kinematics/ik_dls_triangle.py
```

交互查看 DLS 收敛过程，看末端实时追目标：

```bash
uv run python 3.inverse-kinematics/viewer_dls_convergence.py
# MacOS 上开窗口必须用 mjpython，Linux / Windows 换成 python
# uv run mjpython 3.inverse-kinematics/viewer_dls_convergence.py
```

离屏渲染 DLS 收敛过程，导出 GIF：

```bash
uv run python 3.inverse-kinematics/render_dls_convergence_gif.py
```

### 4.quadruped-mjcf

静态查看固定基座模型，机器人不动：

```bash
uv run python 4.quadruped-mjcf/run_view_pupper_fixed.py
# MacOS 上开窗口必须用 mjpython，Linux / Windows 换成 python
# uv run mjpython 4.quadruped-mjcf/run_view_pupper_fixed.py
```

浮动基座自由落地，位置伺服把腿拉回 home（纯观察，不打印）：

```bash
uv run python 4.quadruped-mjcf/run_view_pupper.py
# MacOS 上开窗口必须用 mjpython，Linux / Windows 换成 python 
# uv run mjpython 4.quadruped-mjcf/run_view_pupper.py
```

同上，但站姿锁到可改的 STAND_POSE，关窗打印稳定性判据（std<5mm 算站稳）：

```bash
uv run python 4.quadruped-mjcf/run_stand_pupper.py
# MacOS 上开窗口必须用 mjpython，Linux / Windows 换成 python
# uv run mjpython 4.quadruped-mjcf/run_stand_pupper.py
```

PD 调参对比扫描，出 CSV / 图 / GIF（无窗口）：

```bash
uv run python 4.quadruped-mjcf/run_gain_sweep.py
```

### 5.gait-control

渲染原地踏步 / 前进 trot 两段 GIF：

```bash
uv run python 5.gait-control/render_gait_experiment_gifs.py
```
