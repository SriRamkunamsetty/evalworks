"""Add allowlisted run version metadata."""

import sqlalchemy as sa
from alembic import op

revision = "0002_run_metadata"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("evaluation_runs", "metadata")
