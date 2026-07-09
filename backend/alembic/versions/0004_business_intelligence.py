"""business intelligence persistence

Revision ID: 0004_business_intelligence
Revises: 0003_meeting_favorites
Create Date: 2026-07-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_business_intelligence"
down_revision: str | None = "0003_meeting_favorites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_type", sa.String(length=60), nullable=False),
        sa.Column("business_idea", sa.Text(), nullable=False),
        sa.Column("business_category", sa.String(length=160), nullable=False),
        sa.Column("location_label", sa.String(length=300), nullable=False),
        sa.Column("budget", sa.Numeric(14, 2), nullable=True),
        sa.Column("data_mode", sa.String(length=40), nullable=False),
        sa.Column("provider_label", sa.String(length=220), nullable=False),
        sa.Column("recommendation_label", sa.String(length=120), nullable=False),
        sa.Column("opportunity_score", sa.Integer(), nullable=False),
        sa.Column("evidence_confidence", sa.String(length=40), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_business_analyses_created_at", "business_analyses", ["created_at"])
    op.create_index(
        "ix_business_analyses_business_category",
        "business_analyses",
        ["business_category"],
    )
    op.create_index("ix_business_analyses_data_mode", "business_analyses", ["data_mode"])

    op.create_table(
        "business_evidence_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("source_name", sa.String(length=220), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=120), nullable=False),
        sa.Column("retrieval_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.String(length=40), nullable=False),
        sa.Column("verification_status", sa.String(length=80), nullable=False),
        sa.Column("freshness", sa.String(length=80), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index(
        "ix_business_evidence_analysis_id",
        "business_evidence_records",
        ["analysis_id"],
    )
    op.create_index(
        "ix_business_evidence_source_type",
        "business_evidence_records",
        ["source_type"],
    )

    op.create_table(
        "saved_suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("category", sa.String(length=160), nullable=True),
        sa.Column("location_label", sa.String(length=220), nullable=True),
        sa.Column("distance_km", sa.Numeric(10, 2), nullable=True),
        sa.Column("verification_status", sa.String(length=80), nullable=False),
        sa.Column("contact_status", sa.String(length=120), nullable=True),
        sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supplier_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_saved_suppliers_analysis_id", "saved_suppliers", ["analysis_id"])
    op.create_index("ix_saved_suppliers_name", "saved_suppliers", ["name"])
    op.create_index("ix_saved_suppliers_preferred", "saved_suppliers", ["is_preferred"])

    op.create_table(
        "business_validation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=True),
        sa.Column("due_date", sa.String(length=120), nullable=True),
        sa.Column("cost", sa.String(length=160), nullable=True),
        sa.Column("expected_evidence", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(length=160), nullable=True),
        sa.Column("effect_on_confidence", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=60), nullable=False, server_default="open"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_business_validation_tasks_analysis_id",
        "business_validation_tasks",
        ["analysis_id"],
    )
    op.create_index(
        "ix_business_validation_tasks_status",
        "business_validation_tasks",
        ["status"],
    )

    op.create_table(
        "business_performance_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_label", sa.String(length=120), nullable=False),
        sa.Column("revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("expenses", sa.Numeric(14, 2), nullable=True),
        sa.Column("customers", sa.Integer(), nullable=True),
        sa.Column("transactions", sa.Integer(), nullable=True),
        sa.Column("performance_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_business_performance_entries_analysis_id",
        "business_performance_entries",
        ["analysis_id"],
    )
    op.create_index(
        "ix_business_performance_entries_created_at",
        "business_performance_entries",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_business_performance_entries_created_at",
        table_name="business_performance_entries",
    )
    op.drop_index(
        "ix_business_performance_entries_analysis_id",
        table_name="business_performance_entries",
    )
    op.drop_table("business_performance_entries")
    op.drop_index("ix_business_validation_tasks_status", table_name="business_validation_tasks")
    op.drop_index(
        "ix_business_validation_tasks_analysis_id",
        table_name="business_validation_tasks",
    )
    op.drop_table("business_validation_tasks")
    op.drop_index("ix_saved_suppliers_preferred", table_name="saved_suppliers")
    op.drop_index("ix_saved_suppliers_name", table_name="saved_suppliers")
    op.drop_index("ix_saved_suppliers_analysis_id", table_name="saved_suppliers")
    op.drop_table("saved_suppliers")
    op.drop_index("ix_business_evidence_source_type", table_name="business_evidence_records")
    op.drop_index("ix_business_evidence_analysis_id", table_name="business_evidence_records")
    op.drop_table("business_evidence_records")
    op.drop_index("ix_business_analyses_data_mode", table_name="business_analyses")
    op.drop_index("ix_business_analyses_business_category", table_name="business_analyses")
    op.drop_index("ix_business_analyses_created_at", table_name="business_analyses")
    op.drop_table("business_analyses")
