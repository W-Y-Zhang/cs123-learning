#!/usr/bin/env python3
"""A tiny online extrinsic-calibration game.

The game simulates one common calibration problem:

- A camera has an unknown yaw offset relative to the robot body.
- A target is observed at several distances.
- The yaw error creates a lateral residual that grows with distance.
- An online estimator updates the yaw estimate frame by frame.

Everything is synthetic and uses only the Python standard library, so it is safe
to run without private logs or robot hardware.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path


LEVELS = {
    "easy": {"true_yaw_deg": 1.2, "noise_cm": 1.0, "frames": 30},
    "normal": {"true_yaw_deg": 1.8, "noise_cm": 2.0, "frames": 45},
    "hard": {"true_yaw_deg": 2.6, "noise_cm": 4.0, "frames": 60},
}


@dataclass
class Frame:
    idx: int
    distance_m: float
    lateral_residual_m: float
    yaw_measurement_deg: float
    estimate_deg: float
    abs_error_deg: float
    mean_abs_residual_m: float
    triggered: bool
    accepted: bool


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def bar(value: float, scale: float = 0.05, width: int = 34) -> str:
    n = clamp(int(abs(value) / scale), 0, width)
    left = "<" * n if value < 0 else ""
    right = ">" * n if value > 0 else ""
    return f"{left:>{width}}|{right:<{width}}"


def simulate(
    true_yaw_deg: float,
    initial_guess_deg: float,
    update_gain: float,
    noise_cm: float,
    frames: int,
    seed: int,
) -> list[Frame]:
    rng = random.Random(seed)
    estimate_deg = initial_guess_deg
    residual_window: list[float] = []
    records: list[Frame] = []

    for idx in range(frames):
        distance_m = 2.0 + (idx % 9) * 0.75
        if idx % 13 == 0:
            distance_m = 1.5

        yaw_error_rad = math.radians(true_yaw_deg - estimate_deg)
        clean_residual = distance_m * math.tan(yaw_error_rad)
        noise_m = rng.gauss(0.0, noise_cm / 100.0)
        residual_m = clean_residual + noise_m

        yaw_measurement_deg = estimate_deg + math.degrees(math.atan2(residual_m, distance_m))
        residual_window.append(abs(residual_m))
        residual_window = residual_window[-6:]
        mean_abs_residual_m = sum(residual_window) / len(residual_window)

        has_excitation = distance_m >= 3.5
        residual_is_large = mean_abs_residual_m >= 0.05
        triggered = has_excitation and residual_is_large

        if triggered:
            step = update_gain * (yaw_measurement_deg - estimate_deg)
            estimate_deg += clamp(step, -0.35, 0.35)

        abs_error_deg = abs(true_yaw_deg - estimate_deg)
        accepted = abs_error_deg < 0.2 and mean_abs_residual_m < 0.045

        records.append(
            Frame(
                idx=idx,
                distance_m=distance_m,
                lateral_residual_m=residual_m,
                yaw_measurement_deg=yaw_measurement_deg,
                estimate_deg=estimate_deg,
                abs_error_deg=abs_error_deg,
                mean_abs_residual_m=mean_abs_residual_m,
                triggered=triggered,
                accepted=accepted,
            )
        )

    return records


def write_csv(records: list[Frame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "frame",
                "distance_m",
                "lateral_residual_m",
                "yaw_measurement_deg",
                "estimate_deg",
                "abs_error_deg",
                "mean_abs_residual_m",
                "triggered",
                "accepted",
            ],
        )
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "frame": r.idx,
                    "distance_m": f"{r.distance_m:.3f}",
                    "lateral_residual_m": f"{r.lateral_residual_m:.5f}",
                    "yaw_measurement_deg": f"{r.yaw_measurement_deg:.5f}",
                    "estimate_deg": f"{r.estimate_deg:.5f}",
                    "abs_error_deg": f"{r.abs_error_deg:.5f}",
                    "mean_abs_residual_m": f"{r.mean_abs_residual_m:.5f}",
                    "triggered": int(r.triggered),
                    "accepted": int(r.accepted),
                }
            )


def summarize(records: list[Frame], true_yaw_deg: float) -> dict[str, float | int | bool]:
    first = records[0]
    last = records[-1]
    initial_residual = first.mean_abs_residual_m
    final_residual = sum(r.mean_abs_residual_m for r in records[-6:]) / min(6, len(records))
    improvement = 1.0 - final_residual / max(initial_residual, 1e-6)
    convergence_frame = next((r.idx for r in records if r.accepted), -1)
    passed = last.abs_error_deg < 0.25 and improvement > 0.55 and convergence_frame >= 0
    return {
        "true_yaw_deg": true_yaw_deg,
        "final_estimate_deg": last.estimate_deg,
        "final_abs_error_deg": last.abs_error_deg,
        "residual_improvement": improvement,
        "convergence_frame": convergence_frame,
        "passed": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Play a synthetic online calibration game.")
    parser.add_argument("--level", choices=sorted(LEVELS), default="normal")
    parser.add_argument("--initial-guess-deg", type=float, default=0.0)
    parser.add_argument("--update-gain", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with code 1 when the regression checks fail.",
    )
    args = parser.parse_args()

    cfg = LEVELS[args.level]
    records = simulate(
        true_yaw_deg=cfg["true_yaw_deg"],
        initial_guess_deg=args.initial_guess_deg,
        update_gain=args.update_gain,
        noise_cm=cfg["noise_cm"],
        frames=cfg["frames"],
        seed=args.seed,
    )
    summary = summarize(records, true_yaw_deg=cfg["true_yaw_deg"])

    print("Online calibration game: estimate the hidden camera yaw offset")
    print(f"level={args.level} seed={args.seed} true_yaw={summary['true_yaw_deg']:.2f} deg")
    print()
    print(" frame  dist  residual       estimate  abs_err  event")
    for r in records[:: max(1, len(records) // 12)]:
        event = "ACCEPT" if r.accepted else ("UPDATE" if r.triggered else "watch")
        print(
            f"{r.idx:6d} {r.distance_m:5.2f}m {bar(r.lateral_residual_m)} "
            f"{r.estimate_deg:8.3f} {r.abs_error_deg:7.3f}  {event}"
        )

    print()
    print("Regression checks")
    print(f"- final estimate: {summary['final_estimate_deg']:.3f} deg")
    print(f"- final abs error: {summary['final_abs_error_deg']:.3f} deg")
    print(f"- residual improvement: {summary['residual_improvement'] * 100:.1f}%")
    print(f"- convergence frame: {summary['convergence_frame']}")
    print(f"- result: {'PASS' if summary['passed'] else 'FAIL'}")

    if args.csv:
        write_csv(records, args.csv)
        print(f"- csv: {args.csv}")

    if args.fail_on_regression and not summary["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
