from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    meetings: Mapped[list[BoardMeetingRecord]] = relationship(back_populates="startup_brief")


class BoardMeetingRecord(Base):
    __tablename__ = "board_meetings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    startup_brief_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("startup_briefs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
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
    executives: Mapped[list[ExecutiveAgentRecord]] = relationship(back_populates="board_meeting")
    turns: Mapped[list[MeetingTurnRecord]] = relationship(back_populates="board_meeting")
    votes: Mapped[list[BoardVoteRecord]] = relationship(back_populates="board_meeting")
    vote_events: Mapped[list[VoteEventRecord]] = relationship(back_populates="board_meeting")
    confidence_events: Mapped[list[ConfidenceEventRecord]] = relationship(
        back_populates="board_meeting"
    )
    stream_events: Mapped[list[MeetingEventRecord]] = relationship(back_populates="board_meeting")
    reports: Mapped[list[FinalReportRecord]] = relationship(back_populates="board_meeting")


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
    sections: Mapped[list[ReportSectionRecord]] = relationship(back_populates="final_report")


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
