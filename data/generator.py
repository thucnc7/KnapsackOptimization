"""Generate JSON benchmark instances for the 0/1 knapsack problem.

Key design decisions (v4 – Gaussian Mixture + Rejection Sampling):
  - n_actual   = N(n, max(1.0, 0.35·n))   clamped to >= 2
  - ratio_actual = N(ratio, max(0.005, 0.15·ratio)) clamped to [0.01, 1.0]
  - pearson_actual = N(pearson_anchor, 0.30) clamped to [-0.99, 0.99]
  - When target_pearson_r >= 0.9, rejection-sample until the realised
    Pearson r is within 0.03 of the target (max 200 attempts).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.stats import pearsonr as _pearsonr
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models import Item, KnapsackInstance

DEFAULT_MAX_WEIGHT = 1000

_MAX_REJECTION_ATTEMPTS = 200


# ── Core generation ──────────────────────────────────────────────────────────

def _generate_with_target_correlation(
    rng: np.random.Generator,
    n: int,
    max_weight: int,
    target_pearson_r: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate (weights, values) targeting a specific Pearson correlation.

    Uses the Cholesky method:  y = r·x + sqrt(1-r²)·z
    then scales both arrays to [1, max_weight].
    """
    r = float(np.clip(target_pearson_r, -1.0, 1.0))

    x = rng.standard_normal(n)
    z = rng.standard_normal(n)
    y = r * x + np.sqrt(max(0.0, 1.0 - r ** 2)) * z

    def _scale(arr: np.ndarray) -> np.ndarray:
        lo, hi = arr.min(), arr.max()
        if hi == lo:
            return np.full(n, (max_weight + 1) // 2, dtype=int)
        normalised = (arr - lo) / (hi - lo)
        return np.round(normalised * (max_weight - 1) + 1).astype(int)

    return _scale(x), _scale(y)


def _generate_with_rejection(
    rng: np.random.Generator,
    n: int,
    max_weight: int,
    target_pearson_r: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Wrapper: rejection-sample when target_pearson_r >= 0.9.

    Ensures the realised Pearson r is within 0.03 of the target.
    Falls back to best attempt after _MAX_REJECTION_ATTEMPTS.
    """
    need_rejection = target_pearson_r >= 0.9
    tolerance = 0.03

    best_w, best_v = None, None
    best_err = float("inf")

    for _ in range(_MAX_REJECTION_ATTEMPTS if need_rejection else 1):
        w, v = _generate_with_target_correlation(rng, n, max_weight, target_pearson_r)

        if not need_rejection:
            return w, v

        if n < 3:
            return w, v

        actual_r, _ = _pearsonr(w.astype(float), v.astype(float))
        err = abs(actual_r - target_pearson_r)

        if err < best_err:
            best_err = err
            best_w, best_v = w, v

        if err <= tolerance:
            return w, v

    return best_w, best_v


def _jitter_n(rng: np.random.Generator, n_anchor: int) -> int:
    """Apply Gaussian jitter:  n_actual = N(n, max(1.0, n*0.35)), clamped >= 2."""
    sigma = max(1.0, n_anchor * 0.35)
    n_actual = int(round(rng.normal(loc=n_anchor, scale=sigma)))
    return max(2, n_actual)


def _jitter_ratio(rng: np.random.Generator, ratio_anchor: float) -> float:
    """Apply Gaussian jitter: ratio_actual = N(ratio, max(0.005, ratio*0.15)), [0.01, 1.0]."""
    sigma = max(0.005, ratio_anchor * 0.15)
    ratio_actual = rng.normal(loc=ratio_anchor, scale=sigma)
    return float(np.clip(ratio_actual, 0.01, 1.0))


def _jitter_pearson(rng: np.random.Generator, pearson_anchor: float) -> float:
    """Apply Gaussian jitter: pearson_actual = N(pearson_anchor, 0.30), [-0.99, 0.99]."""
    pearson_actual = rng.normal(loc=pearson_anchor, scale=0.30)
    return float(np.clip(pearson_actual, -0.99, 0.99))


# ── Build helpers ────────────────────────────────────────────────────────────

def _build_items(weights: np.ndarray, values: np.ndarray) -> List[Item]:
    return [
        Item(id=int(idx), weight=float(w), value=float(v))
        for idx, (w, v) in enumerate(zip(weights, values))
    ]


def _instance_to_json_dict(
    instance: KnapsackInstance,
    test_id: str,
    *,
    n_anchor: int,
    n_actual: int,
    target_pearson_r: float,
    pearson_actual: float,
    ratio_anchor: float,
    ratio_actual: float,
    max_weight: int,
    seed: int,
    instance_seed: int,
) -> dict:
    return {
        "test_id": test_id,
        "capacity": instance.capacity,
        "metadata": {
            **instance.metadata,
            "n_anchor": n_anchor,
            "n_actual": n_actual,
            "target_pearson_r": target_pearson_r,
            "pearson_actual": pearson_actual,
            "capacity_ratio_anchor": ratio_anchor,
            "capacity_ratio_actual": ratio_actual,
            "max_weight": max_weight,
            "seed": seed,
            "instance_seed": instance_seed,
        },
        "items": [
            {"id": it.id, "weight": it.weight, "value": it.value}
            for it in instance.items
        ],
    }


def generate_instance(
    n_anchor: int,
    ratio_anchor: float,
    target_pearson_r: float,
    instance_index: int,
    rng: np.random.Generator,
    scenario_name: str,
    max_weight: int = DEFAULT_MAX_WEIGHT,
) -> Tuple[KnapsackInstance, str, int, float, float]:
    """Generate a single instance with Gaussian jitter on n, ratio, and pearson.

    Returns (instance, test_id, n_actual, ratio_actual, pearson_actual).
    """
    n_actual = _jitter_n(rng, n_anchor)
    ratio_actual = _jitter_ratio(rng, ratio_anchor)
    pearson_actual = _jitter_pearson(rng, target_pearson_r)

    weights, values = _generate_with_rejection(
        rng, n_actual, max_weight, pearson_actual
    )
    total_weight = float(np.sum(weights))
    capacity = total_weight * ratio_actual

    items = _build_items(weights, values)
    instance = KnapsackInstance(items=items, capacity=capacity)

    idx_str = f"{instance_index:02d}"
    test_id = (
        f"{scenario_name}_n{n_anchor}_wmax{max_weight}"
        f"_cr{ratio_anchor:g}_pr{target_pearson_r:g}_{idx_str}"
    )
    return instance, test_id, n_actual, ratio_actual, pearson_actual


def save_instance(
    instance: KnapsackInstance,
    test_id: str,
    output_dir: Path,
    *,
    n_anchor: int,
    n_actual: int,
    target_pearson_r: float,
    pearson_actual: float,
    ratio_anchor: float,
    ratio_actual: float,
    max_weight: int,
    seed: int,
    instance_seed: int,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{test_id}.json"
    data = _instance_to_json_dict(
        instance, test_id,
        n_anchor=n_anchor,
        n_actual=n_actual,
        target_pearson_r=target_pearson_r,
        pearson_actual=pearson_actual,
        ratio_anchor=ratio_anchor,
        ratio_actual=ratio_actual,
        max_weight=max_weight,
        seed=seed,
        instance_seed=instance_seed,
    )
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return path


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate 0/1 knapsack benchmark instances."
    )
    parser.add_argument(
        "--config", type=Path,
        default=Path(__file__).resolve().parent / "test_scenarios.json",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(__file__).resolve().parent / "raw"
    seed = args.seed

    with args.config.open("r", encoding="utf-8") as fh:
        scenarios = json.load(fh)

    total = sum(
        len(s["n_values"])
        * len(s["capacity_ratios"])
        * len(s["pearson_r_targets"])
        * s["instances_per_config"]
        for s in scenarios
    )

    with tqdm(total=total, desc="Generating instances") as pbar:
        for scenario in scenarios:
            name = scenario["name"]
            mw = int(scenario.get("max_weight", DEFAULT_MAX_WEIGHT))
            for n_anchor in scenario["n_values"]:
                for ratio_anchor in scenario["capacity_ratios"]:
                    ratio_sc = int(round(ratio_anchor * 1000))
                    for target_r in scenario["pearson_r_targets"]:
                        r_sc = int(round(target_r * 1000))
                        for idx in range(1, scenario["instances_per_config"] + 1):
                            iseed = (
                                seed * 1_000_003
                                + n_anchor * 101
                                + ratio_sc * 1009
                                + r_sc * 9176
                                + idx
                            ) % (2**32)
                            rng = np.random.default_rng(iseed)

                            inst, tid, n_act, r_act, p_act = generate_instance(
                                n_anchor=n_anchor,
                                ratio_anchor=ratio_anchor,
                                target_pearson_r=target_r,
                                instance_index=idx,
                                rng=rng,
                                scenario_name=name,
                                max_weight=mw,
                            )
                            save_instance(
                                inst, tid, output_dir,
                                n_anchor=n_anchor,
                                n_actual=n_act,
                                target_pearson_r=target_r,
                                pearson_actual=p_act,
                                ratio_anchor=ratio_anchor,
                                ratio_actual=r_act,
                                max_weight=mw,
                                seed=seed,
                                instance_seed=iseed,
                            )
                            pbar.update(1)


if __name__ == "__main__":
    main()
