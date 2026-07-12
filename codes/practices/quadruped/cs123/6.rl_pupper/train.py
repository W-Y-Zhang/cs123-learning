"""使用 Stable-Baselines3 PPO 训练 Pupper 速度跟踪策略。"""

from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv

from pupper_env import PupperEnv


LAB_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = LAB_DIR / "outputs"


def make_env(seed: int, rank: int):
    def _thunk():
        env = Monitor(PupperEnv())
        env.reset(seed=seed + rank)
        return env

    return _thunk


def train(
    timesteps: int,
    n_envs: int,
    seed: int,
    out: str,
    tensorboard: bool,
    checkpoint: str | None,
) -> Path:
    if checkpoint and not Path(checkpoint).exists():
        raise FileNotFoundError(f"checkpoint 不存在：{checkpoint}")

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    vec_env = SubprocVecEnv([make_env(seed, rank) for rank in range(n_envs)])
    try:
        tensorboard_log = str(out_dir / "tb") if tensorboard else None

        if checkpoint:
            print(f"从 checkpoint 继续训练：{checkpoint}")
            model = PPO.load(checkpoint, env=vec_env, tensorboard_log=tensorboard_log)
            model.set_random_seed(seed)
        else:
            model = PPO(
                "MlpPolicy",
                vec_env,
                n_steps=2048,
                batch_size=256,
                n_epochs=4,
                learning_rate=3e-4,
                gamma=0.97,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01,
                policy_kwargs={"net_arch": [256, 256]},
                tensorboard_log=tensorboard_log,
                verbose=1,
                seed=seed,
                device="auto",
            )

        checkpoint_callback = CheckpointCallback(
            save_freq=max(1_000_000 // n_envs, 1),
            save_path=str(out_dir),
            name_prefix="pupper_ppo",
        )
        model.learn(total_timesteps=timesteps, callback=checkpoint_callback)
        final_path = out_dir / "pupper_ppo.zip"
        model.save(str(final_path))
    finally:
        vec_env.close()

    return final_path


def main() -> None:
    parser = argparse.ArgumentParser(description="使用 PPO 训练 Pupper")
    parser.add_argument("--timesteps", type=int, default=20_000_000)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--tensorboard", action="store_true")
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()

    path = train(
        args.timesteps,
        args.n_envs,
        args.seed,
        args.out,
        args.tensorboard,
        args.checkpoint,
    )
    print(f"模型已保存：{path}")


if __name__ == "__main__":
    main()
