"""Upgrading a populated, 0004-era database to head keeps every row and changes nothing it should not.

Revisions 0005-0008 relax the Aadhaar column, add the audit log, tie support queries to donors and add the
case-insensitive email index. A real deployment upgrades with data in the tables, so test exactly that, on
SQLite and (when MIGRATION_TEST_DATABASE_URL is set) on PostgreSQL.
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.test_email_migration import _donor, _remove, _run
from tests.test_migrations import _database_urls, _run_alembic

OLD_ADMIN = (
    "INSERT INTO admin_details (id, email, password, username, authentication_id, vec_registration_number, "
    "date_of_birth, mobile_number, active_status, approved_donation_count, closed_requests_count, created_at) "
    "VALUES ('ADM-9', 'old.admin@example.com', 'x', 'Old Admin', 'AUTHADM-9', 'VEC-9', '1980-01-01', '9000000009', "
    "'Active', 0, 0, '2026-01-01 00:00:00')"
)
OLD_QUERIES = [
    "INSERT INTO query_table (user_name, user_email, admin_id, admin_name, user_query, created_at) "
    "VALUES ('Visitor', 'visitor@example.com', 'PENDING', 'PENDING', 'a question from before ownership', '2026-01-01 00:00:00')",
    "INSERT INTO query_table (user_name, user_email, admin_id, admin_name, user_query, admin_response, created_at) "
    "VALUES ('Donor', 'a@example.com', 'ADM-9', 'Old Admin', 'answered earlier', 'here is the answer', '2026-01-02 00:00:00')",
]
AADHAAR = "UPDATE personal_details SET aadhar_number = '000011112222' WHERE id = 'PD-1'"
CLEANUP = _remove(1) + _remove(2) + [
    "DELETE FROM query_table WHERE user_email IN ('visitor@example.com', 'a@example.com')",
    "DELETE FROM admin_details WHERE id = 'ADM-9'",
]


async def _fetch(url: str, sql: str):
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            return (await conn.execute(text(sql))).fetchall()
    finally:
        await engine.dispose()


@pytest.fixture(params=["sqlite", "postgres"])
def old_database(request, tmp_path):
    urls = dict(_database_urls(tmp_path))
    if request.param not in urls:
        pytest.skip("set MIGRATION_TEST_DATABASE_URL to an EMPTY throwaway Postgres to test it")
    url = urls[request.param]
    for step in (("upgrade", "head"), ("downgrade", "0004")):  # start from a database as it was at 0004
        done = _run_alembic(url, *step)
        assert done.returncode == 0, done.stderr
    yield request.param, url
    asyncio.run(_run(url, CLEANUP))
    assert _run_alembic(url, "upgrade", "head").returncode == 0  # leave the shared database at head


def test_a_populated_0004_database_upgrades_to_head_without_losing_anything(old_database):
    dialect, url = old_database
    seed = _donor(1, "a@example.com", dialect) + _donor(2, "B@Example.com", dialect)
    asyncio.run(_run(url, seed + [AADHAAR, OLD_ADMIN] + OLD_QUERIES))

    done = _run_alembic(url, "upgrade", "head")
    assert done.returncode == 0, done.stdout + done.stderr

    emails = [e for (e,) in asyncio.run(_fetch(url, "SELECT email FROM donor_details WHERE id IN ('DON-1', 'DON-2') ORDER BY id"))]
    assert emails == ["a@example.com", "B@Example.com"], "existing emails are not rewritten"
    assert asyncio.run(_fetch(url, "SELECT COUNT(*) FROM admin_details WHERE id = 'ADM-9'"))[0][0] == 1

    queries = asyncio.run(_fetch(url, "SELECT user_query, admin_response, donor_id FROM query_table WHERE user_email IN ('visitor@example.com', 'a@example.com') ORDER BY id"))
    assert [q[0] for q in queries] == ["a question from before ownership", "answered earlier"]
    assert queries[1][1] == "here is the answer"
    assert all(q[2] is None for q in queries), "pre-existing queries stay ownerless (admin-visible only)"

    assert asyncio.run(_fetch(url, "SELECT aadhar_number FROM personal_details WHERE id = 'PD-1'"))[0][0] == "000011112222", (
        "upgrading must never destroy the retired Aadhaar column or its values"
    )
    assert _run_alembic(url, "check").returncode == 0


def test_the_upgraded_database_can_be_taken_back_to_0004_and_forward_again(old_database):
    dialect, url = old_database
    asyncio.run(_run(url, _donor(1, "a@example.com", dialect) + OLD_QUERIES))
    for args in (("upgrade", "head"), ("downgrade", "0004"), ("upgrade", "head"), ("check",)):
        done = _run_alembic(url, *args)
        assert done.returncode == 0, f"alembic {' '.join(args)}: {done.stdout}{done.stderr}"
    queries = asyncio.run(_fetch(url, "SELECT COUNT(*) FROM query_table WHERE user_email IN ('visitor@example.com', 'a@example.com')"))[0][0]
    assert queries == 2, "no support query is lost by going down and up again"
