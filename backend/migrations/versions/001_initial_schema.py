"""Initial schema for MCP Forge.

Revision ID: 001_initial
Revises: None
Create Date: 2026-10-04 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. project table
    op.create_table(
        "project",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.Column("archived_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_slug", "project", ["slug"], unique=True)

    # 2. spec_version table
    op.create_table(
        "spec_version",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_ref", sa.String(length=256), nullable=False),
        sa.Column("format", sa.String(length=8), nullable=False),
        sa.Column("spec_kind", sa.String(length=16), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("operation_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "version_no", name="uq_project_spec_version"),
    )
    op.create_index("ix_spec_version_project_id", "spec_version", ["project_id"], unique=False)

    # 3. project_settings table
    op.create_table(
        "project_settings",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("timeout_s", sa.Integer(), nullable=False),
        sa.Column("max_response_chars", sa.Integer(), nullable=False),
        sa.Column("retry_safe_requests", sa.Boolean(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("naming_style", sa.String(length=16), nullable=False),
        sa.Column("include_writes_default", sa.Boolean(), nullable=False),
        sa.Column("auth_mapping", sa.Text(), nullable=False),
        sa.Column("transports", sa.Text(), nullable=False),
        sa.Column("tool_prefix", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )

    # 4. operation_config table
    op.create_table(
        "operation_config",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("operation_key", sa.String(length=256), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("tool_name_override", sa.String(length=64), nullable=True),
        sa.Column("description_override", sa.Text(), nullable=True),
        sa.Column("group_override", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "operation_key"),
    )

    # 5. build table
    op.create_table(
        "build",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("spec_version_id", sa.String(length=36), nullable=False),
        sa.Column("build_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("tool_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("generator_version", sa.String(length=32), nullable=False),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("error_message_safe", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["spec_version_id"], ["spec_version.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_build_project_id", "build", ["project_id"], unique=False)
    op.create_index("ix_build_spec_version_id", "build", ["spec_version_id"], unique=False)

    # 6. review_finding table
    op.create_table(
        "review_finding",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("build_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("spec_version_id", sa.String(length=36), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("operation_key", sa.String(length=256), nullable=True),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["build.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["spec_version_id"], ["spec_version.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_finding_project_id", "review_finding", ["project_id"], unique=False)
    op.create_index(
        "ix_review_finding_spec_version_id", "review_finding", ["spec_version_id"], unique=False
    )

    # 7. playground_session table
    op.create_table(
        "playground_session",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("build_id", sa.String(length=36), nullable=False),
        sa.Column("target", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.String(length=32), nullable=False),
        sa.Column("ended_at", sa.String(length=32), nullable=True),
        sa.Column("exit_info", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["build_id"], ["build.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_playground_session_build_id", "playground_session", ["build_id"], unique=False
    )

    # 8. trace_event table
    op.create_table(
        "trace_event",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=24), nullable=False),
        sa.Column("message_json", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["playground_session.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trace_event_session_id", "trace_event", ["session_id"], unique=False)

    # 9. app_setting table
    op.create_table(
        "app_setting",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("app_setting")
    op.drop_table("trace_event")
    op.drop_table("playground_session")
    op.drop_table("review_finding")
    op.drop_table("build")
    op.drop_table("operation_config")
    op.drop_table("project_settings")
    op.drop_table("spec_version")
    op.drop_table("project")
