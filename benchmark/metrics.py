"""Process-isolated profiling utilities for benchmark execution."""

from __future__ import annotations

import multiprocessing as mp
import time
import tracemalloc
from typing import Any, Callable, Tuple


STATUS_SUCCESS = "SUCCESS"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_OOM = "OOM"
STATUS_ERROR = "ERROR"


def _worker(func: Callable[..., Any], args: Tuple[Any, ...], queue: mp.Queue) -> None:
    """Worker entry point executed in a child process."""
    start = time.perf_counter()
    tracemalloc.start()
    status = STATUS_SUCCESS
    result: Any = None
    try:
        result = func(*args)
    except MemoryError:
        status = STATUS_OOM
    except Exception as exc:  # pragma: no cover - safety for unexpected failures
        status = STATUS_ERROR
        result = f"{type(exc).__name__}: {exc}"
    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.perf_counter() - start
        peak_mb = peak / (1024.0 * 1024.0)
        queue.put((status, result, elapsed, peak_mb))


def run_with_profiler(
    func: Callable[..., Any],
    args: Tuple[Any, ...],
    timeout_sec: int,
) -> Tuple[str, Any, float, float]:
    """Run a function in a child process with time and memory profiling.

    Returns:
        Tuple[str, Any, float, float]:
            (status, result, exec_time_sec, peak_memory_mb)
    """
    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_worker, args=(func, args, queue))
    process.daemon = True
    process.start()
    process.join(timeout=timeout_sec)

    if process.is_alive():
        process.terminate()
        process.join()
        return STATUS_TIMEOUT, None, float(timeout_sec), 0.0

    if queue.empty():
        return STATUS_ERROR, None, 0.0, 0.0

    status, result, exec_time, peak_mb = queue.get()
    return status, result, float(exec_time), float(peak_mb)
