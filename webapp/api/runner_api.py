"""API endpoints to trigger benchmark/generator jobs as background subprocesses."""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("runner", __name__)

_JOBS: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.Lock()


def _root() -> Path:
    return Path(current_app.config["ROOT_DIR"])


def _new_job(kind: str, cmd, cwd: Path) -> str:
    job_id = uuid.uuid4().hex[:10]
    log_path = cwd / "results" / "csv" / f"job_{kind}_{job_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    with _LOCK:
        _JOBS[job_id] = {
            "id": job_id,
            "kind": kind,
            "cmd": cmd,
            "pid": proc.pid,
            "log": str(log_path),
            "started_at": datetime.utcnow().isoformat(),
            "process": proc,
            "log_file": log_file,
        }
    return job_id


@bp.route("/jobs", methods=["GET"])
def list_jobs():
    with _LOCK:
        snapshot = []
        for job_id, job in _JOBS.items():
            proc = job["process"]
            poll = proc.poll()
            snapshot.append({
                "id": job_id,
                "kind": job["kind"],
                "pid": job["pid"],
                "running": poll is None,
                "exit_code": poll,
                "started_at": job["started_at"],
                "log": job["log"],
                "cmd": job["cmd"],
            })
    return jsonify(snapshot)


_TQDM_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*\[(\d{2}:\d{2}(?::\d{2})?)<(\d{2}:\d{2}(?::\d{2})?|\?)")


def _parse_tqdm(content: str) -> Dict[str, Any]:
    """Find the last tqdm-style progress line and extract current/total/eta."""
    last = None
    for chunk in content.replace("\r", "\n").splitlines()[-50:]:
        m = _TQDM_RE.search(chunk)
        if m:
            last = m
    if not last:
        return {}
    current, total = int(last.group(1)), int(last.group(2))
    return {
        "current": current,
        "total": total,
        "percent": round(100.0 * current / total, 1) if total else 0,
        "elapsed": last.group(3),
        "eta": last.group(4),
    }


@bp.route("/jobs/<job_id>/log", methods=["GET"])
def job_log(job_id: str):
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    log_path = Path(job["log"])
    if not log_path.exists():
        return jsonify({"content": "", "running": job["process"].poll() is None})
    content = log_path.read_text(encoding="utf-8", errors="ignore")
    progress = _parse_tqdm(content)
    tail = (request.args.get("tail") or "").lower() in ("1", "true", "yes")
    if tail and len(content) > 20000:
        content = content[-20000:]
    return jsonify({
        "content": content,
        "running": job["process"].poll() is None,
        "exit_code": job["process"].poll(),
        "progress": progress,
    })


@bp.route("/jobs/<job_id>", methods=["DELETE"])
def stop_job(job_id: str):
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    proc = job["process"]
    if proc.poll() is None:
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
    return jsonify({"stopped": True})


@bp.route("/benchmark", methods=["POST"])
def start_benchmark():
    body = request.get_json(force=True, silent=True) or {}
    timeout = int(body.get("timeout", 5) or 5)
    limit = int(body.get("limit", 0) or 0)
    output_name = body.get("output", f"benchmark_results_t{timeout}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")

    root = _root()
    output_path = root / "results" / "csv" / output_name
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "benchmark.runner",
        "--timeout",
        str(timeout),
        "--output",
        str(output_path),
    ]
    if limit > 0:
        cmd.extend(["--limit", str(limit)])

    job_id = _new_job("benchmark", cmd, root)
    return jsonify({"job_id": job_id, "output": str(output_path)})


@bp.route("/generator", methods=["POST"])
def start_generator():
    body = request.get_json(force=True, silent=True) or {}
    seed = int(body.get("seed", 42) or 42)

    root = _root()
    cmd = [sys.executable, "-u", str(root / "data" / "generator.py"), "--seed", str(seed)]
    job_id = _new_job("generator", cmd, root)
    return jsonify({"job_id": job_id})


@bp.route("/quality", methods=["POST"])
def start_quality():
    root = _root()
    cmd = [sys.executable, "-u", str(root / "data" / "quality.py")]
    job_id = _new_job("quality", cmd, root)
    return jsonify({"job_id": job_id})
