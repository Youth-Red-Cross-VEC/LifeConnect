"""Unique index on lower(donor_details.email): one account per address, whatever the letter case

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-05 18:30:00

The application now stores and looks up donor emails in lowercase. This index makes the database enforce
it, so two accounts whose emails differ only by case can never exist (the old unique constraint compares
exact strings).

Existing collisions stop the upgrade for private operator review.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX = "uq_donor_details_email_lower"


def upgrade() -> None:
    collision = op.get_bind().execute(sa.text(
        "SELECT 1 FROM donor_details GROUP BY lower(email) HAVING count(*) > 1 LIMIT 1"
    )).first()
    if collision:
        raise RuntimeError("Donor email addresses differ only by letter case. Review collisions privately before retrying.")
    op.create_index(INDEX, "donor_details", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index(INDEX, table_name="donor_details")
