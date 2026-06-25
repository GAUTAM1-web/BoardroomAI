"""live boardroom streaming persistence

Revision ID: 0002_live_boardroom_streaming
Revises: 0001_initial_boardroom_schema
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_live_boardroom_streaming"
down_revision: str | None = "0001_initial_boardroom_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("board_meetings", sa.Column("current_phase", sa.String(length=80), nullable=True))
    op.add_column("board_meetings", sa.Column("assessment", postgresql.JSONB(), nullable=True))

    op.add_column("meeting_turns", sa.Column("sequence", sa.Integer(), nullable=True))
    op.add_column("meeting_turns", sa.Column("topic", sa.String(length=160), nullable=True))
    op.add_column("meeting_turns", sa.Column("reasoning", postgresql.JSONB(), nullable=True))
    op.add_column(
        "meeting_turns",
        sa.Column("memory_references", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "meeting_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_meeting_events_board_meeting_id", "meeting_events", ["board_meeting_id"])
    op.create_index(
        "ix_meeting_events_sequence", "meeting_events", ["board_meeting_id", "sequence"]
    )

    op.create_table(
        "confidence_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("previous_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("delta", sa.Numeric(5, 4), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_confidence_events_board_meeting_id",
        "confidence_events",
        ["board_meeting_id"],
    )

    op.create_table(
        "vote_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("previous_vote", sa.String(length=60), nullable=True),
        sa.Column("vote", sa.String(length=60), nullable=False),
        sa.Column("changed", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_vote_events_board_meeting_id", "vote_events", ["board_meeting_id"])


def downgrade() -> None:
    op.drop_index("ix_vote_events_board_meeting_id", table_name="vote_events")
    op.drop_table("vote_events")
    op.drop_index("ix_confidence_events_board_meeting_id", table_name="confidence_events")
    op.drop_table("confidence_events")
    op.drop_index("ix_meeting_events_sequence", table_name="meeting_events")
    op.drop_index("ix_meeting_events_board_meeting_id", table_name="meeting_events")
    op.drop_table("meeting_events")
    op.drop_column("meeting_turns", "memory_references")
    op.drop_column("meeting_turns", "reasoning")
    op.drop_column("meeting_turns", "topic")
    op.drop_column("meeting_turns", "sequence")
    op.drop_column("board_meetings", "assessment")
    op.drop_column("board_meetings", "current_phase")
