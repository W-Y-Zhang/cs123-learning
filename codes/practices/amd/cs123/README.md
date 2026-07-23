
# CS123 四足机器人 · AMD Linux 版

本目录是 `codes/practices/quadruped/cs123` 的 AMD Linux 独立副本，目标机器为：

- Ubuntu 24.04 / x86_64
- AMD Ryzen AI 9 HX 370
- AMD Radeon 890M

MuJoCo 物理仿真主要使用 CPU；有桌面图形会话时，交互 viewer 和离屏渲染由
Linux 图形栈使用 Radeon。强化学习依赖固定为官方 CPU 版 PyTorch，避免原锁
文件在 Linux 上安装 CUDA 13 和 `nvidia-*` 运行库。

当前系统的 ROCm 设备节点 `/dev/kfd` 不可用，因此本版本优先保证 CPU 路径
稳定可复现，不启用 PyTorch ROCm。以后修复系统 ROCm 环境时，可另建专用虚拟
环境尝试 GPU 训练，无需改动 MuJoCo 控制代码。

## 环境准备

用 [uv](https://docs.astral.sh/uv/) 管理依赖。在本目录下执行：

```bash
uv sync --frozen
```

`uv sync --frozen` 会按 `.python-version` 使用 Python 3.12，创建 `.venv` 并安装
`pyproject.toml` 里锁定的依赖（MuJoCo、Gymnasium、CPU PyTorch、
Matplotlib、Pillow）。

之后用 `uv run` 执行脚本，无需手动激活环境：

```bash
uv run python xxx.py
```

AMD Linux 上的交互式 viewer 直接使用 `python`：

```bash
uv run python xxx.py
```

安装后可确认没有启用 CUDA/NVIDIA 后端：

```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

当前锁定环境应输出 `2.13.0+cpu False`。还可以确认两个锁文件没有
NVIDIA/CUDA 包：

```bash
rg -i 'nvidia|cuda-(bindings|pathfinder|toolkit)' uv.lock exercises/uv.lock
```

该命令没有输出即为正常。

## 本机验证

根目录的运动学、RL、短训练和离屏渲染测试：

```bash
uv run python 2.forward-kinematics/fk_numpy_mujoco_check.py
uv run python 3.inverse-kinematics/ik_dls_triangle.py
uv run pytest -q 6.rl_pupper/tests
```

`exercises` 使用独立环境；各 Lab 的测试文件都叫 `tests.py`，需要分开运行，
避免 pytest 模块名冲突：

```bash
cd exercises
uv sync --frozen
bash shared/rl/fetch_policies.sh

for suite in \
  lab_1_pid_bode/tests.py \
  lab_2_fk_teleop/tests.py \
  lab_3_stepping/tests.py \
  lab_4_urdf_surgery/tests.py \
  lab_6_rl_pupper/tests.py \
  lab_7_llm_control/tests.py \
  lab_8_ball_chase/tests.py
do
  uv run pytest -q "$suite"
done

PYTHONPATH=. uv run pytest -q shared/kinematics/test_leg_kinematics.py
PYTHONPATH=. uv run pytest -q shared/rl/test_obs_helpers.py
```

## 运行指南

所有命令都在 `cs123` 目录下执行。

### 1.pid-control

单摆 PD 位置控制，杆摆到目标角并稳住（交互窗口）：

```bash
uv run python 1.pid-control/pd_single_joint.py
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
```

离屏渲染 DLS 收敛过程，导出 GIF：

```bash
uv run python 3.inverse-kinematics/render_dls_convergence_gif.py
```

### 4.quadruped-mjcf

静态查看固定基座模型，机器人不动：

```bash
uv run python 4.quadruped-mjcf/run_view_pupper_fixed.py
```

浮动基座自由落地，位置伺服把腿拉回 home（纯观察，不打印）：

```bash
uv run python 4.quadruped-mjcf/run_view_pupper.py
```

同上，但站姿锁到可改的 STAND_POSE，关窗打印稳定性判据（std<5mm 算站稳）：

```bash
uv run python 4.quadruped-mjcf/run_stand_pupper.py
```

PD 调参对比扫描，出 CSV / 图 / GIF（无窗口）：

```bash
uv run python 4.quadruped-mjcf/run_gain_sweep.py
```

### 5.gait-control

渲染原地 / 前进步态 GIF（默认 trot，可选 walk / pace / bound / gallop）：

```bash
uv run python 5.gait-control/run_gait_control.py
uv run python 5.gait-control/run_gait_control.py --gait walk
uv run python 5.gait-control/run_gait_control.py --gait pace
uv run python 5.gait-control/run_gait_control.py --gait bound
uv run python 5.gait-control/run_gait_control.py --gait gallop
```

在 MuJoCo 中交互预览：

```bash
uv run python 5.gait-control/run_gait_control.py --gait walk --viewer inplace
uv run python 5.gait-control/run_gait_control.py --gait pace --viewer forward
uv run python 5.gait-control/run_gait_control.py --gait gallop --viewer forward
```

### 6.rl_pupper

运行环境和奖励函数冒烟测试：

```bash
uv run pytest -q 6.rl_pupper/tests
uv run python 6.rl_pupper/pupper_env.py
```

训练 PPO 速度跟踪策略，先用短训练确认流程：

```bash
uv run python 6.rl_pupper/train.py --timesteps 100000 --n-envs 4
```

加载 checkpoint，生成命令演示 GIF 和速度跟踪图：

```bash
uv run python 6.rl_pupper/evaluate.py
```

训练参数和控制设计见 [`6.rl_pupper/README.md`](6.rl_pupper/README.md)。
