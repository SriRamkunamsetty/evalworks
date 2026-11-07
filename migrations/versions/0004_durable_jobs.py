"""Add encrypted, durable evaluation jobs."""

import sqlalchemy as sa
from alembic import op

revision = "0004_durable_jobs"
down_revision = "0003_workspaces_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            sa.ForeignKey("workspaces.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("project", sa.String(length=48), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("payload_ciphertext", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.id", ondelete="SET NULL"),
        ),
        sa.Column("error_code", sa.String(length=40)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_jobs_status",
        ),
        sa.UniqueConstraint("workspace_id", "idempotency_key", name="uq_job_idempotency"),
    )
    op.create_index("ix_evaluation_jobs_workspace_id", "evaluation_jobs", ["workspace_id"])
    op.create_index("ix_evaluation_jobs_status", "evaluation_jobs", ["status"])
    op.create_index("ix_evaluation_jobs_available_at", "evaluation_jobs", ["available_at"])
    op.create_index("ix_evaluation_jobs_created_at", "evaluation_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_jobs_created_at", table_name="evaluation_jobs")
    op.drop_index("ix_evaluation_jobs_available_at", table_name="evaluation_jobs")
    op.drop_index("ix_evaluation_jobs_status", table_name="evaluation_jobs")
    op.drop_index("ix_evaluation_jobs_workspace_id", table_name="evaluation_jobs")
    op.drop_table("evaluation_jobs")
