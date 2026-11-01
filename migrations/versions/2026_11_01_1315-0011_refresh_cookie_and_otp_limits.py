"""Rename refresh records and track hourly OTP failure limits.

Revision ID: 0011
Revises: 0010
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Old OTP values used an unkeyed digest, so invalidate outstanding codes instead of
    # carrying forward records that no longer satisfy the HMAC-at-rest policy.
    op.execute(sa.text("DELETE FROM otp_codes"))
    with op.batch_alter_table("otp_codes") as batch:
        batch.alter_column(
            "otp_hash", new_column_name="code_hmac",
            existing_type=sa.String(length=64), existing_nullable=False,
        )

    op.rename_table("refresh_sessions", "refresh_tokens")
    with op.batch_alter_table("refresh_tokens") as batch:
        batch.alter_column(
            "role", new_column_name="user_type",
            existing_type=sa.String(length=10), existing_nullable=False,
        )
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_tokens")
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "otp_failure_windows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("purpose", "email", name="uq_otp_failure_windows_purpose_email"),
    )


def downgrade() -> None:
    op.drop_table("otp_failure_windows")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.rename_table("refresh_tokens", "refresh_sessions")
    with op.batch_alter_table("refresh_sessions") as batch:
        batch.alter_column(
            "user_type", new_column_name="role",
            existing_type=sa.String(length=10), existing_nullable=False,
        )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"], unique=False)
    with op.batch_alter_table("otp_codes") as batch:
        batch.alter_column(
            "code_hmac", new_column_name="otp_hash",
            existing_type=sa.String(length=64), existing_nullable=False,
        )
