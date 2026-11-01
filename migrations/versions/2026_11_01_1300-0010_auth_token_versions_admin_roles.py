"""Add token invalidation versions and database-backed admin roles.

Revision ID: 0010
Revises: 0009
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("donor_details", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("admin_details", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("admin_details", sa.Column("role", sa.String(length=20), nullable=False, server_default="admin"))

    bind = op.get_bind()
    bind.execute(sa.text("UPDATE admin_details SET active_status = 'Active' WHERE lower(active_status) = 'active'"))
    bind.execute(sa.text("UPDATE admin_details SET active_status = 'Inactive' WHERE lower(active_status) = 'inactive'"))
    oldest = bind.execute(sa.text("SELECT id FROM admin_details ORDER BY created_at ASC, id ASC LIMIT 1")).scalar_one_or_none()
    if oldest is not None:
        bind.execute(sa.text("UPDATE admin_details SET role = 'super_admin' WHERE id = :id"), {"id": oldest})


def downgrade() -> None:
    op.drop_column("admin_details", "role")
    op.drop_column("admin_details", "token_version")
    op.drop_column("donor_details", "token_version")
