"""Benchmark orchestrator for knapsack algorithms."""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple

from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models import Item, KnapsackInstance
from src.algorithms.basic import (
    BacktrackingSolver,
    BranchAndBoundSolver,
    DPKnapsackSolver,
)
from src.algorithms.greedy import GreedyKnapsackSolver
from src.algorithms.simplex import (
    PrimalSimplexSolver,
    DualSimplexSolver,
    BranchAndBoundSimplexSolver,
    GomoryCutSolver,
)
from benchmark.metrics import (
    STATUS_SUCCESS,
    run_with_profiler,
)


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    factory: Callable[..., Any]
    target_knapsack_type: str


def get_algorithm_registry() -> Sequence[AlgorithmSpec]:
    """Return the list of algorithm specs to benchmark."""
    return [
        AlgorithmSpec(name="DP", factory=DPKnapsackSolver, target_knapsack_type="01"),
        AlgorithmSpec(
            name="BranchAndBound",
            factory=BranchAndBoundSolver,
            target_knapsack_type="01",
        ),
        AlgorithmSpec(
            name="Backtracking",
            factory=BacktrackingSolver,
            target_knapsack_type="01",
        ),
        AlgorithmSpec(
            name="GomoryCut",
            factory=GomoryCutSolver,
            target_knapsack_type="01",
        ),
        AlgorithmSpec(
            name="SimplexBnB",
            factory=BranchAndBoundSimplexSolver,
            target_knapsack_type="01",
        ),
        AlgorithmSpec(
            name="GreedyFractional",
            factory=GreedyKnapsackSolver,
            target_knapsack_type="fractional",
        ),
        AlgorithmSpec(
            name="PrimalSimplex",
            factory=PrimalSimplexSolver,
            target_knapsack_type="fractional",
        ),
        AlgorithmSpec(
            name="DualSimplex",
            factory=DualSimplexSolver,
            target_knapsack_type="fractional",
        ),
        AlgorithmSpec(
            name="Greedy01",
            factory=GreedyKnapsackSolver,
            target_knapsack_type="01",
        ),
        AlgorithmSpec(
            name="DPUnbounded",
            factory=DPKnapsackSolver,
            target_knapsack_type="unbounded",
        ),
    ]


def _load_instances(raw_dir: Path) -> List[Tuple[str, KnapsackInstance, Dict[str, Any]]]:
    instances: List[Tuple[str, KnapsackInstance, Dict[str, Any]]] = []
    for path in sorted(raw_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        items = [
            Item(id=item["id"], weight=float(item["weight"]), value=float(item["value"]))
            for item in payload.get("items", [])
        ]
        instance = KnapsackInstance(items=items, capacity=float(payload["capacity"]))
        instances.append((payload.get("test_id", path.stem), instance, payload.get("metadata", {})))
    return instances


def _density_variance(items: Sequence[Item]) -> float:
    if not items or len(items) <= 1:
        return 0.0
    densities = [item.density for item in items]
    mean_density = sum(densities) / len(densities)
    # Sample variance (/ n-1) to match models.py _calculate_metadata
    variance = sum((d - mean_density) ** 2 for d in densities) / (len(densities) - 1)
    return variance


def _normalize_knapsack_type(value: str) -> str:
    value = str(value).lower().strip()
    mapping = {
        "01": "01",
        "zero_one": "01",
        "0/1": "01",
        "fractional": "fractional",
        "unbounded": "unbounded",
    }
    return mapping.get(value, value)


def _run_algorithm(algorithm: Any, instance: KnapsackInstance, knapsack_type: str) -> Any:
    """Execute an algorithm instance using the requested knapsack variant."""
    variant = _normalize_knapsack_type(knapsack_type)

    if variant == "fractional":
        if hasattr(algorithm, "run_fractional"):
            return algorithm.run_fractional()
        if hasattr(algorithm, "solve_fractional"):
            return algorithm.solve_fractional()
    elif variant == "unbounded":
        if hasattr(algorithm, "run_unbounded"):
            return algorithm.run_unbounded()
        if hasattr(algorithm, "solve_unbounded"):
            return algorithm.solve_unbounded()
    else:
        if hasattr(algorithm, "run_zero_one"):
            return algorithm.run_zero_one()
        if hasattr(algorithm, "solve_zero_one"):
            return algorithm.solve_zero_one()

    if hasattr(algorithm, "solve"):
        try:
            return algorithm.solve(instance)
        except TypeError:
            algorithm.instance = instance
            return algorithm.solve()
    if hasattr(algorithm, "run"):
        try:
            return algorithm.run(instance)
        except TypeError:
            algorithm.instance = instance
            return algorithm.run()
    if callable(algorithm):
        return algorithm(instance)
    raise TypeError("Algorithm does not expose a callable solve/run interface.")


def _execute_algorithm(
    factory: Callable[..., Any],
    instance: KnapsackInstance,
    default_knapsack_type: str,
) -> Tuple[Any, str]:
    try:
        algorithm = factory()
    except TypeError:
        algorithm = factory(instance)
    knapsack_type = getattr(algorithm, "target_knapsack_type", default_knapsack_type)
    result = _run_algorithm(algorithm, instance, knapsack_type)
    return result, _normalize_knapsack_type(knapsack_type)


def _extract_optimal_value(result: Any) -> int:
    if result is None:
        return -1
    if isinstance(result, (int, float)):
        return int(round(result))
    if isinstance(result, dict):
        for key in ("optimal_value", "best_value", "value"):
            if key in result:
                return int(round(result[key]))
    if isinstance(result, tuple) and result:
        head = result[0]
        if isinstance(head, (int, float)):
            return int(round(head))
    for attr in ("optimal_value", "best_value", "value"):
        if hasattr(result, attr):
            return int(round(getattr(result, attr)))
    return -1


def _format_float(value: float, precision: int) -> str:
    return f"{value:.{precision}f}"


def _build_row(
    test_id: str,
    algorithm: AlgorithmSpec,
    knapsack_type: str,
    status: str,
    exec_time: float,
    peak_memory_mb: float,
    optimal_value: int,
    instance: KnapsackInstance,
    payload_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    # Prefer JSON payload metadata (capacity_ratio_input, target_pearson_r) with fallback to computed metadata.
    metadata = payload_metadata or instance.metadata
    return {
        "test_id": test_id,
        "algorithm": algorithm.name,
        "knapsack_type": knapsack_type,
        "status": status,
        "time_sec": _format_float(exec_time, 5),
        "peak_memory_mb": _format_float(peak_memory_mb, 4),
        "optimal_value": optimal_value,
        "n": int(metadata.get("n", len(instance.items))),
        "capacity": int(round(instance.capacity)),
        "capacity_to_weight_ratio": metadata.get(
            "capacity_ratio_actual",
            metadata.get("capacity_ratio", 0.0),
        ),
        "pearson_corr": metadata.get(
            "pearson_r",
            metadata.get("pearson_actual", 0.0),
        ),
        "density_variance": _density_variance(instance.items),
    }


def run_benchmark(
    raw_dir: Path,
    output_csv: Path,
    timeout_sec: int,
    limit: int,
) -> List[Dict[str, Any]]:
    instances = _load_instances(raw_dir)
    if limit > 0:
        instances = instances[:limit]

    algorithms = list(get_algorithm_registry())
    rows: List[Dict[str, Any]] = []

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "test_id",
        "algorithm",
        "knapsack_type",
        "status",
        "time_sec",
        "peak_memory_mb",
        "optimal_value",
        "n",
        "capacity",
        "capacity_to_weight_ratio",
        "pearson_corr",
        "density_variance",
    ]

    completed = _load_existing_keys(output_csv)
    total_tasks = len(instances) * len(algorithms)
    skipped = len(completed)

    write_header = not output_csv.exists() or output_csv.stat().st_size == 0
    with output_csv.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
            handle.flush()

        with tqdm(total=total_tasks, desc="Benchmarking", unit="run") as progress:
            if skipped:
                progress.update(min(skipped, total_tasks))
            for test_id, instance, payload_metadata in instances:
                for algo in algorithms:
                    if (test_id, algo.name) in completed:
                        continue

                    status, result, exec_time, peak_mb = run_with_profiler(
                        _execute_algorithm,
                        (algo.factory, instance, algo.target_knapsack_type),
                        timeout_sec=timeout_sec,
                    )

                    if status != STATUS_SUCCESS:
                        optimal_value = -1
                        knapsack_type = _normalize_knapsack_type(algo.target_knapsack_type)
                    else:
                        result_value, knapsack_type = result
                        optimal_value = _extract_optimal_value(result_value)

                    row = _build_row(
                        test_id=test_id,
                        algorithm=algo,
                        knapsack_type=knapsack_type,
                        status=status,
                        exec_time=exec_time,
                        peak_memory_mb=peak_mb,
                        optimal_value=optimal_value,
                        instance=instance,
                        payload_metadata=payload_metadata,
                    )
                    writer.writerow(row)
                    handle.flush()
                    rows.append(row)
                    completed.add((test_id, algo.name))
                    progress.update(1)

    return rows


def _load_existing_keys(output_csv: Path) -> set[tuple[str, str]]:
    if not output_csv.exists():
        return set()
    completed: set[tuple[str, str]] = set()
    try:
        with output_csv.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                test_id = (row.get("test_id") or "").strip()
                algorithm = (row.get("algorithm") or "").strip()
                if test_id and algorithm:
                    completed.add((test_id, algorithm))
    except (csv.Error, OSError):
        # If the CSV is partially written or corrupted, resume from what we can parse.
        pass
    return completed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run knapsack benchmark suite.")
    parser.add_argument(
        "--raw",
        type=Path,
        default=ROOT_DIR / "data" / "raw",
        help="Directory containing JSON instances.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT_DIR / "results" / "csv" / "benchmark_results.csv",
        help="CSV output path.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout (seconds) for each algorithm run.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=max(1, (os.cpu_count() or 4) // 2),
        help="Number of parallel jobs to run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of instances (0 = all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.raw.exists():
        raise FileNotFoundError(f"Raw data directory not found: {args.raw}")

    run_benchmark(
        raw_dir=args.raw,
        output_csv=args.output,
        timeout_sec=max(args.timeout, 1),
        limit=max(args.limit, 0),
    )


if __name__ == "__main__":
    mp.freeze_support()
    main()
