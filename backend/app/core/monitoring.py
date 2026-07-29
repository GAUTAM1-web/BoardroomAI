from __future__ import annotations

import os
import platform
import statistics
import time
import tracemalloc
from collections import deque
from datetime import UTC, datetime
from typing import Any

_STARTED_AT = datetime.now(UTC)
_REQUEST_COUNT = 0
_STATUS_COUNTS: dict[str, int] = {}
_LATENCY_MS: deque[float] = deque(maxlen=1000)
_ACTIVE_REQUESTS = 0

tracemalloc.start()


def mark_request_started() -> None:
    global _ACTIVE_REQUESTS
    _ACTIVE_REQUESTS += 1


def record_request(status_code: int, duration_ms: float) -> None:
    global _ACTIVE_REQUESTS, _REQUEST_COUNT
    _REQUEST_COUNT += 1
    _ACTIVE_REQUESTS = max(0, _ACTIVE_REQUESTS - 1)
    _LATENCY_MS.append(duration_ms)
    status_group = f"{status_code // 100}xx"
    _STATUS_COUNTS[status_group] = _STATUS_COUNTS.get(status_group, 0) + 1


def record_request_exception(duration_ms: float) -> None:
    record_request(500, duration_ms)


def request_metrics() -> dict[str, Any]:
    latencies = list(_LATENCY_MS)
    return {
        "started_at": _STARTED_AT.isoformat(),
        "uptime_seconds": round((datetime.now(UTC) - _STARTED_AT).total_seconds(), 3),
        "request_count": _REQUEST_COUNT,
        "active_requests": _ACTIVE_REQUESTS,
        "status_counts": dict(_STATUS_COUNTS),
        "latency_ms": {
            "count": len(latencies),
            "average": round(statistics.fmean(latencies), 2) if latencies else 0,
            "p95": _percentile(latencies, 0.95),
            "max": round(max(latencies), 2) if latencies else 0,
        },
    }


def process_metrics() -> dict[str, Any]:
    current, peak = tracemalloc.get_traced_memory()
    snapshot = {
        "pid": os.getpid(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "process_time_seconds": round(time.process_time(), 3),
        "memory_bytes": {
            "tracemalloc_current": current,
            "tracemalloc_peak": peak,
        },
        "cpu_percent": None,
        "rss_bytes": None,
    }
    try:
        import psutil  # type: ignore[import-not-found]

        process = psutil.Process(os.getpid())
        snapshot["cpu_percent"] = process.cpu_percent(interval=0.0)
        snapshot["rss_bytes"] = process.memory_info().rss
    except Exception:
        snapshot["psutil"] = "not_available"
    return snapshot


def monitoring_snapshot(
    *,
    dependencies: dict[str, object],
    providers: dict[str, object],
    jobs: dict[str, object],
    cache: dict[str, object],
    active_users: int,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "api": request_metrics(),
        "process": process_metrics(),
        "active_users": active_users,
        "dependencies": dependencies,
        "providers": providers,
        "jobs": jobs,
        "cache": cache,
    }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * percentile)))
    return round(ordered[index], 2)
