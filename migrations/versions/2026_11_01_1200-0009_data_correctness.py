"""data correctness: donor availability, donor_ids as text, lower-case emails

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-01 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _lowercase_emails(bind) -> None:
    """Normalise stored addresses, refusing to guess when two rows would collide.

    The donor table already has a unique index on lower(email) (0008), so its update cannot
    collide. Admin emails have only a case-sensitive unique constraint, so two rows can exist
    that differ only by case; there the migration stops instead of silently merging accounts.
    """

    admin_duplicates = bind.execute(
        sa.text(
            "SELECT lower(email) AS address FROM admin_details "
            "GROUP BY lower(email) HAVING count(*) > 1"
        )
    ).fetchall()
    if admin_duplicates:
        addresses = ", ".join(row[0] for row in admin_duplicates)
        raise RuntimeError(
            "Cannot lower-case admin emails: these addresses belong to more than one admin "
            f"({addresses}). Merge or delete the duplicates, then run the migration again."
        )

    bind.execute(sa.text(
        "UPDATE donor_details SET email = lower(email) WHERE email <> lower(email)"
    ))
    bind.execute(sa.text(
        "UPDATE admin_details SET email = lower(email) WHERE email <> lower(email)"
    ))
    bind.execute(sa.text(
        "UPDATE query_table SET user_email = lower(user_email) WHERE user_email <> lower(user_email)"
    ))


def upgrade() -> None:
    bind = op.get_bind()
    # Check every collision first; do nothing if any exists, so a failed run leaves no partial state.
    _lowercase_emails(bind)

    # Plain ADD COLUMN, not batch_alter_table: SQLite's batch mode rebuilds donor_details and
    # drops the functional unique index created by 0008, which then breaks 0008's downgrade.
    op.add_column(
        "donor_details",
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_donor_details_is_available", "donor_details", ["is_available"], unique=False
    )

    with op.batch_alter_table("response_details") as batch:
        batch.alter_column(
            "donor_ids",
            existing_type=sa.String(length=255),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("response_details") as batch:
        batch.alter_column(
            "donor_ids",
            existing_type=sa.Text(),
            type_=sa.String(length=255),
            existing_nullable=True,
        )

    op.drop_index("ix_donor_details_is_available", table_name="donor_details")
    op.drop_column("donor_details", "is_available")

    # Emails stay lower-cased: the original casing is not recorded anywhere and reloading
    # it would resurrect duplicate accounts.
