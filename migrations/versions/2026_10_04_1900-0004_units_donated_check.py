"""CHECK units_donated >= 0

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-04 19:00:00

The upper bound (units_donated <= units_required) compares columns of two
different tables, which a CHECK constraint cannot do; it stays enforced by
POST /blood-requests/{id}/close.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT = "ck_response_details_units_donated_nonneg"


def upgrade() -> None:
    with op.batch_alter_table("response_details") as batch:
        batch.create_check_constraint(CONSTRAINT, "units_donated IS NULL OR units_donated >= 0")


def downgrade() -> None:
    with op.batch_alter_table("response_details") as batch:
        batch.drop_constraint(CONSTRAINT, type_="check")
