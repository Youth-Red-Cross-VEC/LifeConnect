"""B8: migration 0008 adds a unique index on lower(donor_details.email) and refuses to run if it would break.

An existing database may already hold two accounts whose emails differ only by case. The migration must
stop with an redacted error (and change nothing), not silently pick one or half-apply.
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.test_migrations import _database_urls, _run_alembic

PREVIOUS = "0007"

SEED = [
    "INSERT INTO personal_details (id, first_name, age, date_of_birth, contact_number, created_at) "
    "VALUES ('PD-{n}', 'D', 30, '1994-01-01', '9000000001', '2026-01-01 00:00:00')",
    "INSERT INTO address_details (id, address, pincode, country, state, city, created_at) "
    "VALUES ('AD-{n}', '1 Street', '600001', 'India', 'TN', 'Chennai', '2026-01-01 00:00:00')",
    "INSERT INTO disease_details (id, name) VALUES ('DS-{n}', 'None')",
    "INSERT INTO terms_and_conditions (id, version, effective_date) VALUES ('TC-{n}', '1.0', '2026-01-01')",
    "INSERT INTO donor_details (id, name, email, password, blood_group, active_status, authentication_id, "
    "number_of_times_donated, personal_details_id, address_id, disease_id, terms_and_conditions_id, created_at) "
    "VALUES ('DON-{n}', 'Donor {n}', '{email}', 'x', 'O+', {active}, 'AUTH-{n}', 0, 'PD-{n}', 'AD-{n}', "
    "'DS-{n}', 'TC-{n}', '2026-01-01 00:00:00')",
]
CLEANUP = [
    "DELETE FROM donor_details WHERE id = 'DON-{n}'",
    "DELETE FROM terms_and_conditions WHERE id = 'TC-{n}'",
    "DELETE FROM disease_details WHERE id = 'DS-{n}'",
    "DELETE FROM address_details WHERE id = 'AD-{n}'",
    "DELETE FROM personal_details WHERE id = 'PD-{n}'",
]


async def _run(url: str, statements: list[str]) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            for statement in statements:
                await conn.execute(text(statement))
    finally:
        await engine.dispose()


def _donor(n: int, email: str, dialect: str) -> list[str]:
    active = "1" if dialect == "sqlite" else "true"
    return [s.format(n=n, email=email, active=active) for s in SEED]


def _remove(n: int) -> list[str]:
    return [s.format(n=n) for s in CLEANUP]


@pytest.fixture(params=["sqlite", "postgres"])
def database(request, tmp_path):
    urls = dict(_database_urls(tmp_path))
    if request.param not in urls:
        pytest.skip("set MIGRATION_TEST_DATABASE_URL to an EMPTY throwaway Postgres to test it")
    url = urls[request.param]
    for step in (("upgrade", "head"), ("downgrade", PREVIOUS)):  # a database that predates the index
        done = _run_alembic(url, *step)
        assert done.returncode == 0, done.stderr
    yield request.param, url
    asyncio.run(_run(url, _remove(1) + _remove(2) + _remove(3)))
    done = _run_alembic(url, "upgrade", "head")  # leave the shared database at head for other tests
    assert done.returncode == 0, done.stderr


def test_case_variant_duplicates_stop_the_migration_without_disclosing_accounts(database):
    dialect, url = database
    asyncio.run(_run(url, _donor(1, "Pat@Example.com", dialect) + _donor(2, "pat@example.com", dialect)))

    done = _run_alembic(url, "upgrade", "head")

    assert done.returncode != 0
    output = done.stdout + done.stderr
    assert "differ only by letter case" in output
    assert "DON-1" not in output and "DON-2" not in output
    assert "pat@example.com" not in output.lower()

    # Nothing was half-applied: the database is still at the previous revision.
    current = _run_alembic(url, "current")
    assert PREVIOUS in current.stdout + current.stderr


def test_without_duplicates_the_index_is_created_and_enforced(database):
    dialect, url = database
    asyncio.run(_run(url, _donor(1, "pat@example.com", dialect) + _donor(3, "sam@example.com", dialect)))

    done = _run_alembic(url, "upgrade", "head")
    assert done.returncode == 0, done.stderr

    with pytest.raises(IntegrityError):
        asyncio.run(_run(url, _donor(2, "PAT@EXAMPLE.COM", dialect)))


def test_the_migration_can_be_reversed_and_the_check_is_clean(database):
    dialect, url = database
    for args in (("upgrade", "head"), ("downgrade", PREVIOUS), ("upgrade", "head"), ("check",)):
        done = _run_alembic(url, *args)
        assert done.returncode == 0, f"alembic {' '.join(args)}: {done.stdout}{done.stderr}"
