"""executive intelligence meeting modes

Revision ID: 0005_executive_intelligence
Revises: 0004_business_intelligence
Create Date: 2026-07-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_executive_intelligence"
down_revision: str | None = "0004_business_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "startup_briefs",
        sa.Column(
            "meeting_mode",
            sa.String(length=80),
            nullable=False,
            server_default="full_board",
        ),
    )
    op.alter_column("startup_briefs", "meeting_mode", server_default=None)


def downgrade() -> None:
    op.drop_column("startup_briefs", "meeting_mode")
