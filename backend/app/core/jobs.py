from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import redis.asyncio as redis

from app.core.config import Settings, get_settings

JobStatus = str
JOB_STATUSES: set[JobStatus] = {
    "queued",
    "running",
    "completed",
    "failed",
    "canceled",
    "dead_letter",
}
QUEUE_KEY = "boardroomai:jobs:queued"
DEAD_LETTER_KEY = "boardroomai:jobs:dead_letter"
LIST_KEY = "boardroomai:jobs:list"
_MEMORY_JOBS: dict[str, dict[str, Any]] = {}
_MEMORY_QUEUE: list[str] = []
_MEMORY_DEAD_LETTER: list[str] = []


class JobQueue:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: redis.Redis | None = None

    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any] | None = None,
        *,
        actor: str | None = None,
        organization_id: str | None = None,
        scheduled_for: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        record = {
            "id": str(uuid4()),
            "type": job_type,
            "status": "queued",
            "payload": payload or {},
            "actor": actor,
            "organization_id": organization_id,
            "attempts": 0,
            "max_attempts": self.settings.job_max_attempts,
            "progress": 0,
            "scheduled_for": scheduled_for,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "finished_at": None,
            "error": None,
            "cancel_requested": False,
        }
        await self._save(record)
        await self._push_queue(str(record["id"]))
        return record

    async def get(self, job_id: str) -> dict[str, Any] | None:
        client = self._redis_client()
        if client is not None:
            try:
                raw = await client.get(_job_key(job_id))
                if raw:
                    data = json.loads(raw)
                    return data if isinstance(data, dict) else None
            except Exception:
                pass
        return _MEMORY_JOBS.get(job_id)

    async def list(self, limit: int = 50) -> list[dict[str, Any]]:
        client = self._redis_client()
        if client is not None:
            try:
                ids = await client.lrange(LIST_KEY, 0, max(0, limit - 1))
                records = [await self.get(job_id) for job_id in ids]
                return [record for record in records if record is not None]
            except Exception:
                pass
        return sorted(
            _MEMORY_JOBS.values(),
            key=lambda item: str(item.get("created_at", "")),
            reverse=True,
        )[:limit]

    async def cancel(self, job_id: str) -> dict[str, Any] | None:
        record = await self.get(job_id)
        if record is None:
            return None
        if record["status"] in {"completed", "failed", "dead_letter"}:
            return record
        record["status"] = "canceled"
        record["cancel_requested"] = True
        record["updated_at"] = datetime.now(UTC).isoformat()
        await self._save(record)
        return record

    async def retry(self, job_id: str) -> dict[str, Any] | None:
        record = await self.get(job_id)
        if record is None:
            return None
        if record["status"] not in {"failed", "dead_letter", "canceled"}:
            return record
        record["status"] = "queued"
        record["error"] = None
        record["cancel_requested"] = False
        record["updated_at"] = datetime.now(UTC).isoformat()
        await self._save(record)
        await self._push_queue(job_id)
        return record

    async def mark_failed(self, job_id: str, error: str) -> dict[str, Any] | None:
        record = await self.get(job_id)
        if record is None:
            return None
        record["attempts"] = int(record.get("attempts") or 0) + 1
        record["error"] = error[:500]
        record["updated_at"] = datetime.now(UTC).isoformat()
        if int(record["attempts"]) >= int(record.get("max_attempts") or 1):
            record["status"] = "dead_letter"
            await self._push_dead_letter(job_id)
        else:
            record["status"] = "failed"
        await self._save(record)
        return record

    async def update_progress(
        self,
        job_id: str,
        progress: int,
        status: str | None = None,
    ) -> dict[str, Any] | None:
        record = await self.get(job_id)
        if record is None:
            return None
        record["progress"] = max(0, min(100, progress))
        if status in JOB_STATUSES:
            record["status"] = status
        record["updated_at"] = datetime.now(UTC).isoformat()
        if status == "running" and record.get("started_at") is None:
            record["started_at"] = record["updated_at"]
        if status in {"completed", "failed", "canceled", "dead_letter"}:
            record["finished_at"] = record["updated_at"]
        await self._save(record)
        return record

    async def stats(self) -> dict[str, Any]:
        records = await self.list(limit=500)
        counts = {status: 0 for status in sorted(JOB_STATUSES)}
        for record in records:
            status = str(record.get("status") or "queued")
            counts[status] = int(counts.get(status, 0)) + 1
        client = self._redis_client()
        redis_queue_size: int | None = None
        redis_dead_letter_size: int | None = None
        if client is not None:
            try:
                redis_queue_size = int(await client.llen(QUEUE_KEY))
                redis_dead_letter_size = int(await client.llen(DEAD_LETTER_KEY))
            except Exception:
                redis_queue_size = None
                redis_dead_letter_size = None
        return {
            "backend": "redis" if client is not None else "memory",
            "counts": counts,
            "queue_size": redis_queue_size if redis_queue_size is not None else len(_MEMORY_QUEUE),
            "dead_letter_size": (
                redis_dead_letter_size
                if redis_dead_letter_size is not None
                else len(_MEMORY_DEAD_LETTER)
            ),
            "supported_job_types": [
                "report_generation",
                "scheduled_workflow",
                "provider_sync",
                "document_processing",
                "email_delivery",
                "analytics_refresh",
                "scheduled_export",
            ],
        }

    async def health(self) -> dict[str, object]:
        client = self._redis_client()
        if client is None:
            return {"backend": "memory", "status": "ok"}
        try:
            await client.ping()
            return {"backend": "redis", "status": "ok"}
        except Exception as exc:
            return {"backend": "memory", "status": "degraded", "error": type(exc).__name__}

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _save(self, record: dict[str, Any]) -> None:
        _MEMORY_JOBS[str(record["id"])] = record
        client = self._redis_client()
        if client is None:
            return
        try:
            await client.set(_job_key(str(record["id"])), json.dumps(record, default=str))
            await client.lrem(LIST_KEY, 0, str(record["id"]))
            await client.lpush(LIST_KEY, str(record["id"]))
            await client.ltrim(LIST_KEY, 0, 999)
        except Exception:
            return

    async def _push_queue(self, job_id: str) -> None:
        if job_id not in _MEMORY_QUEUE:
            _MEMORY_QUEUE.append(job_id)
        client = self._redis_client()
        if client is None:
            return
        try:
            await client.rpush(QUEUE_KEY, job_id)
        except Exception:
            return

    async def _push_dead_letter(self, job_id: str) -> None:
        if job_id not in _MEMORY_DEAD_LETTER:
            _MEMORY_DEAD_LETTER.append(job_id)
        client = self._redis_client()
        if client is None:
            return
        try:
            await client.rpush(DEAD_LETTER_KEY, job_id)
        except Exception:
            return

    def _redis_client(self) -> redis.Redis | None:
        if self.settings.job_queue_backend.strip().lower() == "memory":
            return None
        if not self.settings.redis_url:
            return None
        if self._client is None:
            self._client = redis.from_url(self.settings.redis_url, decode_responses=True)
        return self._client


def _job_key(job_id: str) -> str:
    return f"boardroomai:jobs:{job_id}"
