from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=120)
    default_locale: str = Field(default="en", max_length=16)


class OrganizationListResponse(BaseModel):
    organizations: list[dict[str, Any]]


class OrganizationResponse(BaseModel):
    organization: dict[str, Any]


class EnterpriseDashboardResponse(BaseModel):
    organization: dict[str, Any]
    departments: list[dict[str, Any]]
    teams: list[dict[str, Any]]
    users: list[dict[str, Any]]
    recent_meetings: list[dict[str, Any]]
    pending_approvals: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    board_activity: list[dict[str, Any]]
    upcoming_reviews: list[dict[str, Any]]
    analytics: dict[str, Any]
    executive_dashboard: dict[str, Any]


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    section_key: str | None = Field(default=None, max_length=120)
    parent_comment_id: UUID | None = None
    mentions: list[str] = Field(default_factory=list, max_length=20)


class CommentResolveRequest(BaseModel):
    status: Literal["open", "resolved"] = "resolved"


class CommentsResponse(BaseModel):
    comments: list[dict[str, Any]]


class CollaboratorJoinRequest(BaseModel):
    user_email: str = Field(default="owner@boardroom.local", max_length=240)
    display_name: str = Field(default="Workspace Owner", max_length=160)
    role: str = Field(default="Manager", max_length=80)


class ApprovalCreateRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)
    steps: list[str] = Field(default_factory=lambda: ["Manager", "CEO"], max_length=8)
    business_analysis_id: UUID | None = None


class ApprovalDecisionRequest(BaseModel):
    status: Literal["approved", "rejected"]
    reason: str | None = Field(default=None, max_length=1000)


class ApprovalResponse(BaseModel):
    approval: dict[str, Any]


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=220)
    description: str | None = Field(default=None, max_length=2000)
    board_meeting_id: UUID | None = None
    business_analysis_id: UUID | None = None
    assignee_email: str | None = Field(default=None, max_length=240)
    due_at: str | None = None
    source: str = Field(default="manual", max_length=80)


class TaskUpdateRequest(BaseModel):
    status: Literal["open", "in_progress", "done", "blocked"] | None = None
    title: str | None = Field(default=None, max_length=220)
    description: str | None = Field(default=None, max_length=2000)
    due_at: str | None = None


class TaskResponse(BaseModel):
    task: dict[str, Any]


class TaskListResponse(BaseModel):
    tasks: list[dict[str, Any]]


class EnterpriseCollectionResponse(BaseModel):
    items: list[dict[str, Any]]


class EnterpriseAnalyticsResponse(BaseModel):
    analytics: dict[str, Any]
    executive_dashboard: dict[str, Any]


class AdminPanelResponse(BaseModel):
    users: list[dict[str, Any]]
    organizations: list[dict[str, Any]]
    api_keys: list[dict[str, Any]]
    providers: dict[str, Any]
    feature_flags: dict[str, bool]
    diagnostics: dict[str, Any]
    usage_statistics: dict[str, Any]
