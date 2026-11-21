"""Add donor erasure review state and retryable certificate removal."""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "erasure_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("donor_id", sa.String(36), sa.ForeignKey("donor_details.id", ondelete="SET NULL"), unique=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.CheckConstraint("status IN ('pending', 'completed', 'rejected')", name="ck_erasure_request_status"),
    )
    op.create_table("erasure_files", sa.Column("filename", sa.String(255), primary_key=True))


def downgrade() -> None:
    op.drop_table("erasure_files")
    op.drop_table("erasure_requests")
