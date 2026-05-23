"""API endpoints serving raw test instances and quality data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("data", __name__)


def _raw_dir() -> Path:
    return Path(current_app.config["DATA_RAW_DIR"])


@bp.route("/instances", methods=["GET"])
def list_instances():
    """List all available instance files (paginated)."""
    raw = _raw_dir()
    if not raw.exists():
        return jsonify({"items": [], "total": 0})

    q = (request.args.get("q") or "").lower()
    limit = int(request.args.get("limit", 200) or 200)
    offset = int(request.args.get("offset", 0) or 0)

    files = sorted(raw.glob("*.json"))
    filtered = [p for p in files if not q or q in p.name.lower()]
    sliced = filtered[offset:offset + limit]
    items = [{"id": p.stem, "name": p.name, "size": p.stat().st_size} for p in sliced]
    return jsonify({"items": items, "total": len(filtered), "offset": offset, "limit": limit})


@bp.route("/instance/<instance_id>", methods=["GET"])
def get_instance(instance_id: str):
    """Return the full JSON payload of a single instance."""
    raw = _raw_dir()
    candidate = raw / f"{instance_id}.json"
    if not candidate.exists():
        return jsonify({"error": "Instance not found"}), 404
    with candidate.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    payload["n"] = len(payload.get("items", []))
    return jsonify(payload)


@bp.route("/scenarios", methods=["GET"])
def scenarios():
    """Return benchmark scenarios configuration."""
    path = Path(current_app.config["SCENARIOS_FILE"])
    if not path.exists():
        return jsonify([])
    with path.open("r", encoding="utf-8") as handle:
        return jsonify(json.load(handle))


@bp.route("/algorithms", methods=["GET"])
def algorithms():
    """Return list of supported algorithms with metadata."""
    from benchmark.runner import get_algorithm_registry
    specs = get_algorithm_registry()
    return jsonify([
        {
            "name": s.name,
            "knapsack_type": s.target_knapsack_type,
            "description": _algorithm_description(s.name),
        }
        for s in specs
    ])


def _algorithm_description(name: str) -> str:
    return {
        "DP": "Dynamic Programming — quy hoạch động bảng O(n·W). Chính xác nhưng tốn bộ nhớ khi W lớn.",
        "DPUnbounded": "Dynamic Programming cho Unbounded Knapsack — mỗi vật phẩm lấy nhiều lần.",
        "BranchAndBound": "Nhánh cận với hàm chặn LP relaxation. Cân bằng giữa tốc độ và độ chính xác.",
        "Backtracking": "Quay lui vét cạn có cắt tỉa. Chậm với N lớn.",
        "Greedy01": "Tham lam 0/1 theo density (v/w). Nhanh, không tối ưu.",
        "GreedyFractional": "Tham lam phân số. Tối ưu cho Fractional Knapsack.",
        "PrimalSimplex": "Đơn hình nguyên thủy cho LP relaxation.",
        "DualSimplex": "Đơn hình đối ngẫu cho LP relaxation.",
        "SimplexBnB": "Simplex kết hợp Branch-and-Bound.",
        "GomoryCut": "Phương pháp cắt Gomory cho integer programming.",
    }.get(name, "Knapsack solver implementation.")


@bp.route("/quality-images", methods=["GET"])
def quality_images():
    quality_dir = Path(current_app.config["RESULTS_QUALITY_DIR"])
    plots_dir = Path(current_app.config["RESULTS_PLOTS_DIR"])
    images: List[Dict[str, Any]] = []
    for label, directory in (("quality", quality_dir), ("plots", plots_dir)):
        if not directory.exists():
            continue
        for img in sorted(directory.glob("*.png")):
            images.append({
                "category": label,
                "name": img.name,
                "url": f"/api/data/static-image/{label}/{img.name}",
            })
    return jsonify(images)


@bp.route("/random-instance", methods=["POST"])
def random_instance():
    """Generate a random knapsack instance on-the-fly using the project's generator."""
    import random
    body = request.get_json(force=True, silent=True) or {}
    n = max(2, min(int(body.get("n", 20) or 20), 5000))
    max_weight = max(1, min(int(body.get("max_weight", 100) or 100), 100000))
    capacity_ratio = float(body.get("capacity_ratio", 0.5) or 0.5)
    capacity_ratio = max(0.05, min(capacity_ratio, 0.95))
    pearson_r = float(body.get("pearson_r", 0.5) or 0.5)
    pearson_r = max(-0.95, min(pearson_r, 0.95))
    seed = body.get("seed")
    rng = random.Random(int(seed) if seed not in (None, "") else None)

    weights = [rng.randint(1, max_weight) for _ in range(n)]
    base_values = [rng.gauss(0, 1) for _ in range(n)]
    w_norm = [(w - sum(weights) / n) for w in weights]
    items = []
    for w, b in zip(weights, base_values):
        # Linear blend: rho * weight component + sqrt(1-rho^2) * independent noise
        noise = rng.gauss(0, 1)
        val = pearson_r * (w / max(max_weight, 1)) * 100 + ((1 - pearson_r ** 2) ** 0.5) * (noise * 30 + 50)
        val = max(1.0, val + 50.0)
        items.append({"weight": float(w), "value": round(val, 2)})
    total_weight = sum(it["weight"] for it in items)
    capacity = round(total_weight * capacity_ratio, 2)
    items = [{"id": i, **it} for i, it in enumerate(items)]
    return jsonify({
        "test_id": f"random_n{n}_w{max_weight}_cr{capacity_ratio:.2f}_pr{pearson_r:.2f}",
        "capacity": capacity,
        "items": items,
        "metadata": {
            "n": n, "max_weight": max_weight,
            "capacity_ratio_input": capacity_ratio,
            "target_pearson_r": pearson_r,
        },
    })


@bp.route("/static-image/<category>/<filename>", methods=["GET"])
def static_image(category: str, filename: str):
    from flask import send_from_directory
    if category == "quality":
        directory = current_app.config["RESULTS_QUALITY_DIR"]
    elif category == "plots":
        directory = current_app.config["RESULTS_PLOTS_DIR"]
    else:
        return ("not found", 404)
    return send_from_directory(directory, filename)
