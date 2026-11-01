"""Make personal_details.aadhar_number nullable (non-destructive)

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-04 19:30:00

The application no longer stores Aadhaar numbers and the ORM model has no such column, so
inserts leave it out. This only guarantees the column (if it still exists) accepts NULL.
It never drops data, so `alembic upgrade head` can run automatically on every start.

The destructive drop is a deliberate, manual step: scripts/drop_aadhaar_column.py.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {c["name"]: c for c in sa.inspect(op.get_bind()).get_columns("personal_details")}
    column = columns.get("aadhar_number")
    if column is None or column["nullable"]:
        return  # already dropped by the manual script, or already nullable
    with op.batch_alter_table("personal_details") as batch:
        batch.alter_column("aadhar_number", existing_type=sa.String(length=20), nullable=True)


def downgrade() -> None:
    # Nothing to undo: relaxing a NOT NULL constraint is not worth re-imposing.
    pass
