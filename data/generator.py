"""Generate JSON benchmark instances for the 0/1 knapsack problem."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models import Item, KnapsackInstance

DEFAULT_MAX_WEIGHT = 1000
DEFAULT_CAPACITY_RATIO = 0.5


def _generate_with_target_correlation(
    rng: np.random.Generator,
    n: int,
    max_weight: int,
    target_pearson_r: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate (weights, values) arrays targeting a specific Pearson correlation.

    Uses the Cholesky / linear-combination method:
      - x ~ N(0,1) for weights
      - y = r*x + sqrt(1-r²)*z  where z ~ N(0,1) independent
    Both arrays are then scaled to integer values in [1, max_weight].
    The realised correlation converges to target_pearson_r as n grows.
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


def _build_items(weights: np.ndarray, values: np.ndarray) -> List[Item]:
    """Convert numpy arrays into Item records."""
    return [
        Item(id=int(idx), weight=float(w), value=float(v))
        for idx, (w, v) in enumerate(zip(weights, values))
    ]


def _instance_to_json_dict(
    instance: KnapsackInstance,
    test_id: str,
    target_pearson_r: float,
    capacity_ratio_input: float,
    max_weight: int,
    seed: int,
    instance_seed: int,
) -> dict:
    """Serialize a KnapsackInstance to a JSON-ready dictionary."""
    return {
        "test_id": test_id,
        "capacity": instance.capacity,
        "metadata": {
            **instance.metadata,
            "target_pearson_r": target_pearson_r,
            "capacity_ratio_input": capacity_ratio_input,
            "max_weight": max_weight,
            "seed": seed,
            "instance_seed": instance_seed,
        },
        "items": [
            {"id": item.id, "weight": item.weight, "value": item.value}
            for item in instance.items
        ],
    }


def generate_instance(
    n: int,
    ratio: float,
    target_pearson_r: float,
    instance_index: int,
    rng: np.random.Generator,
    scenario_name: str,
    max_weight: int = DEFAULT_MAX_WEIGHT,
) -> Tuple[KnapsackInstance, str]:
    """Generate a single knapsack instance and return it with its test_id."""
    weights, values = _generate_with_target_correlation(rng, n, max_weight, target_pearson_r)
    total_weight = float(np.sum(weights))
    capacity = total_weight * ratio

    items = _build_items(weights, values)
    instance = KnapsackInstance(items=items, capacity=capacity)

    index_str = f"{instance_index:02d}"
    ratio_str = f"{ratio:g}"
    r_str = f"{target_pearson_r:g}"
    test_id = (
        f"{scenario_name}_n{n}_wmax{max_weight}_cr{ratio_str}_pr{r_str}_{index_str}"
    )
    return instance, test_id


def save_instance(
    instance: KnapsackInstance,
    test_id: str,
    output_dir: Path,
    target_pearson_r: float,
    capacity_ratio_input: float,
    max_weight: int,
    seed: int,
    instance_seed: int,
) -> Path:
    """Write the instance as JSON to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{test_id}.json"
    data = _instance_to_json_dict(
        instance,
        test_id,
        target_pearson_r,
        capacity_ratio_input,
        max_weight,
        seed,
        instance_seed,
    )
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for instance generation."""
    parser = argparse.ArgumentParser(
        description="Generate 0/1 knapsack benchmark instances from scenarios."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "test_scenarios.json",
        help="Path to the scenario configuration JSON file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for the generator."""
    args = parse_args()
    output_dir = Path(__file__).resolve().parent / "raw"
    seed = args.seed

    with args.config.open("r", encoding="utf-8") as handle:
        scenarios = json.load(handle)

    total_tasks = 0
    for scenario in scenarios:
        total_tasks += (
            len(scenario["n_values"])
            * len(scenario["capacity_ratios"])
            * len(scenario["pearson_r_targets"])
            * scenario["instances_per_config"]
        )

    with tqdm(total=total_tasks, desc="Generating instances") as progress:
        for scenario in scenarios:
            scenario_name = scenario["name"]
            n_values = scenario["n_values"]
            ratios = scenario["capacity_ratios"]
            pearson_r_targets = scenario["pearson_r_targets"]
            instances_per_config = scenario["instances_per_config"]
            scenario_max_weight = int(scenario.get("max_weight", DEFAULT_MAX_WEIGHT))

            for n in n_values:
                for ratio in ratios:
                    ratio_scaled = int(round(ratio * 1000))
                    for target_r in pearson_r_targets:
                        r_scaled = int(round(target_r * 1000))
                        for index in range(1, instances_per_config + 1):
                            instance_seed = (
                                seed * 1_000_003
                                + n * 101
                                + ratio_scaled * 1009
                                + r_scaled * 9176
                                + index
                            ) % (2**32)
                            rng = np.random.default_rng(instance_seed)
                            instance, test_id = generate_instance(
                                n=n,
                                ratio=ratio,
                                target_pearson_r=target_r,
                                instance_index=index,
                                rng=rng,
                                scenario_name=scenario_name,
                                max_weight=scenario_max_weight,
                            )
                            save_instance(
                                instance=instance,
                                test_id=test_id,
                                output_dir=output_dir,
                                target_pearson_r=target_r,
                                capacity_ratio_input=ratio,
                                max_weight=scenario_max_weight,
                                seed=seed,
                                instance_seed=instance_seed,
                            )
                            progress.update(1)


if __name__ == "__main__":
    main()
