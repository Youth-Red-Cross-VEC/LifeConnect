#!/usr/bin/env python
"""Load the synthetic DEVELOPMENT data. Never for a real deployment.

    python scripts/load_dev_data.py            # one bootstrap admin (docs/initial_data.sql)
    python scripts/load_dev_data.py --full     # 2 admins, 10 donors, hospitals, requests (docs/SyntheticData.sql)
    python scripts/load_dev_data.py --database-url postgresql+asyncpg://user:pw@localhost/lifeconnect

Every account in that data has the PUBLISHED password `DevOnly#2026`, so anyone who has read this repository can
log in as the seeded admin. That makes loading it into the wrong database a security incident, and this script
refuses to do it:

  * APP_ENV=production (any capitalisation): refused.
  * the database already holds any admin or donor account (a copy of real data restored "just for testing",
    a staging database, a production database with APP_ENV set wrongly): refused. Seed an EMPTY database.

Run `alembic upgrade head` first. Do not pipe the .sql files into psql by hand: that has no guard at all.
Uses DATABASE_URL and APP_ENV from the environment/.env unless --database-url is given.
"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

BOOTSTRAP = ROOT / "docs" / "initial_data.sql"
FULL = ROOT / "docs" / "SyntheticData.sql"
GUARDED_TABLES = ("admin_details", "donor_details")


def async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def refuse_reason(app_env: str, existing: dict[str, int]) -> Optional[str]:
    """Why the seed must not be loaded, or None if it may be."""
    if app_env.strip().lower() == "production":
        return "APP_ENV is production: the dev seed has a published admin password and must never be loaded here."
    populated = {table: n for table, n in existing.items() if n}
    if populated:
        found = ", ".join(f"{n} row(s) in {table}" for table, n in populated.items())
        return (
            f"the database is not empty ({found}). The dev seed adds an admin with a published password, so "
            "it only loads into an empty database (run `alembic upgrade head` on a fresh one)."
        )
    return None


def split_statements(sql: str) -> list[str]:
    """Split a SQL script on ';', ignoring ';' inside '...' strings and '--' comments."""
    statements, current, i, n = [], [], 0, len(sql)
    in_string = False
    while i < n:
        ch = sql[i]
        if in_string:
            current.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":  # '' is an escaped quote
                    current.append("'")
                    i += 1
                else:
                    in_string = False
        elif ch == "'":
            in_string = True
            current.append(ch)
        elif ch == "-" and sql.startswith("--", i):
            while i < n and sql[i] != "\n":
                i += 1
            continue
        elif ch == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


async def load(url: str, sql: str, app_env: str) -> int:
    engine = create_async_engine(async_url(url))
    try:
        async with engine.begin() as conn:
            existing = {
                table: (await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()  # fixed table names
                for table in GUARDED_TABLES
            }
            reason = refuse_reason(app_env, existing)
            if reason:
                print(f"Refusing to load the dev data: {reason}", file=sys.stderr)
                return 2
            statements = split_statements(sql)
            for statement in statements:
                await conn.execute(text(statement))
            print(f"Loaded {len(statements)} statements of synthetic development data.")
            print("Every seeded account uses the published password DevOnly#2026. Development only.")
            return 0
    finally:
        await engine.dispose()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--full", action="store_true", help="load docs/SyntheticData.sql instead of the bootstrap admin")
    parser.add_argument("--database-url", help="target database (default: DATABASE_URL from the environment/.env)")
    args = parser.parse_args(argv)

    from app.config import get_settings  # reads .env

    settings = get_settings()
    url = args.database_url or settings.DATABASE_URL
    sql = (FULL if args.full else BOOTSTRAP).read_text(encoding="utf-8")
    return asyncio.run(load(url, sql, settings.APP_ENV))


if __name__ == "__main__":
    raise SystemExit(main())
