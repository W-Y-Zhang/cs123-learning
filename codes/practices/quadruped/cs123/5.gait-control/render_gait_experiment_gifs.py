"""在真实 Pupper v3 上渲染 §5 的两个开环 trot 实验 GIF（本目录自包含）。

管线：`pupper_ik` 的数值 IK 把足端轨迹反解成关节角 → 写进真实模型自带的位置
伺服 → MjSpec 加的 base weld 把机身固定住 → 离屏渲染成 GIF。原地 trot 与前进
trot 只差 `step_length` 和是否平移焊接点。产物写到本目录 `outputs/`。

在 cs123 目录下运行：
    uv run python 5.gait-control/render_gait_experiment_gifs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pupper_ik import (  # noqa: E402
    HIP_OFFSETS,
    LEG_ORDER,
    WELD_RELPOSE_X,
    PupperLegIK,
    build_sim_model,
)


OUT_DIR = Path(__file__).with_name("outputs")

# trot：对角腿同相，两组错半个周期（FL+RR / FR+RL）。
PHASE_OFFSETS = {"FL": 0.0, "FR": 0.5, "RL": 0.5, "RR": 0.0}
DUTY = 0.5

WIDTH = 720
HEIGHT = 540
FPS = 24
SETTLE_SECONDS = 0.35
RENDER_SECONDS = 3.0


def leg_phase(t: float, leg: str, t_cycle: float, duty: float = DUTY) -> tuple[bool, float]:
    t_local = ((t / t_cycle) % 1.0 + PHASE_OFFSETS[leg]) % 1.0
    if t_local < duty:
        return True, t_local / duty
    return False, (t_local - duty) / (1.0 - duty)


def foot_trajectory(s: float, in_stance: bool, step_length: float, step_height: float, stand_height: float) -> np.ndarray:
    if in_stance:
        x = step_length * (0.5 - s)
        z = -stand_height
    else:
        x = step_length * (s - 0.5)
        z = -stand_height + step_height * np.sin(np.pi * s)
    return np.array((x, 0.0, z), dtype=float)


def gait_step(
    kin: PupperLegIK,
    t: float,
    step_length: float,
    seed: dict[str, np.ndarray],
    *,
    t_cycle: float,
    step_height: float,
    stand_height: float,
) -> dict[str, np.ndarray]:
    target = {}
    for leg in LEG_ORDER:
        in_stance, s = leg_phase(t, leg, t_cycle)
        foot_base = HIP_OFFSETS[leg] + foot_trajectory(s, in_stance, step_length, step_height, stand_height)
        q = kin.ik(foot_base, leg=leg, q_seed=seed[leg])
        seed[leg] = q
        target[leg] = q
    return target


def add_label(frame: np.ndarray, text: str) -> Image.Image:
    image = Image.fromarray(frame).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((18, 18, 470, 68), radius=10, fill=(255, 255, 255, 218))
    draw.text((34, 34), text, fill=(20, 30, 40, 255))
    return image


def make_camera() -> mujoco.MjvCamera:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.distance = 0.72
    camera.azimuth = 135.0
    camera.elevation = -18.0
    camera.lookat[:] = (0.0, 0.0, 0.10)
    return camera


def render_experiment(
    name: str,
    output: Path,
    *,
    step_length: float,
    t_cycle: float,
    step_height: float,
    stand_height: float,
    weld_speed: float = 0.0,
) -> None:
    kin = PupperLegIK()
    model = build_sim_model(stand_height=stand_height, weld=True)
    model.vis.global_.offwidth = max(model.vis.global_.offwidth, WIDTH)
    model.vis.global_.offheight = max(model.vis.global_.offheight, HEIGHT)
    data = mujoco.MjData(model)
    base_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")

    seed = {leg: np.zeros(3) for leg in LEG_ORDER}
    q0 = gait_step(kin, 0.0, step_length, seed, t_cycle=t_cycle, step_height=step_height, stand_height=stand_height)

    # 初始摆到站姿：base 在 stand_height，12 个关节按 q0。
    data.qpos[:] = 0.0
    data.qpos[2] = stand_height
    data.qpos[3] = 1.0
    for leg in LEG_ORDER:
        data.qpos[kin.qadr[leg]] = q0[leg]
    mujoco.mj_forward(model, data)

    renderer = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
    camera = make_camera()
    frames: list[Image.Image] = []
    next_frame_time = 0.0
    base_z: list[float] = []

    try:
        while data.time < SETTLE_SECONDS + RENDER_SECONDS:
            gait_t = max(0.0, data.time - SETTLE_SECONDS)
            if weld_speed and model.neq:
                model.eq_data[0, WELD_RELPOSE_X] = weld_speed * gait_t
            target = (
                q0
                if data.time < SETTLE_SECONDS
                else gait_step(kin, gait_t, step_length, seed, t_cycle=t_cycle, step_height=step_height, stand_height=stand_height)
            )
            for leg in LEG_ORDER:
                data.ctrl[kin.ctrl[leg]] = target[leg]
            mujoco.mj_step(model, data)

            if data.time < SETTLE_SECONDS:
                continue
            base_z.append(float(data.xpos[base_id][2]))

            render_t = data.time - SETTLE_SECONDS
            if render_t + 0.5 * model.opt.timestep < next_frame_time:
                continue
            camera.lookat[:] = data.xpos[base_id]
            camera.lookat[2] = max(float(camera.lookat[2]), 0.09)
            renderer.update_scene(data, camera=camera)
            frames.append(add_label(renderer.render(), name))
            next_frame_time += 1.0 / FPS
    finally:
        renderer.close()

    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0, optimize=True)
    std_mm = float(np.std(base_z[-int(round(1.0 / model.opt.timestep)):])) * 1000.0
    print(f"saved {output} ({len(frames)} frames, base z std={std_mm:.2f} mm)")


def main() -> None:
    render_experiment(
        name="In-place trot · pupper_v3.xml",
        output=OUT_DIR / "lab5_inplace_trot.gif",
        step_length=0.0,
        t_cycle=0.4,
        step_height=0.03,
        stand_height=0.13,
    )
    render_experiment(
        name="Forward trot · pupper_v3.xml",
        output=OUT_DIR / "lab5_forward_trot.gif",
        step_length=0.05,
        t_cycle=0.5,
        step_height=0.035,
        stand_height=0.13,
        weld_speed=0.10,
    )


if __name__ == "__main__":
    main()
