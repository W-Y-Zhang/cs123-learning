---
title: 项目实战概述
sidebar_position: 1
---

# 项目实战：从仿真验证走向真机部署

项目实战统一归入 **AMD 专区、仿真实战、真机实战** 三个入口。你可以先在仿真中跑通算法和控制闭环，再进入真机部署；使用 AMD 平台的课程与实验则从专区直接进入。

## AMD 专区

- [AUP Learning Cloud 云算力](./amd/aup-learning-cloud)：在浏览器中使用 Ryzen AI APU、JupyterHub、Code Server 与 ROCm 环境，适合课程练习、端侧推理和小规模实验。
- [玩转 Pupper 四足机器人](./amd/pupper-control/intro)：AMD 专区旗舰项目，包含 **Pupper Locomotion｜强化学习运动策略**与 **Pupper VLA｜视觉-语言-动作智能**两个方向。

## 仿真实战

| 项目 | 技术主线 | 状态 |
| --- | --- | --- |
| [从零到一搭建四足机器人](./quadruped/cs123/intro) | MuJoCo、PD、运动学、PPO、LLM 控制 | 可用 |
| [MuJoCo 仿真入门](./robot-arm/mujoco-arm-pick-place) | MJCF、物理仿真、Python 控制 | 可用 |
| [DDPG InvertedPendulum](./robot-arm/ddpg-mujoco/invertedpendulum-v5) | 连续控制基础与 DDPG baseline | 可用 |
| [DDPG Reacher](./robot-arm/ddpg-mujoco/reacher-v5) | 二维机械臂目标追踪 | 可用 |
| [DDPG Pusher](./robot-arm/ddpg-mujoco/pusher-v5) | 机械臂接触操作与奖励设计 | 可用 |
| [ACT 双臂操作训练](./vla/act) | ALOHA、模仿学习、ACT、多回合评估 | 可用 |
| [两轮足 Flamingo · Isaac Lab](./wheel-legged/flamingo-isaaclab/preview) | PPO / CaT、Sim2Sim、鲁棒性验证 | 预告 |
| [Sim2Sim 验证](./quadruped/sim2sim/placeholder) | 跨仿真策略验证 | 施工中 |

## 真机实战

| 项目 | 技术主线 | 状态 |
| --- | --- | --- |
| [SO-101 + LeRobot 真机教程](./robot-arm/data-collection/so101-lerobot-real) | 硬件连通、安全测试、动作回放 | 可用 |
| [LeRobot 中文课程讲义](./robot-arm/data-collection/lerobot-course) | 数据集、机器人学习工具链、真机流程前置知识 | 可用 |
| [ROS2 机械臂控制](./robot-arm/ros2-arm-control/placeholder) | ROS2 控制链路与机械臂执行 | 施工中 |
| [Sim2Real 指南](./quadruped/sim2real-guide/placeholder) | 仿真策略部署与真机验证 | 施工中 |
