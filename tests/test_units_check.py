"""DB-level CHECK on response_details.units_donated (P1-23)."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.blood_request import ResponseDetails


@pytest.mark.asyncio
async def test_negative_units_donated_rejected_by_database(test_session):
    test_session.add(ResponseDetails(id="RESP-NEG", units_donated=-1))
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()


@pytest.mark.asyncio
async def test_null_and_zero_units_allowed(test_session):
    test_session.add_all([ResponseDetails(id="R-N"), ResponseDetails(id="R-0", units_donated=0)])
    await test_session.commit()


def test_migration_adds_the_constraint(tmp_path):
    import sqlite3
    from tests.test_migrations import _run_alembic

    db = tmp_path / "chk.db"
    assert _run_alembic(f"sqlite+aiosqlite:///{db}", "upgrade", "head").returncode == 0
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO response_details (id, units_donated, created_at) VALUES ('x', -5, '2026-01-01')"
            )
    finally:
        conn.close()
