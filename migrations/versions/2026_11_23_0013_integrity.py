"""Enforce account, blood request and OTP invariants without rewriting legacy values."""

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

OTP_TABLES = ("otp_codes", "otp_failure_windows")


def upgrade() -> None:
    db = op.get_bind()
    if db.dialect.name == "postgresql":
        op.execute("SET LOCAL lock_timeout = '5s'")
        op.execute("LOCK TABLE admin_details, blood_request_details, otp_codes, otp_failure_windows IN SHARE ROW EXCLUSIVE MODE")
    checks = [
        ("administrator email collision", "SELECT 1 FROM admin_details GROUP BY lower(email) HAVING count(*) > 1"),
        ("shared response", "SELECT 1 FROM blood_request_details GROUP BY response_id HAVING count(*) > 1"),
    ]
    for table in OTP_TABLES:
        checks.append((f"negative attempts in {table}", f"SELECT 1 FROM {table} WHERE attempts < 0"))
    for label, query in checks:
        if db.execute(sa.text(query + " LIMIT 1")).first():
            raise RuntimeError(f"Revision 0013 blocked by {label}. Review affected records before retrying.")
    op.create_index("uq_admin_details_email_lower", "admin_details", [sa.text("lower(email)")], unique=True)
    op.create_index("uq_blood_request_response", "blood_request_details", ["response_id"], unique=True)
    for table in OTP_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.create_check_constraint(f"ck_{table}_attempts", "attempts >= 0")


def downgrade() -> None:
    for table in reversed(OTP_TABLES):
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(f"ck_{table}_attempts", type_="check")
    op.drop_index("uq_blood_request_response", table_name="blood_request_details")
    op.drop_index("uq_admin_details_email_lower", table_name="admin_details")
