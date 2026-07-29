from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.core.jobs import JobQueue

_MEMORY_SCHEDULES: dict[str, dict[str, Any]] = {}


class ScheduleStore:
    def __init__(self, queue: JobQueue | None = None) -> None:
        self.queue = queue or JobQueue()

    async def create(
        self,
        name: str,
        cron: str,
        job_type: str,
        payload: dict[str, Any] | None = None,
        *,
        actor: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        record = {
            "id": str(uuid4()),
            "name": name,
            "cron": normalize_cron(cron),
            "job_type": job_type,
            "payload": payload or {},
            "actor": actor,
            "organization_id": organization_id,
            "enabled": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_run_at": None,
            "next_run_at": next_cron_run(cron, now).isoformat(),
        }
        _MEMORY_SCHEDULES[str(record["id"])] = record
        return record

    async def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return sorted(
            _MEMORY_SCHEDULES.values(),
            key=lambda item: str(item.get("created_at", "")),
            reverse=True,
        )[:limit]

    async def get(self, schedule_id: str) -> dict[str, Any] | None:
        return _MEMORY_SCHEDULES.get(schedule_id)

    async def set_enabled(self, schedule_id: str, enabled: bool) -> dict[str, Any] | None:
        record = _MEMORY_SCHEDULES.get(schedule_id)
        if record is None:
            return None
        record["enabled"] = enabled
        record["updated_at"] = datetime.now(UTC).isoformat()
        return record

    async def enqueue_due(self, now: datetime | None = None) -> list[dict[str, Any]]:
        moment = now or datetime.now(UTC)
        jobs = []
        for record in list(_MEMORY_SCHEDULES.values()):
            next_run_raw = str(record.get("next_run_at") or "")
            if not record.get("enabled") or not next_run_raw:
                continue
            try:
                next_run = datetime.fromisoformat(next_run_raw)
            except ValueError:
                continue
            if next_run > moment:
                continue
            job = await self.queue.enqueue(
                str(record["job_type"]),
                dict(record.get("payload") or {}),
                actor=str(record.get("actor") or "scheduler"),
                organization_id=(
                    str(record["organization_id"]) if record.get("organization_id") else None
                ),
                scheduled_for=record["next_run_at"],
            )
            record["last_run_at"] = moment.isoformat()
            record["next_run_at"] = next_cron_run(str(record["cron"]), moment).isoformat()
            record["updated_at"] = moment.isoformat()
            jobs.append(job)
        return jobs


def normalize_cron(expression: str) -> str:
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError("Cron expressions must use five fields: minute hour day month weekday.")
    for value, minimum, maximum in zip(parts, [0, 0, 1, 1, 0], [59, 23, 31, 12, 6], strict=True):
        _allowed_values(value, minimum, maximum)
    return " ".join(parts)


def next_cron_run(expression: str, after: datetime | None = None) -> datetime:
    cron = normalize_cron(expression)
    minute_values, hour_values, day_values, month_values, weekday_values = [
        _allowed_values(value, minimum, maximum)
        for value, minimum, maximum in zip(
            cron.split(),
            [0, 0, 1, 1, 0],
            [59, 23, 31, 12, 6],
            strict=True,
        )
    ]
    cursor = (after or datetime.now(UTC)).replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _attempt in range(525600):
        if (
            cursor.minute in minute_values
            and cursor.hour in hour_values
            and cursor.day in day_values
            and cursor.month in month_values
            and ((cursor.weekday() + 1) % 7) in weekday_values
        ):
            return cursor
        cursor += timedelta(minutes=1)
    raise ValueError("Cron expression did not produce a run time within one year.")


def _allowed_values(field: str, minimum: int, maximum: int) -> set[int]:
    values: set[int] = set()
    for part in field.split(","):
        values.update(_part_values(part.strip(), minimum, maximum))
    if not values:
        raise ValueError("Cron field does not contain any values.")
    return values


def _part_values(part: str, minimum: int, maximum: int) -> set[int]:
    if part == "*":
        return set(range(minimum, maximum + 1))
    if part.startswith("*/"):
        step = int(part[2:])
        if step <= 0:
            raise ValueError("Cron step must be positive.")
        return set(range(minimum, maximum + 1, step))
    if "-" in part:
        start, end = [int(item) for item in part.split("-", 1)]
        if start < minimum or end > maximum or start > end:
            raise ValueError("Cron range is outside the supported bounds.")
        return set(range(start, end + 1))
    value = int(part)
    if value < minimum or value > maximum:
        raise ValueError("Cron value is outside the supported bounds.")
    return {value}
