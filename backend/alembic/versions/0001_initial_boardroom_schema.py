"""initial boardroom schema

Revision ID: 0001_initial_boardroom_schema
Revises:
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial_boardroom_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "startup_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("startup_idea", sa.Text(), nullable=False),
        sa.Column("industry", sa.String(length=160), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("budget", sa.Numeric(14, 2), nullable=False),
        sa.Column("timeline_months", sa.Integer(), nullable=False),
        sa.Column("competitors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=False),
        sa.Column("funding_stage", sa.String(length=80), nullable=False),
        sa.Column("business_model", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "board_meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "startup_brief_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("startup_briefs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("consensus_reached", sa.Boolean(), nullable=False),
        sa.Column("aggregate_confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("decision", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "executive_agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("charter", sa.Text(), nullable=False),
        sa.Column("personality", sa.Text(), nullable=False),
        sa.Column("goals", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risk_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )

    op.create_table(
        "meeting_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("speaker_role", sa.String(length=120), nullable=False),
        sa.Column("turn_type", sa.String(length=40), nullable=False),
        sa.Column("stance", sa.String(length=60), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("concerns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "board_votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("vote", sa.String(length=60), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
    )

    op.create_table(
        "final_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("decision", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "report_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "final_report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("final_reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_key", sa.String(length=120), nullable=False),
        sa.Column("section_title", sa.String(length=160), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )

    op.create_index("ix_board_meetings_startup_brief_id", "board_meetings", ["startup_brief_id"])
    op.create_index("ix_meeting_turns_board_meeting_id", "meeting_turns", ["board_meeting_id"])
    op.create_index("ix_report_sections_final_report_id", "report_sections", ["final_report_id"])


def downgrade() -> None:
    op.drop_index("ix_report_sections_final_report_id", table_name="report_sections")
    op.drop_index("ix_meeting_turns_board_meeting_id", table_name="meeting_turns")
    op.drop_index("ix_board_meetings_startup_brief_id", table_name="board_meetings")
    op.drop_table("report_sections")
    op.drop_table("final_reports")
    op.drop_table("board_votes")
    op.drop_table("meeting_turns")
    op.drop_table("executive_agents")
    op.drop_table("board_meetings")
    op.drop_table("startup_briefs")
