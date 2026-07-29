from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    job_type: Literal[
        "report_generation",
        "scheduled_workflow",
        "provider_sync",
        "document_processing",
        "email_delivery",
        "analytics_refresh",
        "scheduled_export",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)
    organization_id: str | None = Field(default=None, max_length=120)


class JobResponse(BaseModel):
    job: dict[str, Any]


class JobListResponse(BaseModel):
    jobs: list[dict[str, Any]]
    stats: dict[str, Any]


class ScheduleCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    cron: str = Field(min_length=5, max_length=120)
    job_type: str = Field(min_length=2, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)
    organization_id: str | None = Field(default=None, max_length=120)


class ScheduleToggleRequest(BaseModel):
    enabled: bool


class ScheduleResponse(BaseModel):
    schedule: dict[str, Any]


class ScheduleListResponse(BaseModel):
    schedules: list[dict[str, Any]]
