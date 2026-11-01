"""Permanently drop personal_details.aadhar_number (DESTRUCTIVE, manual only).

The application no longer stores Aadhaar numbers, but the column (and any values in it) is
left in place by `alembic upgrade head` so deploys can never lose data by accident. Run this
yourself, after taking a backup:

    LIFECONNECT_ALLOW_AADHAAR_DROP=1 python scripts/drop_aadhaar_column.py --i-have-a-backup

Without --i-have-a-backup it only reports how many rows hold a value and exits non-zero.
Uses DATABASE_URL from the environment/.env. Safe to re-run: a missing column is a no-op.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

ALLOW_ENV = "LIFECONNECT_ALLOW_AADHAAR_DROP"


def async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def run(url: str, confirmed: bool) -> int:
    engine = create_async_engine(async_url(url))
    try:
        async with engine.begin() as conn:
            columns = await conn.run_sync(lambda c: [x["name"] for x in inspect(c).get_columns("personal_details")])
            if "aadhar_number" not in columns:
                print("personal_details.aadhar_number does not exist; nothing to do.")
                return 0
            count = (await conn.execute(
                text("SELECT COUNT(*) FROM personal_details WHERE aadhar_number IS NOT NULL")
            )).scalar()
            print(f"{count} row(s) in personal_details hold an Aadhaar number.")
            if os.environ.get(ALLOW_ENV) != "1":
                print(f"Refusing: set {ALLOW_ENV}=1 to confirm you want this data destroyed.", file=sys.stderr)
                return 2
            if not confirmed:
                print("Refusing: pass --i-have-a-backup once you have a verified database backup.", file=sys.stderr)
                return 2
            await conn.execute(text("ALTER TABLE personal_details DROP COLUMN aadhar_number"))
            print("Dropped personal_details.aadhar_number.")
            return 0
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--i-have-a-backup", action="store_true", dest="confirmed")
    args = parser.parse_args()
    url = os.environ.get("DATABASE_URL")
    if not url:
        from app.config import get_settings  # reads .env

        url = get_settings().DATABASE_URL
    return asyncio.run(run(url, args.confirmed))


if __name__ == "__main__":
    sys.exit(main())
