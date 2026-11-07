"""Create initial evaluation and feedback tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_runs_project", "evaluation_runs", ["project"])
    op.create_index("ix_evaluation_runs_input_digest", "evaluation_runs", ["input_digest"])
    op.create_index("ix_evaluation_runs_created_at", "evaluation_runs", ["created_at"])
    op.create_table(
        "review_feedback",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewer_id", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_feedback_run_id", "review_feedback", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_review_feedback_run_id", table_name="review_feedback")
    op.drop_table("review_feedback")
    op.drop_index("ix_evaluation_runs_created_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_input_digest", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_project", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
