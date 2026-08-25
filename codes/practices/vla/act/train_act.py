"""使用 LeRobotDataset 在 ALOHA Transfer Cube 数据上训练 ACT。

这是教学用的最小训练循环。它展示 LeRobot 中数据特征、动作时间窗、ACT
配置、预处理器和 checkpoint 保存如何连接起来，不替代功能更完整的
``lerobot-train`` 命令。
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import torch
from lerobot.configs import FeatureType
from lerobot.datasets import LeRobotDataset, LeRobotDatasetMetadata
from lerobot.policies import make_pre_post_processors
from lerobot.policies.act import ACTConfig, ACTPolicy
from lerobot.utils.feature_utils import dataset_to_policy_features
from torch.utils.data import DataLoader

LAB_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_ID = "lerobot/aloha_sim_transfer_cube_human"
DEFAULT_OUTPUT_DIR = LAB_DIR / "outputs" / "act_aloha_transfer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用 LeRobot 的 ACT 实现在 ALOHA 仿真示教上训练策略。",
    )
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument(
        "--revision",
        default="v3.0",
        help="Hugging Face 数据集 revision；固定版本便于复现实验。",
    )
    parser.add_argument(
        "--episodes",
        nargs="*",
        type=int,
        default=None,
        help="只加载指定 episode，例如 --episodes 0 1；默认加载全部。",
    )
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--kl-weight", type=float, default=10.0)
    parser.add_argument(
        "--no-vae",
        action="store_true",
        help="关闭 ACT 的 CVAE，便于做消融实验。",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cuda", "mps", "cpu"),
        default="auto",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--max-grad-norm", type=float, default=10.0)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if args.steps < 1:
        parser.error("--steps 必须大于 0")
    if args.batch_size < 1:
        parser.error("--batch-size 必须大于 0")
    if args.num_workers < 0:
        parser.error("--num-workers 不能小于 0")
    if args.chunk_size < 1:
        parser.error("--chunk-size 必须大于 0")
    if args.log_every < 1:
        parser.error("--log-every 必须大于 0")
    if args.max_grad_norm <= 0:
        parser.error("--max-grad-norm 必须大于 0")
    if args.episodes is not None and any(index < 0 for index in args.episodes):
        parser.error("episode index 不能为负数")
    return args


def resolve_device(requested: str) -> torch.device:
    """解析训练设备，并在显式请求不可用设备时尽早报错。"""
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA 不可用；请改用 --device mps 或 --device cpu。")
    if requested == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS 不可用；请改用 --device cuda 或 --device cpu。")
    return torch.device(requested)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_delta_timestamps(indices: list[int] | None, fps: int) -> list[float]:
    """把离散帧偏移转换成 LeRobotDataset 使用的秒级偏移。"""
    if indices is None:
        return [0.0]
    return [index / fps for index in indices]


def split_policy_features(metadata: LeRobotDatasetMetadata):
    """从数据集元数据推导 ACT 的输入与输出特征。"""
    features = dataset_to_policy_features(metadata.features)
    output_features = {
        name: feature
        for name, feature in features.items()
        if feature.type is FeatureType.ACTION
    }
    input_features = {
        name: feature
        for name, feature in features.items()
        if name not in output_features
    }
    if not output_features:
        raise ValueError("数据集中没有 ACT 可监督的 action 特征。")
    return input_features, output_features


def train(args: argparse.Namespace) -> Path:
    set_seed(args.seed)
    device = resolve_device(args.device)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"dataset: {args.dataset_id}@{args.revision}")
    print(f"device:  {device}")
    print(f"output:  {output_dir}")

    metadata = LeRobotDatasetMetadata(
        args.dataset_id,
        revision=args.revision,
    )
    input_features, output_features = split_policy_features(metadata)

    config = ACTConfig(
        input_features=input_features,
        output_features=output_features,
        device=str(device),
        chunk_size=args.chunk_size,
        n_action_steps=args.chunk_size,
        use_vae=not args.no_vae,
        kl_weight=args.kl_weight,
        push_to_hub=False,
    )
    policy = ACTPolicy(config).to(device)
    preprocessor, postprocessor = make_pre_post_processors(
        config,
        dataset_stats=metadata.stats,
    )

    delta_timestamps = {
        "action": make_delta_timestamps(
            config.action_delta_indices,
            metadata.fps,
        ),
        **{
            name: make_delta_timestamps(
                config.observation_delta_indices,
                metadata.fps,
            )
            for name in config.image_features
        },
    }
    dataset = LeRobotDataset(
        args.dataset_id,
        episodes=args.episodes,
        delta_timestamps=delta_timestamps,
        revision=args.revision,
    )
    if len(dataset) < args.batch_size:
        raise ValueError(
            f"可用样本数 {len(dataset)} 小于 batch size {args.batch_size}；"
            "请减小 --batch-size 或加载更多 episode。",
        )

    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
        drop_last=True,
    )
    optimizer = config.get_optimizer_preset().build(policy.parameters())

    print(
        f"frames: {len(dataset)}, fps: {metadata.fps}, "
        f"chunk: {config.chunk_size}, vae: {config.use_vae}",
    )
    print(f"inputs:  {', '.join(input_features)}")
    print(f"outputs: {', '.join(output_features)}")

    policy.train()
    step = 0
    while step < args.steps:
        for batch in dataloader:
            optimizer.zero_grad(set_to_none=True)
            batch = preprocessor(batch)
            loss, loss_metrics = policy.forward(batch)
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(
                policy.parameters(),
                args.max_grad_norm,
            )
            optimizer.step()

            step += 1
            if step == 1 or step % args.log_every == 0 or step == args.steps:
                metric_text = ""
                if loss_metrics:
                    metric_text = " " + " ".join(
                        f"{name}={value:.4f}"
                        for name, value in loss_metrics.items()
                        if isinstance(value, (int, float))
                    )
                print(
                    f"step={step:>6d} loss={loss.item():.4f} "
                    f"grad_norm={float(grad_norm):.4f}{metric_text}",
                )

            if step >= args.steps:
                break

    policy.save_pretrained(output_dir)
    preprocessor.save_pretrained(output_dir)
    postprocessor.save_pretrained(output_dir)
    print(f"checkpoint 已保存到：{output_dir}")
    return output_dir


def main() -> None:
    train(parse_args())


if __name__ == "__main__":
    main()
