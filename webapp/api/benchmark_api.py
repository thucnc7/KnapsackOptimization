"""API endpoints serving benchmark CSV data with aggregations."""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("benchmark", __name__)

_NUMERIC_FIELDS = (
    "time_sec",
    "peak_memory_mb",
    "optimal_value",
    "n",
    "capacity",
    "capacity_to_weight_ratio",
    "pearson_corr",
    "density_variance",
)


def _csv_dir() -> Path:
    return Path(current_app.config["RESULTS_CSV_DIR"])


def _coerce(row: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(row)
    for key in _NUMERIC_FIELDS:
        if key in out and out[key] not in (None, ""):
            try:
                out[key] = float(out[key]) if "." in out[key] or "e" in out[key].lower() else int(out[key])
            except (ValueError, TypeError):
                try:
                    out[key] = float(out[key])
                except (ValueError, TypeError):
                    out[key] = None
    return out


def _load_csv(filename: str) -> List[Dict[str, Any]]:
    target = _csv_dir() / filename
    if not target.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with target.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(_coerce(row))
    return rows


@bp.route("/files", methods=["GET"])
def list_csv_files():
    csv_dir = _csv_dir()
    if not csv_dir.exists():
        return jsonify([])
    files = [
        {
            "name": p.name,
            "size_bytes": p.stat().st_size,
            "rows": _count_rows(p),
        }
        for p in sorted(csv_dir.glob("*.csv"))
    ]
    return jsonify(files)


def _count_rows(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return max(0, sum(1 for _ in handle) - 1)
    except OSError:
        return 0


@bp.route("/raw", methods=["GET"])
def raw_rows():
    filename = request.args.get("file", "benchmark_results.csv")
    algorithm = request.args.get("algorithm")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 0) or 0)

    rows = _load_csv(filename)
    if algorithm:
        rows = [r for r in rows if r.get("algorithm") == algorithm]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if limit > 0:
        rows = rows[:limit]
    return jsonify(rows)


@bp.route("/summary", methods=["GET"])
def summary():
    filename = request.args.get("file", "benchmark_results.csv")
    rows = _load_csv(filename)
    if not rows:
        return jsonify({"algorithms": [], "totals": {}, "by_algorithm": {}, "by_n": {}})

    by_algo: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total": 0, "success": 0, "timeout": 0, "error": 0,
        "times_success": [], "memory_success": [],
    })
    by_n: Dict[int, Dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: {
        "total": 0, "success": 0, "avg_time": 0.0, "_times": [],
    }))

    for r in rows:
        algo = r.get("algorithm", "?")
        st = r.get("status", "?")
        n_val = r.get("n", 0)
        by_algo[algo]["total"] += 1
        if st == "SUCCESS":
            by_algo[algo]["success"] += 1
            t = r.get("time_sec")
            m = r.get("peak_memory_mb")
            if isinstance(t, (int, float)):
                by_algo[algo]["times_success"].append(t)
            if isinstance(m, (int, float)):
                by_algo[algo]["memory_success"].append(m)
        elif st == "TIMEOUT":
            by_algo[algo]["timeout"] += 1
        else:
            by_algo[algo]["error"] += 1

        cell = by_n[n_val][algo]
        cell["total"] += 1
        if st == "SUCCESS":
            cell["success"] += 1
            t = r.get("time_sec")
            if isinstance(t, (int, float)):
                cell["_times"].append(t)

    out_algo: Dict[str, Any] = {}
    for algo, d in by_algo.items():
        times = d["times_success"]
        mems = d["memory_success"]
        out_algo[algo] = {
            "total": d["total"],
            "success": d["success"],
            "timeout": d["timeout"],
            "error": d["error"],
            "success_rate": round(d["success"] / d["total"], 4) if d["total"] else 0,
            "avg_time": round(mean(times), 6) if times else None,
            "median_time": round(median(times), 6) if times else None,
            "max_time": round(max(times), 6) if times else None,
            "avg_memory_mb": round(mean(mems), 4) if mems else None,
            "max_memory_mb": round(max(mems), 4) if mems else None,
        }

    out_by_n: Dict[str, Dict[str, Any]] = {}
    for n_val, algos in by_n.items():
        out_by_n[str(n_val)] = {
            algo: {
                "total": c["total"],
                "success": c["success"],
                "avg_time": round(mean(c["_times"]), 6) if c["_times"] else None,
            }
            for algo, c in algos.items()
        }

    return jsonify({
        "algorithms": sorted(out_algo.keys()),
        "totals": {
            "rows": len(rows),
            "instances": len({r.get("test_id") for r in rows}),
        },
        "by_algorithm": out_algo,
        "by_n": out_by_n,
    })


@bp.route("/sensitivity", methods=["GET"])
def sensitivity():
    """Return aggregates + raw rows from sensitivity_results.csv (warm-start study)."""
    import statistics
    filename = request.args.get("file", "sensitivity_results.csv")
    target = _csv_dir() / filename
    if not target.exists():
        return jsonify({"rows": [], "by_scenario": {}, "totals": {}, "available": False,
                        "hint": "Chạy `python benchmark/sensitivity_runner.py` để sinh file này."})
    rows: List[Dict[str, Any]] = []
    with target.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            coerced: Dict[str, Any] = dict(row)
            for key in ("n", "iter_scratch", "iter_warm"):
                try:
                    coerced[key] = int(row[key])
                except (KeyError, ValueError, TypeError):
                    coerced[key] = None
            for key in ("time_scratch_sec", "time_warm_sec", "speedup"):
                try:
                    coerced[key] = float(row[key])
                except (KeyError, ValueError, TypeError):
                    coerced[key] = None
            rows.append(coerced)

    by_scenario: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        sc = r.get("scenario", "?")
        bucket = by_scenario.setdefault(sc, {
            "count": 0, "warm_wins": 0,
            "speedups": [], "time_scratch": [], "time_warm": [],
            "iter_scratch": [], "iter_warm": [],
        })
        bucket["count"] += 1
        sp = r.get("speedup")
        if isinstance(sp, (int, float)):
            bucket["speedups"].append(sp)
            if sp > 1.0:
                bucket["warm_wins"] += 1
        for src, dst in (("time_scratch_sec", "time_scratch"),
                         ("time_warm_sec", "time_warm"),
                         ("iter_scratch", "iter_scratch"),
                         ("iter_warm", "iter_warm")):
            v = r.get(src)
            if isinstance(v, (int, float)):
                bucket[dst].append(v)

    def _stats(vals):
        if not vals:
            return {"mean": None, "median": None, "max": None, "min": None}
        return {
            "mean": round(statistics.mean(vals), 4),
            "median": round(statistics.median(vals), 4),
            "max": round(max(vals), 4),
            "min": round(min(vals), 4),
        }

    summary_by_scenario: Dict[str, Any] = {}
    all_speedups: List[float] = []
    all_warm_wins = 0
    total_count = 0
    for sc, b in by_scenario.items():
        summary_by_scenario[sc] = {
            "count": b["count"],
            "warm_wins": b["warm_wins"],
            "warm_win_rate": round(b["warm_wins"] / b["count"], 4) if b["count"] else 0,
            "speedup": _stats(b["speedups"]),
            "time_scratch": _stats(b["time_scratch"]),
            "time_warm": _stats(b["time_warm"]),
            "iter_scratch": _stats(b["iter_scratch"]),
            "iter_warm": _stats(b["iter_warm"]),
        }
        all_speedups.extend(b["speedups"])
        all_warm_wins += b["warm_wins"]
        total_count += b["count"]

    return jsonify({
        "available": True,
        "rows": rows,
        "by_scenario": summary_by_scenario,
        "totals": {
            "count": total_count,
            "warm_wins": all_warm_wins,
            "warm_win_rate": round(all_warm_wins / total_count, 4) if total_count else 0,
            "speedup": _stats(all_speedups),
        },
    })


@bp.route("/compare", methods=["GET"])
def compare():
    """Return paired results for two algorithms on the same test_id."""
    filename = request.args.get("file", "benchmark_results.csv")
    a = request.args.get("a")
    b = request.args.get("b")
    if not a or not b:
        return jsonify({"error": "Specify ?a=...&b=..."}), 400
    rows = _load_csv(filename)
    grouped: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        if r.get("algorithm") in (a, b):
            grouped[r.get("test_id")][r.get("algorithm")] = r

    paired = []
    for tid, mapping in grouped.items():
        if a in mapping and b in mapping:
            paired.append({
                "test_id": tid,
                "n": mapping[a].get("n"),
                "a": {
                    "status": mapping[a].get("status"),
                    "time": mapping[a].get("time_sec"),
                    "memory": mapping[a].get("peak_memory_mb"),
                    "value": mapping[a].get("optimal_value"),
                },
                "b": {
                    "status": mapping[b].get("status"),
                    "time": mapping[b].get("time_sec"),
                    "memory": mapping[b].get("peak_memory_mb"),
                    "value": mapping[b].get("optimal_value"),
                },
            })
    return jsonify({"a": a, "b": b, "pairs": paired})
