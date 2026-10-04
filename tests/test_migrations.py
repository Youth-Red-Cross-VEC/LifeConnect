"""Schema must be reproducible from migrations alone, with no drift from the ORM."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import asyncio

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.models.base import Base
import app.models  # noqa: F401  (register all tables)

ROOT = Path(__file__).resolve().parent.parent


def _run_alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "DATABASE_URL": db_url,
        "SECRET_KEY": "k" * 40,
        "GOOGLE_MAPS_API_KEY": "x",
        "MAIL_SERVER": "x",
        "MAIL_USERNAME": "x",
        "MAIL_PASSWORD": "x",
        "MAIL_FROM": "a@example.com",
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )


def _database_urls(tmp_path):
    urls = [("sqlite", f"sqlite+aiosqlite:///{tmp_path / 'mig.db'}")]
    pg = os.environ.get("MIGRATION_TEST_DATABASE_URL")  # e.g. postgresql+asyncpg://...@localhost/empty_db
    if pg:
        urls.append(("postgres", pg))
    return urls


async def _table_names(url: str) -> set[str]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            return set(await conn.run_sync(lambda c: inspect(c).get_table_names()))
    finally:
        await engine.dispose()


@pytest.mark.parametrize("kind", ["sqlite", "postgres"])
def test_upgrade_head_creates_all_tables_and_no_drift(tmp_path, kind):
    chosen = dict(_database_urls(tmp_path))
    if kind not in chosen:
        pytest.skip("set MIGRATION_TEST_DATABASE_URL to an EMPTY throwaway Postgres to test it")
    async_url = chosen[kind]

    upgrade = _run_alembic(async_url, "upgrade", "head")
    assert upgrade.returncode == 0, upgrade.stderr

    tables = asyncio.run(_table_names(async_url))
    expected = set(Base.metadata.tables)
    assert expected <= tables, f"missing tables: {expected - tables}"

    check = _run_alembic(async_url, "check")
    assert check.returncode == 0, check.stdout + check.stderr
