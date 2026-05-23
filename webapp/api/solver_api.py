"""API endpoints for running a single algorithm on an instance live with timeout."""

from __future__ import annotations

import json
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context

bp = Blueprint("solver", __name__)

DEFAULT_TIMEOUT_SEC = 10


def _build_algo_map():
    from benchmark.runner import get_algorithm_registry
    return {spec.name: spec for spec in get_algorithm_registry()}


def _load_payload(instance_id: str, custom: Dict[str, Any]) -> Dict[str, Any]:
    if instance_id:
        path = Path(current_app.config["DATA_RAW_DIR"]) / f"{instance_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Instance not found: {instance_id}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if not custom:
        raise ValueError("Provide instance_id or instance payload")
    return custom


def _worker(payload: Dict[str, Any], algorithm_name: str, queue: mp.Queue) -> None:
    """Child-process entry point — runs the algorithm and pushes a serializable result."""
    import tracemalloc
    from benchmark.runner import _run_algorithm, _normalize_knapsack_type, get_algorithm_registry
    from src.models import Item, KnapsackInstance

    try:
        items = [
            Item(id=it.get("id", idx), weight=float(it["weight"]), value=float(it["value"]))
            for idx, it in enumerate(payload.get("items", []))
        ]
        instance = KnapsackInstance(items=items, capacity=float(payload["capacity"]))
        spec = {s.name: s for s in get_algorithm_registry()}[algorithm_name]
        try:
            algo = spec.factory(instance)
        except TypeError:
            algo = spec.factory()
            algo.instance = instance
        knapsack_type = getattr(algo, "target_knapsack_type", spec.target_knapsack_type)
        normalized = _normalize_knapsack_type(knapsack_type)

        tracemalloc.start()
        start = time.perf_counter()
        result = _run_algorithm(algo, instance, knapsack_type)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        selected, optimal_value = _extract_solution(algo, result, normalized)
        queue.put({
            "status": "SUCCESS",
            "knapsack_type": normalized,
            "time_sec": round(elapsed, 6),
            "peak_memory_mb": round(peak / (1024 * 1024), 4),
            "optimal_value": optimal_value,
            "selected": selected,
            "n": len(instance.items),
            "capacity": instance.capacity,
        })
    except Exception as exc:  # pylint: disable=broad-except
        queue.put({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"})


def _extract_solution(algo, result, normalized) -> tuple[List[Dict[str, Any]], float]:
    selected: List[Dict[str, Any]] = []
    optimal_value: float = 0.0

    if normalized == "fractional":
        for item, frac in getattr(algo, "fractional_selected_items", []) or []:
            selected.append({"id": item.id, "weight": item.weight, "value": item.value, "fraction": frac})
        optimal_value = float(getattr(algo, "fractional_best_value", 0.0))
    elif normalized == "unbounded":
        for item, qty in getattr(algo, "unbounded_selected_items", []) or []:
            selected.append({"id": item.id, "weight": item.weight, "value": item.value, "quantity": qty})
        optimal_value = float(getattr(algo, "unbounded_best_value", 0.0))
    else:
        items = getattr(algo, "zero_one_selected_items", None) or getattr(algo, "selected_items", []) or []
        for item in items:
            selected.append({"id": item.id, "weight": item.weight, "value": item.value})
        optimal_value = float(
            getattr(algo, "zero_one_best_value", 0.0) or getattr(algo, "best_value", 0.0)
        )

    if optimal_value == 0 and isinstance(result, (int, float)):
        optimal_value = float(result)
    return selected, optimal_value


def _execute_with_timeout(payload: Dict[str, Any], algorithm_name: str, timeout_sec: float) -> Dict[str, Any]:
    """Run a single algorithm in a worker process with a time budget."""
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_worker, args=(payload, algorithm_name, queue))
    proc.daemon = True
    proc.start()
    proc.join(timeout=timeout_sec)

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=2)
        if proc.is_alive():
            proc.kill()
            proc.join()
        return {
            "status": "TIMEOUT",
            "error": f"Algorithm exceeded {timeout_sec}s budget",
            "time_sec": timeout_sec,
            "peak_memory_mb": 0.0,
            "optimal_value": 0.0,
            "selected": [],
            "knapsack_type": None,
            "n": len(payload.get("items", [])),
            "capacity": payload.get("capacity"),
        }

    if queue.empty():
        return {"status": "ERROR", "error": "Worker process exited without result",
                "time_sec": 0, "peak_memory_mb": 0, "optimal_value": 0, "selected": [],
                "knapsack_type": None,
                "n": len(payload.get("items", [])), "capacity": payload.get("capacity")}

    result = queue.get()
    # Ensure shape consistency
    result.setdefault("time_sec", 0)
    result.setdefault("peak_memory_mb", 0)
    result.setdefault("optimal_value", 0)
    result.setdefault("selected", [])
    result.setdefault("knapsack_type", None)
    result.setdefault("n", len(payload.get("items", [])))
    result.setdefault("capacity", payload.get("capacity"))
    return result


@bp.route("/run", methods=["POST"])
def run():
    body = request.get_json(force=True, silent=True) or {}
    algorithm_name = body.get("algorithm")
    instance_id = body.get("instance_id")
    custom = body.get("instance")
    timeout_sec = float(body.get("timeout", DEFAULT_TIMEOUT_SEC) or DEFAULT_TIMEOUT_SEC)
    timeout_sec = max(0.5, min(timeout_sec, 3600.0))  # clamp 1h

    algo_map = _build_algo_map()
    if algorithm_name not in algo_map:
        return jsonify({"error": f"Unknown algorithm: {algorithm_name}"}), 400

    try:
        payload = _load_payload(instance_id, custom)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": f"Bad instance payload: {exc}"}), 400

    result = _execute_with_timeout(payload, algorithm_name, timeout_sec)
    result["algorithm"] = algorithm_name
    result["instance_id"] = instance_id or "custom"
    result["timeout_budget_sec"] = timeout_sec
    return jsonify(result)


@bp.route("/run-stream", methods=["POST"])
def run_stream():
    """Stream multi-algorithm results as newline-delimited JSON.

    Emits events:
      {"event":"start","total":N,"algorithms":[...],"n":..,"capacity":..}
      {"event":"algo-start","algorithm":"X","index":i}
      {"event":"tick","algorithm":"X","elapsed":1.2}    # while running
      {"event":"algo-done","algorithm":"X","result":{...}}
      {"event":"end","results":[...]}
    """
    body = request.get_json(force=True, silent=True) or {}
    algorithms = body.get("algorithms") or []
    instance_id = body.get("instance_id")
    custom = body.get("instance")
    timeout_sec = float(body.get("timeout", DEFAULT_TIMEOUT_SEC) or DEFAULT_TIMEOUT_SEC)
    timeout_sec = max(0.5, min(timeout_sec, 3600.0))

    algo_map = _build_algo_map()
    try:
        payload = _load_payload(instance_id, custom)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400

    def generate():
        import json as _json
        yield _json.dumps({
            "event": "start",
            "total": len(algorithms),
            "algorithms": algorithms,
            "n": len(payload.get("items", [])),
            "capacity": payload.get("capacity"),
            "timeout_budget_sec": timeout_sec,
        }) + "\n"

        collected = []
        for idx, name in enumerate(algorithms):
            yield _json.dumps({"event": "algo-start", "algorithm": name, "index": idx}) + "\n"

            if name not in algo_map:
                res = {"status": "ERROR", "error": "Unknown algorithm",
                       "time_sec": 0, "peak_memory_mb": 0, "optimal_value": 0, "selected": []}
                res["algorithm"] = name
                collected.append(res)
                yield _json.dumps({"event": "algo-done", "algorithm": name, "result": res}) + "\n"
                continue

            queue: mp.Queue = mp.Queue()
            proc = mp.Process(target=_worker, args=(payload, name, queue))
            proc.daemon = True
            proc.start()
            start = time.perf_counter()

            # Tick loop — emit elapsed every ~250ms until process exits or timeout
            tick_interval = 0.25
            done = False
            while True:
                elapsed = time.perf_counter() - start
                if not proc.is_alive():
                    done = True
                    break
                if elapsed >= timeout_sec:
                    break
                proc.join(timeout=tick_interval)
                yield _json.dumps({"event": "tick", "algorithm": name, "elapsed": round(elapsed + tick_interval, 2)}) + "\n"

            if not done and proc.is_alive():
                proc.terminate()
                proc.join(timeout=2)
                if proc.is_alive():
                    proc.kill()
                    proc.join()
                res = {
                    "status": "TIMEOUT",
                    "error": f"Exceeded {timeout_sec}s budget",
                    "time_sec": timeout_sec,
                    "peak_memory_mb": 0,
                    "optimal_value": 0,
                    "selected": [],
                    "knapsack_type": None,
                    "n": len(payload.get("items", [])),
                    "capacity": payload.get("capacity"),
                }
            elif queue.empty():
                res = {"status": "ERROR", "error": "Worker process exited without result",
                       "time_sec": 0, "peak_memory_mb": 0, "optimal_value": 0, "selected": [],
                       "knapsack_type": None,
                       "n": len(payload.get("items", [])),
                       "capacity": payload.get("capacity")}
            else:
                res = queue.get()
            res["algorithm"] = name
            res.setdefault("n", len(payload.get("items", [])))
            res.setdefault("capacity", payload.get("capacity"))
            collected.append(res)
            yield _json.dumps({"event": "algo-done", "algorithm": name, "result": res}) + "\n"

        yield _json.dumps({"event": "end", "results": collected,
                           "instance_id": instance_id or "custom"}) + "\n"

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")


@bp.route("/run-multi", methods=["POST"])
def run_multi():
    """Run multiple algorithms sequentially on the same instance."""
    body = request.get_json(force=True, silent=True) or {}
    algorithms = body.get("algorithms") or []
    instance_id = body.get("instance_id")
    custom = body.get("instance")
    timeout_sec = float(body.get("timeout", DEFAULT_TIMEOUT_SEC) or DEFAULT_TIMEOUT_SEC)
    timeout_sec = max(0.5, min(timeout_sec, 3600.0))

    algo_map = _build_algo_map()
    try:
        payload = _load_payload(instance_id, custom)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": f"Bad instance payload: {exc}"}), 400

    results = []
    for name in algorithms:
        if name not in algo_map:
            results.append({"algorithm": name, "status": "ERROR", "error": "Unknown algorithm",
                            "time_sec": 0, "peak_memory_mb": 0, "optimal_value": 0, "selected": []})
            continue
        res = _execute_with_timeout(payload, name, timeout_sec)
        res["algorithm"] = name
        results.append(res)

    return jsonify({
        "instance_id": instance_id or "custom",
        "results": results,
        "n": len(payload.get("items", [])),
        "capacity": payload.get("capacity"),
        "timeout_budget_sec": timeout_sec,
    })
