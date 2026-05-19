"""Generate JSON benchmark instances for the 0/1 knapsack problem."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models import Item, KnapsackInstance

DEFAULT_MAX_WEIGHT = 1000
DEFAULT_CAPACITY_RATIO = 0.5

StrategyFn = Callable[[np.random.Generator, int, int], Tuple[np.ndarray, np.ndarray]]


def _generate_uncorrelated(
    rng: np.random.Generator, n: int, max_weight: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate weights and values independently from uniform distributions."""
    weights = rng.integers(1, max_weight + 1, size=n, endpoint=False)
    values = rng.integers(1, max_weight + 1, size=n, endpoint=False)
    return weights, values


def _generate_weakly_correlated(
    rng: np.random.Generator, n: int, max_weight: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate values in a band around the weights."""
    delta = max(1, max_weight // 10)
    weights = rng.integers(1, max_weight + 1, size=n, endpoint=False)
    low = np.maximum(1, weights - delta)
    high = weights + delta
    values = rng.integers(low, high + 1, endpoint=False)
    return weights, values


def _generate_strongly_correlated(
    rng: np.random.Generator, n: int, max_weight: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate values as a deterministic offset of weights."""
    delta = max(1, max_weight // 10)
    weights = rng.integers(1, max_weight + 1, size=n, endpoint=False)
    values = weights + delta
    return weights, values


def _build_items(weights: np.ndarray, values: np.ndarray) -> List[Item]:
    """Convert numpy arrays into Item records (using new model fields)."""
    return [
        Item(id=int(idx), weight=float(w), value=float(v))
        for idx, (w, v) in enumerate(zip(weights, values))
    ]


def _instance_to_json_dict(
    instance: KnapsackInstance,
    test_id: str,
    strategy_name: str,
    capacity_ratio_input: float,
    max_weight: int,
    seed: int,
) -> dict:
    """Serialize a KnapsackInstance to a JSON-ready dictionary.

    Includes traceability fields (strategy, seed, max_weight) alongside
    the metadata auto-calculated by the model.
    """
    return {
        "test_id": test_id,
        "capacity": instance.capacity,
        "metadata": {
            **instance.metadata,
            "strategy": strategy_name,
            "capacity_ratio_input": capacity_ratio_input,
            "max_weight": max_weight,
            "seed": seed,
        },
        "items": [
            {"id": item.id, "weight": item.weight, "value": item.value}
            for item in instance.items
        ],
    }


def generate_instance(
    strategy: StrategyFn,
    n: int,
    ratio: float,
    instance_index: int,
    rng: np.random.Generator,
    scenario_name: str,
    strategy_name: str,
    max_weight: int = DEFAULT_MAX_WEIGHT,
    seed: int = 0,
) -> Tuple[KnapsackInstance, str]:
    """Generate a single knapsack instance and return it with its test_id."""
    weights, values = strategy(rng, n, max_weight)
    total_weight = float(np.sum(weights))
    capacity = total_weight * ratio

    items = _build_items(weights, values)
    instance = KnapsackInstance(items=items, capacity=capacity)

    index_str = f"{instance_index:02d}"
    ratio_str = f"{ratio:g}"
    test_id = (
        f"{scenario_name}_n{n}_wmax{max_weight}_r{ratio_str}_{strategy_name}_{index_str}"
    )
    return instance, test_id


def save_instance(
    instance: KnapsackInstance,
    test_id: str,
    output_dir: Path,
    strategy_name: str,
    capacity_ratio_input: float,
    max_weight: int,
    seed: int,
) -> Path:
    """Write the instance as JSON to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{test_id}.json"
    data = _instance_to_json_dict(
        instance, test_id, strategy_name, capacity_ratio_input, max_weight, seed
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
    rng = np.random.default_rng(seed)

    with args.config.open("r", encoding="utf-8") as handle:
        scenarios = json.load(handle)

    strategy_map: Dict[str, StrategyFn] = {
        "uncorrelated": _generate_uncorrelated,
        "weakly_correlated": _generate_weakly_correlated,
        "strongly_correlated": _generate_strongly_correlated,
    }

    total_tasks = 0
    for scenario in scenarios:
        total_tasks += (
            len(scenario["n_values"])
            * len(scenario["capacity_ratios"])
            * len(scenario["strategies"])
            * scenario["instances_per_config"]
        )

    with tqdm(total=total_tasks, desc="Generating instances") as progress:
        for scenario in scenarios:
            scenario_name = scenario["name"]
            n_values = scenario["n_values"]
            ratios = scenario["capacity_ratios"]
            strategy_names = scenario["strategies"]
            instances_per_config = scenario["instances_per_config"]
            scenario_max_weight = int(scenario.get("max_weight", DEFAULT_MAX_WEIGHT))

            for n in n_values:
                for ratio in ratios:
                    for strategy_name in strategy_names:
                        strategy = strategy_map.get(strategy_name)
                        if strategy is None:
                            raise ValueError(
                                f"Unknown strategy '{strategy_name}' in {scenario_name}"
                            )
                        for index in range(1, instances_per_config + 1):
                            instance, test_id = generate_instance(
                                strategy=strategy,
                                n=n,
                                ratio=ratio,
                                instance_index=index,
                                rng=rng,
                                scenario_name=scenario_name,
                                strategy_name=strategy_name,
                                max_weight=scenario_max_weight,
                                seed=seed,
                            )
                            save_instance(
                                instance=instance,
                                test_id=test_id,
                                output_dir=output_dir,
                                strategy_name=strategy_name,
                                capacity_ratio_input=ratio,
                                max_weight=scenario_max_weight,
                                seed=seed,
                            )
                            progress.update(1)


if __name__ == "__main__":
    main()
