"""Add account MFA and session revocation version."""

import sqlalchemy as sa
from alembic import op

revision = "0005_user_mfa"
down_revision = "0004_durable_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column("session_version", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("mfa_secret_ciphertext", sa.Text(), nullable=True))
        batch.add_column(sa.Column("mfa_recovery_hashes", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("mfa_recovery_hashes")
        batch.drop_column("mfa_secret_ciphertext")
        batch.drop_column("mfa_enabled")
        batch.drop_column("session_version")
