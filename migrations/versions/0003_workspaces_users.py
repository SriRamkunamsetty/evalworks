"""Add workspace isolation and authenticated users."""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0003_workspaces_users"
down_revision = "0002_run_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "workspaces",
            sa.column("id", sa.String()),
            sa.column("name", sa.String()),
            sa.column("created_at", sa.DateTime(timezone=True)),
        ),
        [{"id": "local", "name": "Local development", "created_at": datetime.now(UTC)}],
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("role IN ('admin', 'reviewer', 'viewer')", name="ck_users_role"),
    )
    op.create_index("ix_users_workspace_id", "users", ["workspace_id"])
    op.create_index("ix_users_email", "users", ["email"])
    with op.batch_alter_table("evaluation_runs") as batch:
        batch.add_column(
            sa.Column("workspace_id", sa.String(length=36), nullable=False, server_default="local")
        )
        batch.add_column(sa.Column("created_by", sa.String(length=36), nullable=True))
        batch.create_foreign_key(
            "fk_evaluation_runs_workspace", "workspaces", ["workspace_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_evaluation_runs_created_by", "users", ["created_by"], ["id"], ondelete="SET NULL"
        )
        batch.create_index("ix_evaluation_runs_workspace_id", ["workspace_id"])
    with op.batch_alter_table("review_feedback") as batch:
        batch.add_column(
            sa.Column("workspace_id", sa.String(length=36), nullable=False, server_default="local")
        )
        batch.create_foreign_key(
            "fk_review_feedback_workspace", "workspaces", ["workspace_id"], ["id"]
        )
        batch.create_index("ix_review_feedback_workspace_id", ["workspace_id"])


def downgrade() -> None:
    with op.batch_alter_table("review_feedback") as batch:
        batch.drop_index("ix_review_feedback_workspace_id")
        batch.drop_constraint("fk_review_feedback_workspace", type_="foreignkey")
        batch.drop_column("workspace_id")
    with op.batch_alter_table("evaluation_runs") as batch:
        batch.drop_index("ix_evaluation_runs_workspace_id")
        batch.drop_constraint("fk_evaluation_runs_created_by", type_="foreignkey")
        batch.drop_constraint("fk_evaluation_runs_workspace", type_="foreignkey")
        batch.drop_column("created_by")
        batch.drop_column("workspace_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_workspace_id", table_name="users")
    op.drop_table("users")
    op.drop_table("workspaces")
