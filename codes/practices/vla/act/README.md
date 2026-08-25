# LeRobot ACT：ALOHA Transfer Cube

这个示例使用 LeRobot 0.6.1，在 ALOHA 双臂仿真 `Transfer Cube` 的人类示教数据上训练 ACT（Action Chunking with Transformers）。代码刻意保留了一个可读的 PyTorch 训练循环，方便观察 LeRobot 如何把数据特征、未来动作窗口、ACT 和预处理器连接起来。

默认数据集是 [`lerobot/aloha_sim_transfer_cube_human`](https://huggingface.co/datasets/lerobot/aloha_sim_transfer_cube_human)，包含 50 个 episode、20,000 帧、一路顶视 RGB、14 维双臂状态和 14 维动作，采样频率为 50 Hz。

## 环境准备

进入当前目录后使用 `uv` 创建 Python 3.12 环境：

```bash
cd codes/practices/vla/act
uv sync
```

首次运行会从 Hugging Face 下载数据集。完整视频数据需要数百 MB 磁盘空间，之后会复用本地缓存。

macOS 上 PyAV 与 OpenCV 可能同时加载 FFmpeg，从而打印 `AVFFrameReceiver is implemented in both ...` 警告；本机冒烟测试中不影响训练和仿真。若出现实际视频解码崩溃，优先改用 Linux/CUDA 环境。

## 冒烟测试

只读取第 0 个 episode，训练两个 step，先验证下载、视频解码、前向传播和 checkpoint 保存是否正常：

```bash
uv run python train_act.py \
  --episodes 0 \
  --steps 2 \
  --batch-size 2 \
  --device auto
```

默认 checkpoint 写入 `outputs/act_aloha_transfer`，包含：

- `model.safetensors`：ACT 参数。
- `config.json`：ACT 结构、动作 chunk 和输入输出特征。
- `policy_preprocessor.json`：图像、状态和动作归一化流程。
- `policy_postprocessor.json`：推理动作的反归一化流程。

随后可以用一个缩短到 5 帧的回合检查 checkpoint 加载、MuJoCo 环境和视频输出：

```bash
uv run lerobot-eval \
  --policy.path=outputs/act_aloha_transfer \
  --env.type=aloha \
  --env.task=AlohaTransferCube-v0 \
  --env.episode_length=5 \
  --eval.n_episodes=1 \
  --eval.batch_size=1 \
  --output_dir=outputs/eval_smoke
```

两个训练 step 不足以让策略学会任务，因此这里预期成功率为 0；这个命令只验证整条仿真链路。

## 正式训练

下面的参数更接近完整实验；训练时间取决于 GPU：

```bash
uv run python train_act.py \
  --steps 100000 \
  --batch-size 8 \
  --chunk-size 100 \
  --device cuda \
  --log-every 100
```

Apple Silicon 可以使用 `--device mps`。CPU 也能运行，但不适合完整训练。

代码默认启用 CVAE，使用 `--no-vae` 可以完成消融实验：

```bash
uv run python train_act.py \
  --steps 100000 \
  --batch-size 8 \
  --no-vae \
  --output-dir outputs/act_aloha_transfer_no_vae
```

## 仿真评估

训练结束后，用完整的 400 帧回合评估本地 checkpoint：

```bash
uv run lerobot-eval \
  --policy.path=outputs/act_aloha_transfer \
  --env.type=aloha \
  --env.task=AlohaTransferCube-v0 \
  --eval.n_episodes=20 \
  --eval.batch_size=1 \
  --output_dir=outputs/eval_act_aloha_transfer
```

Linux 无显示服务器时，可先设置 `MUJOCO_GL=egl`。评估成功标准是右臂拿起红色方块并将其交给左臂，环境最大 reward 为 4。

> LeRobot Hub 上的 `lerobot/act_aloha_sim_transfer_cube_human` 创建于旧版 processor API。LeRobot 0.6.1 直接加载它会提示 `ProcessorMigrationError`，需要先运行官方 processor migration；本示例因此默认评估自己保存的新格式 checkpoint。

## 代码流程

`train_act.py` 依次执行：

1. 使用 `LeRobotDatasetMetadata` 读取相机、状态、动作和归一化统计。
2. 将数据特征自动转换成 ACT 的 `input_features` 与 `output_features`。
3. 根据 `chunk_size` 构造未来动作的 `delta_timestamps`；默认一次监督未来 100 帧，也就是 2 秒动作。
4. 使用 LeRobot preprocessor 完成图像格式处理、批处理、归一化和设备搬运。
5. 优化 ACT 的动作重构损失与 KL 损失，并保存模型及配套处理器。

为了保持示例紧凑，这里没有实现断点续训、混合精度、定期评估、分布式训练和 W&B。需要这些能力时，应使用官方 `lerobot-train` CLI。
