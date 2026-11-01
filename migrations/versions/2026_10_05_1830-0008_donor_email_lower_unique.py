"""Unique index on lower(donor_details.email): one account per address, whatever the letter case

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-05 18:30:00

The application now stores and looks up donor emails in lowercase. This index makes the database enforce
it, so two accounts whose emails differ only by case can never exist (the old unique constraint compares
exact strings).

An existing database may already hold such pairs. The migration then stops BEFORE changing anything, and
the error names every offending account so they can be merged or renamed by a person; it never picks a
winner. Re-run `alembic upgrade head` once they are resolved. Existing rows are not rewritten.
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
    rows = op.get_bind().execute(sa.text(
        "SELECT id, email FROM donor_details "
        "WHERE lower(email) IN (SELECT lower(email) FROM donor_details GROUP BY lower(email) HAVING COUNT(*) > 1) "
        "ORDER BY lower(email), id"
    )).fetchall()
    if rows:
        groups: dict[str, list[str]] = {}
        for donor_id, email in rows:
            groups.setdefault(email.lower(), []).append(f"{donor_id} <{email}>")
        listing = "\n".join(f"  - {', '.join(accounts)}" for accounts in groups.values())
        raise RuntimeError(
            f"Cannot add the unique index on lower(donor_details.email): {len(groups)} address(es) belong to "
            "more than one donor account and differ only by letter case:\n"
            f"{listing}\n"
            "Merge, rename or delete the extra accounts, then run `alembic upgrade head` again. "
            "Nothing was changed."
        )
    op.create_index(INDEX, "donor_details", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index(INDEX, table_name="donor_details")
