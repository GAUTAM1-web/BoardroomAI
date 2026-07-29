from __future__ import annotations

import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import Settings  # noqa: E402
from app.core.jobs import JobQueue  # noqa: E402
from app.core.scheduler import next_cron_run  # noqa: E402
from app.main import create_app  # noqa: E402


def measure(name: str, operation: Callable[[], Any], iterations: int = 25) -> dict[str, Any]:
    samples: list[float] = []
    last_result: Any = None
    for _ in range(iterations):
        started = time.perf_counter()
        last_result = operation()
        samples.append((time.perf_counter() - started) * 1000)
    return {
        "name": name,
        "iterations": iterations,
        "average_ms": round(statistics.fmean(samples), 3),
        "p95_ms": round(sorted(samples)[min(len(samples) - 1, int(len(samples) * 0.95))], 3),
        "max_ms": round(max(samples), 3),
        "sample_result": summarize(last_result),
    }


async def measure_job_enqueue(iterations: int = 25) -> dict[str, Any]:
    settings = Settings(job_queue_backend="memory", redis_url="")
    queue = JobQueue(settings)
    samples: list[float] = []
    last_job: dict[str, Any] | None = None
    for _ in range(iterations):
        started = time.perf_counter()
        last_job = await queue.enqueue("analytics_refresh", {"benchmark": True}, actor="benchmark")
        samples.append((time.perf_counter() - started) * 1000)
    return {
        "name": "memory_job_enqueue",
        "iterations": iterations,
        "average_ms": round(statistics.fmean(samples), 3),
        "p95_ms": round(sorted(samples)[min(len(samples) - 1, int(len(samples) * 0.95))], 3),
        "max_ms": round(max(samples), 3),
        "sample_result": {"status": last_job["status"] if last_job else "missing"},
    }


def summarize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: value[key] for key in list(value)[:5]}
    return str(value)[:120]


async def main() -> None:
    app = create_app()
    results = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmarks": [
            measure("openapi_schema_generation", app.openapi, iterations=10),
            measure("cron_next_run", lambda: next_cron_run("*/15 * * * *").isoformat()),
            await measure_job_enqueue(),
        ],
    }
    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "performance-rc6.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"wrote {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
