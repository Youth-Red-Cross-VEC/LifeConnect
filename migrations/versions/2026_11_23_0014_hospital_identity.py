"""Enforce hospital identity across concurrent creations and edits."""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    db = op.get_bind()
    if db.dialect.name == "postgresql":
        op.execute("SET LOCAL lock_timeout = '5s'")
        op.execute("LOCK TABLE hospital_details IN SHARE MODE")
    collision = db.execute(sa.text(
        "SELECT 1 FROM hospital_details GROUP BY lower(hospital_name), "
        "lower(coalesce(branch, '')), pincode HAVING count(*) > 1 LIMIT 1"
    )).first()
    if collision:
        raise RuntimeError("Duplicate hospital identity. Review existing records before retrying revision 0014.")
    op.create_index(
        "uq_hospital_identity", "hospital_details",
        [sa.text("lower(hospital_name)"), sa.text("lower(coalesce(branch, ''))"), "pincode"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_hospital_identity", table_name="hospital_details")
