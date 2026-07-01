"""meeting favorites

Revision ID: 0003_meeting_favorites
Revises: 0002_live_boardroom_streaming
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_meeting_favorites"
down_revision: str | None = "0002_live_boardroom_streaming"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "board_meetings",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("board_meetings", "is_favorite", server_default=None)


def downgrade() -> None:
    op.drop_column("board_meetings", "is_favorite")
