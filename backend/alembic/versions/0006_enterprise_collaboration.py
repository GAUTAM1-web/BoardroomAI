"""enterprise collaboration workspace

Revision ID: 0006_enterprise_collaboration
Revises: 0005_executive_intelligence
Create Date: 2026-07-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_enterprise_collaboration"
down_revision: str | None = "0005_executive_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "enterprise_organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("default_locale", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "enterprise_departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "enterprise_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "enterprise_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=240), nullable=False, unique=True),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "enterprise_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("role", sa.String(length=60), nullable=False),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.add_column("board_meetings", sa.Column("organization_id", postgresql.UUID(as_uuid=True)))
    op.add_column("board_meetings", sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key(
        "fk_board_meetings_organization_id",
        "board_meetings",
        "enterprise_organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_board_meetings_created_by_user_id",
        "board_meetings",
        "enterprise_users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("business_analyses", sa.Column("organization_id", postgresql.UUID(as_uuid=True)))
    op.add_column(
        "business_analyses", sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True))
    )
    op.create_foreign_key(
        "fk_business_analyses_organization_id",
        "business_analyses",
        "enterprise_organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_business_analyses_created_by_user_id",
        "business_analyses",
        "enterprise_users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "meeting_collaborators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "report_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_comment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("report_comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_key", sa.String(length=120), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("mentions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "approval_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "business_analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_analyses.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "approval_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("approval_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "approver_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("role", sa.String(length=60), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "enterprise_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "board_meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_meetings.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "business_analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_analyses.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "assignee_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_entity_type", sa.String(length=80), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "enterprise_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "knowledge_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("item_type", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "report_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("sections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    for table, columns in {
        "enterprise_departments": ["organization_id"],
        "enterprise_teams": ["organization_id", "department_id"],
        "enterprise_memberships": ["organization_id", "user_id"],
        "meeting_collaborators": ["board_meeting_id", "user_id"],
        "report_comments": ["organization_id", "board_meeting_id"],
        "approval_workflows": ["organization_id", "board_meeting_id", "business_analysis_id"],
        "enterprise_tasks": ["organization_id", "status"],
        "calendar_events": ["organization_id", "starts_at"],
        "enterprise_notifications": ["organization_id", "status"],
        "knowledge_items": ["organization_id", "item_type"],
        "audit_events": ["organization_id", "action"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    for table, columns in {
        "audit_events": ["organization_id", "action"],
        "knowledge_items": ["organization_id", "item_type"],
        "enterprise_notifications": ["organization_id", "status"],
        "calendar_events": ["organization_id", "starts_at"],
        "enterprise_tasks": ["organization_id", "status"],
        "approval_workflows": ["organization_id", "board_meeting_id", "business_analysis_id"],
        "report_comments": ["organization_id", "board_meeting_id"],
        "meeting_collaborators": ["board_meeting_id", "user_id"],
        "enterprise_memberships": ["organization_id", "user_id"],
        "enterprise_teams": ["organization_id", "department_id"],
        "enterprise_departments": ["organization_id"],
    }.items():
        for column in columns:
            op.drop_index(f"ix_{table}_{column}", table_name=table)

    op.drop_table("audit_events")
    op.drop_table("report_templates")
    op.drop_table("knowledge_items")
    op.drop_table("enterprise_notifications")
    op.drop_table("calendar_events")
    op.drop_table("enterprise_tasks")
    op.drop_table("approval_steps")
    op.drop_table("approval_workflows")
    op.drop_table("report_comments")
    op.drop_table("meeting_collaborators")
    op.drop_constraint(
        "fk_business_analyses_created_by_user_id",
        "business_analyses",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_business_analyses_organization_id",
        "business_analyses",
        type_="foreignkey",
    )
    op.drop_column("business_analyses", "created_by_user_id")
    op.drop_column("business_analyses", "organization_id")
    op.drop_constraint(
        "fk_board_meetings_created_by_user_id",
        "board_meetings",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_board_meetings_organization_id",
        "board_meetings",
        type_="foreignkey",
    )
    op.drop_column("board_meetings", "created_by_user_id")
    op.drop_column("board_meetings", "organization_id")
    op.drop_table("enterprise_memberships")
    op.drop_table("enterprise_users")
    op.drop_table("enterprise_teams")
    op.drop_table("enterprise_departments")
    op.drop_table("enterprise_organizations")
