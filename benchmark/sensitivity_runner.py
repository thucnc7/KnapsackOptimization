"""Sensitivity analysis benchmark runner.

Compares resolving from scratch versus warm-starting using Primal/Dual Simplex.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
import numpy as np

# Set project root path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models import Item, KnapsackInstance
from src.algorithms.simplex.dual_simplex import DualSimplexSolver, SimplexTableau

def load_instance_from_json(path: Path) -> KnapsackInstance:
    with path.open("r", encoding="utf-8") as fh:
        raw_data = json.load(fh)
    
    items = [
        Item(id=int(it["id"]), weight=float(it["weight"]), value=float(it["value"]))
        for it in raw_data["items"]
    ]
    capacity = float(raw_data["capacity"])
    return KnapsackInstance(items=items, capacity=capacity)

def solve_scratch_with_extra_constraint(
    instance: KnapsackInstance,
    new_coeff: list[float],
    new_rhs: float
) -> tuple[float, int, str]:
    """Helper to solve the LP relaxation from scratch with an added constraint."""
    solver = DualSimplexSolver(instance)
    A, b, c = solver._convert_to_lp_form()
    
    A_mod = A + [new_coeff]
    b_mod = b + [new_rhs]
    
    t0 = time.perf_counter()
    is_primal_feasible = all(val >= 0 for val in b_mod)
    if is_primal_feasible:
        tab = SimplexTableau(c, A_mod, b_mod)
        status = tab.solve_primal()
    else:
        zero_c = [0.0] * len(c)
        tab = SimplexTableau(zero_c, A_mod, b_mod)
        status = tab.solve_dual()
        if status == "optimal":
            total_cols = tab.tableau.shape[1]
            new_obj = np.zeros(total_cols, dtype=float)
            new_obj[:tab.n] = -np.asarray(c, dtype=float)
            tab.tableau[-1] = new_obj
            for r in range(tab.m):
                basic_col = tab.basis[r]
                factor = tab.tableau[-1, basic_col]
                if abs(factor) > 1e-12:
                    tab.tableau[-1] -= factor * tab.tableau[r]
            status = tab.solve_primal()
            
    elapsed = time.perf_counter() - t0
    iterations = tab.iterations if hasattr(tab, "iterations") else 0
    return elapsed, iterations, status

def run_benchmarks():
    raw_dir = ROOT_DIR / "data" / "raw"
    csv_dir = ROOT_DIR / "results" / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / "sensitivity_results.csv"
    
    print(f"Starting Sensitivity Analysis Benchmark using raw JSON testcases...")
    print(f"Loading files from: {raw_dir}")
    print(f"Saving results to: {csv_path}")
    
    json_files = sorted(raw_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON testcase files found in {raw_dir}")
        
    # Filter files to only keep N <= 250 (15, 30, 45, 50, 250) to run fast in Python
    allowed_sizes = [15, 30, 45, 50, 250]
    filtered_files = []
    for path in json_files:
        name = path.name
        if any(f"_n{size}_" in name for size in allowed_sizes):
            filtered_files.append(path)
            
    if not filtered_files:
        raise ValueError(f"No testcase files with N <= 250 found in {raw_dir}")
        
    # Sample 200 files reproducibly
    rng = np.random.default_rng(42)
    selected_files = rng.choice(filtered_files, size=min(200, len(filtered_files)), replace=False)
    selected_files = sorted(selected_files)
    
    headers = [
        "instance_id", "n", "scenario", 
        "time_scratch_sec", "time_warm_sec", 
        "iter_scratch", "iter_warm", 
        "speedup", "status_scratch", "status_warm"
    ]
    
    results = []
    
    for idx, path in enumerate(selected_files):
        instance_id = idx + 1
        instance = load_instance_from_json(path)
        n = len(instance.items)
        
        # We need a unique seed per instance for generating volumes in Scenario C
        seed = 42000 + n * 11 + instance_id
        
        # Solve initial
        solver_base = DualSimplexSolver(instance)
        solver_base.solve_fractional()
        if solver_base.tableau is None:
            continue  # Skip invalid/unsolved base states
        iter_init = solver_base.tableau.iterations
        
        # --- Scenario A: Update Capacity (RHS) ---
        # Increase capacity by 15%
        delta_W = instance.capacity * 0.15
        
        # A1. Scratch resolve
        instance_mod_cap = KnapsackInstance(items=instance.items, capacity=instance.capacity + delta_W)
        t0 = time.perf_counter()
        solver_scratch_cap = DualSimplexSolver(instance_mod_cap)
        solver_scratch_cap.solve_fractional()
        time_scratch_cap = time.perf_counter() - t0
        iter_scratch_cap = solver_scratch_cap.tableau.iterations
        
        # A2. Warm start
        solver_warm_cap = DualSimplexSolver(instance)
        solver_warm_cap.solve_fractional()
        t0 = time.perf_counter()
        status_warm_cap = solver_warm_cap.update_rhs(0, delta_W)
        time_warm_cap = time.perf_counter() - t0
        iter_warm_cap = solver_warm_cap.tableau.iterations - iter_init
        
        speedup_cap = time_scratch_cap / time_warm_cap if time_warm_cap > 0 else 1.0
        results.append({
            "instance_id": instance_id, "n": n, "scenario": "capacity",
            "time_scratch_sec": time_scratch_cap, "time_warm_sec": time_warm_cap,
            "iter_scratch": iter_scratch_cap, "iter_warm": max(0, iter_warm_cap),
            "speedup": speedup_cap, "status_scratch": "optimal", "status_warm": status_warm_cap
        })
        
        # --- Scenario B: Update Object Value (Obj Coefficient) ---
        # Change value of item 0 by +25%
        item_idx = 0
        val_delta = instance.items[item_idx].value * 0.25
        
        # B1. Scratch resolve
        items_mod_obj = [Item(id=it.id, weight=it.weight, value=it.value) for it in instance.items]
        items_mod_obj[item_idx] = Item(
            id=items_mod_obj[item_idx].id, 
            weight=items_mod_obj[item_idx].weight, 
            value=items_mod_obj[item_idx].value + val_delta
        )
        instance_mod_obj = KnapsackInstance(items=items_mod_obj, capacity=instance.capacity)
        
        t0 = time.perf_counter()
        solver_scratch_obj = DualSimplexSolver(instance_mod_obj)
        solver_scratch_obj.solve_fractional()
        time_scratch_obj = time.perf_counter() - t0
        iter_scratch_obj = solver_scratch_obj.tableau.iterations
        
        # B2. Warm start
        solver_warm_obj = DualSimplexSolver(instance)
        solver_warm_obj.solve_fractional()
        t0 = time.perf_counter()
        status_warm_obj = solver_warm_obj.update_objective(item_idx, val_delta)
        time_warm_obj = time.perf_counter() - t0
        iter_warm_obj = solver_warm_obj.tableau.iterations - iter_init
        
        speedup_obj = time_scratch_obj / time_warm_obj if time_warm_obj > 0 else 1.0
        results.append({
            "instance_id": instance_id, "n": n, "scenario": "value",
            "time_scratch_sec": time_scratch_obj, "time_warm_sec": time_warm_obj,
            "iter_scratch": iter_scratch_obj, "iter_warm": max(0, iter_warm_obj),
            "speedup": speedup_obj, "status_scratch": "optimal", "status_warm": status_warm_obj
        })
        
        # --- Scenario C: Add Volume Constraint ---
        # Random volumes in [10, 50]
        rng_vol = np.random.default_rng(seed)
        volumes = rng_vol.uniform(10.0, 50.0, size=n)
        vol_limit = float(np.sum(volumes) * 0.4)
        new_coeff = [float(v) for v in volumes]
        
        # C1. Scratch resolve
        time_scratch_vol, iter_scratch_vol, status_scratch_vol = solve_scratch_with_extra_constraint(
            instance, new_coeff, vol_limit
        )
        
        # C2. Warm start
        solver_warm_vol = DualSimplexSolver(instance)
        solver_warm_vol.solve_fractional()
        t0 = time.perf_counter()
        status_warm_vol = solver_warm_vol.add_constraint_and_reoptimize(new_coeff, vol_limit)
        time_warm_vol = time.perf_counter() - t0
        iter_warm_vol = solver_warm_vol.tableau.iterations - iter_init
        
        speedup_vol = time_scratch_vol / time_warm_vol if time_warm_vol > 0 else 1.0
        results.append({
            "instance_id": instance_id, "n": n, "scenario": "volume",
            "time_scratch_sec": time_scratch_vol, "time_warm_sec": time_warm_vol,
            "iter_scratch": iter_scratch_vol, "iter_warm": max(0, iter_warm_vol),
            "speedup": speedup_vol, "status_scratch": status_scratch_vol, "status_warm": status_warm_vol
        })

    # Save to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Benchmark completed successfully! Total records: {len(results)}")

if __name__ == "__main__":
    run_benchmarks()
