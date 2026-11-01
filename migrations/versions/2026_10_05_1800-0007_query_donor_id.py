"""query_table.donor_id: tie support queries to the authenticated donor who filed them

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-05 18:00:00

Support queries used to be owned by an unverified email string, so anyone who registered a donor
account with someone else's address could read that person's queries and admin replies. Ownership
now follows the signed-in donor (donor_id). Existing rows keep donor_id NULL: they stay visible to
admins only and are not shown to any donor.

Non-destructive: adds one nullable column and an index. No data is rewritten or dropped.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("query_table") as batch:
        batch.add_column(
            sa.Column("donor_id", sa.String(length=36), nullable=True)
        )
        # Named: SQLite batch mode cannot create an unnamed constraint.
        batch.create_foreign_key(
            "fk_query_table_donor_id_donor_details",
            "donor_details",
            ["donor_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index(op.f("ix_query_table_donor_id"), ["donor_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("query_table") as batch:
        batch.drop_index(op.f("ix_query_table_donor_id"))
        batch.drop_constraint("fk_query_table_donor_id_donor_details", type_="foreignkey")
        batch.drop_column("donor_id")
