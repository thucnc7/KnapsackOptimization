"""Generate JSON benchmark instances for the 0/1 knapsack problem."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple, Union

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
    delta = max_weight // 10
    weights = rng.integers(1, max_weight + 1, size=n, endpoint=False)
    values = weights + delta
    return weights, values


def _compute_metadata(
    weights: np.ndarray, values: np.ndarray, capacity_ratio: float
) -> Dict[str, Union[int, float]]:
    """Compute statistical metadata for the generated instance."""
    total_weight = float(np.sum(weights))
    capacity = int(total_weight * capacity_ratio)
    ratio = float(capacity / total_weight) if total_weight > 0 else 0.0
    weight_mean = float(np.mean(weights))
    weight_std_dev = float(np.std(weights))
    value_mean = float(np.mean(values))
    value_std_dev = float(np.std(values))

    if weight_std_dev == 0.0 or value_std_dev == 0.0:
        pearson_corr = 0.0
    else:
        pearson_corr = float(np.corrcoef(weights, values)[0, 1])

    density = values / weights
    density_variance = float(np.var(density))

    return {
        "n": int(len(weights)),
        "capacity": capacity,
        "capacity_to_total_weight_ratio": ratio,
        "weight_mean": weight_mean,
        "weight_std_dev": weight_std_dev,
        "value_mean": value_mean,
        "value_std_dev": value_std_dev,
        "pearson_correlation_coefficient": pearson_corr,
        "density_variance": density_variance,
    }


def _enrich_metadata(
    metadata: Dict[str, Union[int, float]],
    strategy_name: str,
    capacity_ratio: float,
    max_weight: int,
    seed: int,
) -> Dict[str, Union[int, float, str]]:
    """Add generation parameters to metadata for traceability."""
    metadata["strategy"] = strategy_name
    metadata["capacity_ratio_input"] = capacity_ratio
    metadata["max_weight"] = max_weight
    metadata["seed"] = seed
    return metadata


def _build_items(weights: np.ndarray, values: np.ndarray) -> List[Item]:
    """Convert numpy arrays into Item records."""
    items: List[Item] = []
    for idx, (w, v) in enumerate(zip(weights, values)):
        items.append(Item(id=int(idx), w=int(w), v=int(v)))
    return items


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
) -> KnapsackInstance:
    """Generate a single knapsack instance with computed metadata."""
    weights, values = strategy(rng, n, max_weight)
    metadata = _compute_metadata(weights, values, ratio)
    metadata = _enrich_metadata(metadata, strategy_name, ratio, max_weight, seed)
    index_str = f"{instance_index:02d}"
    ratio_str = f"{ratio:g}"
    test_id = (
        f"{scenario_name}_n{n}_wmax{max_weight}_r{ratio_str}_{strategy_name}_{index_str}"
    )
    items = _build_items(weights, values)
    return KnapsackInstance(test_id=test_id, metadata=metadata, items=items)


def save_instance(instance: KnapsackInstance, output_dir: Path) -> Path:
    """Write the instance as JSON to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{instance.test_id}.json"
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(instance.to_json_dict(), handle, indent=2)
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
            scenario_max_weight = scenario.get("max_weight", DEFAULT_MAX_WEIGHT)

            for n in n_values:
                for ratio in ratios:
                    for strategy_name in strategy_names:
                        strategy = strategy_map.get(strategy_name)
                        if strategy is None:
                            raise ValueError(
                                f"Unknown strategy '{strategy_name}' in {scenario_name}"
                            )
                        for index in range(1, instances_per_config + 1):
                            instance = generate_instance(
                                strategy=strategy,
                                n=n,
                                ratio=ratio,
                                instance_index=index,
                                rng=rng,
                                scenario_name=scenario_name,
                                strategy_name=strategy_name,
                                max_weight=int(scenario_max_weight),
                                seed=seed,
                            )
                            save_instance(instance, output_dir)
                            progress.update(1)


if __name__ == "__main__":
    main()
