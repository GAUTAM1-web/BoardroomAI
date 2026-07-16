from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class EnterpriseOrganizationRecord(Base):
    __tablename__ = "enterprise_organizations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    default_locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnterpriseDepartmentRecord(Base):
    __tablename__ = "enterprise_departments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnterpriseTeamRecord(Base):
    __tablename__ = "enterprise_teams"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnterpriseUserRecord(Base):
    __tablename__ = "enterprise_users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(240), nullable=False, unique=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnterpriseMembershipRecord(Base):
    __tablename__ = "enterprise_memberships"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(60), nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MeetingCollaboratorRecord(Base):
    __tablename__ = "meeting_collaborators"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("board_meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="joined")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReportCommentRecord(Base):
    __tablename__ = "report_comments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("board_meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_comment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("report_comments.id", ondelete="CASCADE"),
        nullable=True,
    )
    author_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ApprovalWorkflowRecord(Base):
    __tablename__ = "approval_workflows"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    board_meeting_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("board_meetings.id", ondelete="CASCADE"),
        nullable=True,
    )
    business_analysis_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_analyses.id", ondelete="CASCADE"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApprovalStepRecord(Base):
    __tablename__ = "approval_steps"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("approval_workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    approver_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(60), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EnterpriseTaskRecord(Base):
    __tablename__ = "enterprise_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    board_meeting_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("board_meetings.id", ondelete="CASCADE"),
        nullable=True,
    )
    business_analysis_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_analyses.id", ondelete="CASCADE"),
        nullable=True,
    )
    assignee_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CalendarEventRecord(Base):
    __tablename__ = "calendar_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    related_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnterpriseNotificationRecord(Base):
    __tablename__ = "enterprise_notifications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="CASCADE"),
        nullable=True,
    )
    channel: Mapped[str] = mapped_column(String(40), nullable=False, default="in_app")
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="unread")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KnowledgeItemRecord(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    item_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReportTemplateRecord(Base):
    __tablename__ = "report_templates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    sections: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StartupBriefRecord(Base):
    __tablename__ = "startup_briefs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    startup_idea: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(String(160), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    timeline_months: Mapped[int] = mapped_column(Integer, nullable=False)
    competitors: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    funding_stage: Mapped[str] = mapped_column(String(80), nullable=False)
    business_model: Mapped[str] = mapped_column(String(120), nullable=False)
    meeting_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="full_board")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    meetings: Mapped[list[BoardMeetingRecord]] = relationship(
        back_populates="startup_brief",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BoardMeetingRecord(Base):
    __tablename__ = "board_meetings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    startup_brief_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("startup_briefs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consensus_reached: Mapped[bool] = mapped_column(Boolean, nullable=False)
    aggregate_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    decision: Mapped[str] = mapped_column(String(80), nullable=False)
    current_phase: Mapped[str | None] = mapped_column(String(80), nullable=True)
    assessment: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    startup_brief: Mapped[StartupBriefRecord] = relationship(back_populates="meetings")
    executives: Mapped[list[ExecutiveAgentRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    turns: Mapped[list[MeetingTurnRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    votes: Mapped[list[BoardVoteRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    vote_events: Mapped[list[VoteEventRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    confidence_events: Mapped[list[ConfidenceEventRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    stream_events: Mapped[list[MeetingEventRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports: Mapped[list[FinalReportRecord]] = relationship(
        back_populates="board_meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ExecutiveAgentRecord(Base):
    __tablename__ = "executive_agents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    charter: Mapped[str] = mapped_column(Text, nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    goals: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    risk_focus: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="executives")


class MeetingTurnRecord(Base):
    __tablename__ = "meeting_turns"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_role: Mapped[str] = mapped_column(String(120), nullable=False)
    turn_type: Mapped[str] = mapped_column(String(40), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True)
    stance: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    concerns: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    reasoning: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    memory_references: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="turns")


class BoardVoteRecord(Base):
    __tablename__ = "board_votes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    vote: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="votes")


class VoteEventRecord(Base):
    __tablename__ = "vote_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    previous_vote: Mapped[str | None] = mapped_column(String(60), nullable=True)
    vote: Mapped[str] = mapped_column(String(60), nullable=False)
    changed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="vote_events")


class ConfidenceEventRecord(Base):
    __tablename__ = "confidence_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    previous_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    delta: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="confidence_events")


class MeetingEventRecord(Base):
    __tablename__ = "meeting_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="stream_events")


class FinalReportRecord(Base):
    __tablename__ = "final_reports"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    board_meeting_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("board_meetings.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    decision: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    board_meeting: Mapped[BoardMeetingRecord] = relationship(back_populates="reports")
    sections: Mapped[list[ReportSectionRecord]] = relationship(
        back_populates="final_report",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ReportSectionRecord(Base):
    __tablename__ = "report_sections"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    final_report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("final_reports.id", ondelete="CASCADE"), nullable=False
    )
    section_key: Mapped[str] = mapped_column(String(120), nullable=False)
    section_title: Mapped[str] = mapped_column(String(160), nullable=False)
    content: Mapped[dict[str, object] | list[object]] = mapped_column(JSONB, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    final_report: Mapped[FinalReportRecord] = relationship(back_populates="sections")


class BusinessAnalysisRecord(Base):
    __tablename__ = "business_analyses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    workflow_type: Mapped[str] = mapped_column(String(60), nullable=False)
    business_idea: Mapped[str] = mapped_column(Text, nullable=False)
    business_category: Mapped[str] = mapped_column(String(160), nullable=False)
    location_label: Mapped[str] = mapped_column(String(300), nullable=False)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    data_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_label: Mapped[str] = mapped_column(String(220), nullable=False)
    recommendation_label: Mapped[str] = mapped_column(String(120), nullable=False)
    opportunity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_confidence: Mapped[str] = mapped_column(String(40), nullable=False)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evidence_records: Mapped[list[BusinessEvidenceRecord]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    saved_suppliers: Mapped[list[SavedSupplierRecord]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    validation_tasks: Mapped[list[BusinessValidationTaskRecord]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    performance_entries: Mapped[list[BusinessPerformanceEntryRecord]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BusinessEvidenceRecord(Base):
    __tablename__ = "business_evidence_records"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(220), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(120), nullable=False)
    retrieval_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    value: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[str] = mapped_column(String(40), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(80), nullable=False)
    freshness: Mapped[str] = mapped_column(String(80), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    analysis: Mapped[BusinessAnalysisRecord] = relationship(back_populates="evidence_records")


class SavedSupplierRecord(Base):
    __tablename__ = "saved_suppliers"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str | None] = mapped_column(String(160), nullable=True)
    location_label: Mapped[str | None] = mapped_column(String(220), nullable=True)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(80), nullable=False)
    contact_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_preferred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supplier_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    analysis: Mapped[BusinessAnalysisRecord] = relationship(back_populates="saved_suppliers")


class BusinessValidationTaskRecord(Base):
    __tablename__ = "business_validation_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    task: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cost: Mapped[str | None] = mapped_column(String(160), nullable=True)
    expected_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(160), nullable=True)
    effect_on_confidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    analysis: Mapped[BusinessAnalysisRecord] = relationship(back_populates="validation_tasks")


class BusinessPerformanceEntryRecord(Base):
    __tablename__ = "business_performance_entries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_label: Mapped[str] = mapped_column(String(120), nullable=False)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    expenses: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    customers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transactions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    performance_data: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    analysis: Mapped[BusinessAnalysisRecord] = relationship(back_populates="performance_entries")
