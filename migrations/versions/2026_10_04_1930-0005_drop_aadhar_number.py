"""DROP personal_details.aadhar_number  (DESTRUCTIVE)

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-04 19:30:00

The application no longer collects or stores Aadhaar numbers. Dropping the
column permanently deletes any values still in it, so this migration REFUSES
to run while the column holds data unless LIFECONNECT_ALLOW_AADHAAR_DROP=1 is
set. Fresh/empty databases drop it silently. Back up first, then run:

    LIFECONNECT_ALLOW_AADHAAR_DROP=1 alembic upgrade head

The downgrade re-creates the column empty; dropped values are not recoverable.
"""

import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ALLOW_ENV = "LIFECONNECT_ALLOW_AADHAAR_DROP"


def upgrade() -> None:
    bind = op.get_bind()
    populated = bind.execute(
        sa.text("SELECT COUNT(*) FROM personal_details WHERE aadhar_number IS NOT NULL")
    ).scalar()
    if populated and os.environ.get(ALLOW_ENV) != "1":
        raise RuntimeError(
            f"Refusing to drop personal_details.aadhar_number: {populated} row(s) contain data. "
            f"Back up the database, then re-run with {ALLOW_ENV}=1 to confirm."
        )
    with op.batch_alter_table("personal_details") as batch:
        batch.drop_column("aadhar_number")


def downgrade() -> None:
    with op.batch_alter_table("personal_details") as batch:
        batch.add_column(sa.Column("aadhar_number", sa.String(length=20), nullable=True))
