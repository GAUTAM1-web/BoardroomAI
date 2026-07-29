from __future__ import annotations

import sys
import types
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest

from app.core.config import Settings
from app.core.jobs import JobQueue
from app.core.monitoring import record_request, request_metrics
from app.core.plugins import plugin_manifest
from app.core.recovery import recovery_plan
from app.core.scheduler import ScheduleStore, next_cron_run, normalize_cron


def _settings() -> Settings:
    return cast(
        Settings,
        SimpleNamespace(
            job_queue_backend="memory",
            redis_url="",
            job_max_attempts=2,
            shared_cache_ttl_seconds=60,
            app_env="production",
            deployment_target="auto",
            cors_origins=[],
            database_url="postgresql+asyncpg://user:password@db/boardroom",
            qdrant_url="https://qdrant.example.com",
            public_api_url="https://api.example.com",
            public_frontend_url="https://app.example.com",
            frontend_base_url="",
            session_secret="super-secret-session-value-32-plus",
            ai_provider="local",
            openai_api_key="sk-hidden",
            anthropic_api_key="",
            gemini_api_key="",
            distributed_sessions_enabled=True,
            csrf_protection_enabled=True,
            security_headers_enabled=True,
        ),
    )


@pytest.mark.asyncio
async def test_job_queue_tracks_cancel_retry_and_dead_letter() -> None:
    queue = JobQueue(_settings())
    job = await queue.enqueue("report_generation", {"meeting_id": "m1"}, actor="administrator")

    canceled = await queue.cancel(str(job["id"]))
    assert canceled is not None
    assert canceled["status"] == "canceled"

    retried = await queue.retry(str(job["id"]))
    assert retried is not None
    assert retried["status"] == "queued"

    await queue.mark_failed(str(job["id"]), "first failure")
    failed = await queue.mark_failed(str(job["id"]), "second failure")
    assert failed is not None
    assert failed["status"] == "dead_letter"

    stats = await queue.stats()
    assert stats["counts"]["dead_letter"] >= 1
    assert "analytics_refresh" in stats["supported_job_types"]


@pytest.mark.asyncio
async def test_scheduler_accepts_cron_and_enqueues_due_jobs() -> None:
    queue = JobQueue(_settings())
    store = ScheduleStore(queue)
    schedule = await store.create(
        "Daily executive brief",
        "0 9 * * *",
        "scheduled_workflow",
        {"workflow": "daily_brief"},
    )

    assert normalize_cron(schedule["cron"]) == "0 9 * * *"
    assert next_cron_run("0 9 * * *", datetime(2026, 7, 29, 8, 59, tzinfo=UTC)).hour == 9

    schedule["next_run_at"] = datetime(2026, 7, 29, 8, 0, tzinfo=UTC).isoformat()
    jobs = await store.enqueue_due(datetime(2026, 7, 29, 8, 1, tzinfo=UTC))

    assert len(jobs) == 1
    assert jobs[0]["type"] == "scheduled_workflow"


def test_plugin_manifest_discovers_registered_module() -> None:
    module = types.ModuleType("boardroom_test_plugin")

    class TestPlugin:
        name = "Test Analytics"
        plugin_type = "analytics"

        def capabilities(self) -> dict[str, object]:
            return {"metrics": ["decision_quality"]}

    module.register = lambda: TestPlugin()  # type: ignore[attr-defined]
    sys.modules["boardroom_test_plugin"] = module

    manifest = plugin_manifest("boardroom_test_plugin")

    assert manifest["registered_count"] == 1
    assert manifest["plugins"][0]["type"] == "analytics"


def test_recovery_plan_does_not_expose_secret_values() -> None:
    plan = recovery_plan(_settings())
    serialized = str(plan)

    assert "super-secret-session-value-32-plus" not in serialized
    assert "sk-hidden" not in serialized
    assert "pg_restore" in plan["backup_commands"]["postgres_restore"]


def test_monitoring_request_metrics_track_latency() -> None:
    before = request_metrics()["request_count"]
    record_request(200, 12.5)
    metrics = request_metrics()

    assert metrics["request_count"] == before + 1
    assert metrics["latency_ms"]["max"] >= 12.5
