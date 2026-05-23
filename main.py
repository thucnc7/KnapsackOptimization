"""Quick demo: solve a single 0/1 Knapsack instance with each algorithm."""

from __future__ import annotations

import random
import time

from src.models import Item, KnapsackInstance
from src.algorithms.basic import (
    BacktrackingSolver,
    BranchAndBoundSolver,
    DPKnapsackSolver,
    GreedyKnapsackSolver,
)
from src.algorithms.simplex import (
    PrimalSimplexSolver,
    DualSimplexSolver,
)


def _make_instance(n: int = 30, seed: int = 42) -> KnapsackInstance:
    rng = random.Random(seed)
    items = [
        Item(id=i, weight=float(rng.randint(1, 100)), value=float(rng.randint(10, 200)))
        for i in range(n)
    ]
    capacity = sum(it.weight for it in items) * 0.5
    return KnapsackInstance(items=items, capacity=capacity)


def _row(name: str, value: float, runtime: float, items_count: int) -> str:
    return f"  {name:<22} value={value:>12.2f}   time={runtime*1000:>9.3f} ms   items={items_count}"


def main() -> None:
    instance = _make_instance(n=30, seed=42)
    n = len(instance.items)
    cap = instance.capacity
    print(f"Instance: n={n}, capacity={cap:.2f}")
    print(f"  total weight = {sum(it.weight for it in instance.items):.2f}")
    print(f"  total value  = {sum(it.value for it in instance.items):.2f}")
    print()

    print("--- Exact 0/1 solvers (basic) ---")
    for name, factory in [
        ("DP", DPKnapsackSolver),
        ("BranchAndBound", BranchAndBoundSolver),
        ("Backtracking", BacktrackingSolver),
    ]:
        solver = factory(instance)
        t0 = time.perf_counter()
        value, selected = solver.solve_zero_one()
        runtime = time.perf_counter() - t0
        print(_row(name, value, runtime, len(selected)))

    print()
    print("--- LP solvers (Simplex, baseline Greedy) ---")
    greedy = GreedyKnapsackSolver(instance)
    t0 = time.perf_counter()
    value, selected = greedy.solve_fractional()
    runtime = time.perf_counter() - t0
    print(_row("GreedyFractional", value, runtime, len(selected)))
    for name, factory in [
        ("PrimalSimplex", PrimalSimplexSolver),
        ("DualSimplex", DualSimplexSolver),
    ]:
        solver = factory(instance)
        t0 = time.perf_counter()
        value, selected = solver.solve_fractional()
        runtime = time.perf_counter() - t0
        print(_row(name, value, runtime, len(selected)))


if __name__ == "__main__":
    main()
