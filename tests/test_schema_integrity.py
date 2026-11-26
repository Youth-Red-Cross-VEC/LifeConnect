"""Exercise revision 0013 on pre-existing data and writes outside the ORM."""
import asyncio

import pytest
from sqlalchemy.exc import IntegrityError

from tests.test_email_migration import _run
from tests.test_migrations import _database_urls, _run_alembic
from tests.test_upgrade_from_0004 import _fetch, OLD_ADMIN


@pytest.mark.parametrize("kind", ["sqlite", "postgres"])
def test_integrity_upgrade_refuses_invalid_data_and_preserves_rows(tmp_path, kind):
    urls = dict(_database_urls(tmp_path))
    if kind not in urls:
        pytest.skip("requires disposable PostgreSQL")
    url = urls[kind]

    def migrate(*args):
        result = _run_alembic(url, *args)
        assert result.returncode == 0, result.stderr

    def sql(*statements):
        asyncio.run(_run(url, list(statements)))

    migrate("upgrade", "head")
    migrate("downgrade", "0012")
    insert = ("INSERT INTO otp_failure_windows (purpose,email,attempts,window_started_at) "
              "VALUES ('schema-test','test@example.test',-1,'2026-01-01')")
    try:
        sql(insert, OLD_ADMIN)
        refused = _run_alembic(url, "upgrade", "head")
        assert refused.returncode and "negative attempts in otp_failure_windows" in refused.stderr
        assert asyncio.run(_fetch(url, "SELECT version_num FROM alembic_version")) == [("0012",)]
        assert asyncio.run(_fetch(url, "SELECT attempts FROM otp_failure_windows WHERE purpose='schema-test'")) == [(-1,)]
        sql("UPDATE otp_failure_windows SET attempts=0 WHERE purpose='schema-test'")
        migrate("upgrade", "head")
        with pytest.raises(IntegrityError):
            sql("UPDATE otp_failure_windows SET attempts=-1 WHERE purpose='schema-test'")
        with pytest.raises(IntegrityError):
            sql(OLD_ADMIN.replace("ADM-9", "ADM-8").replace("VEC-9", "VEC-8").replace("old.admin@", "OLD.admin@"))
        migrate("downgrade", "0012")
        assert asyncio.run(_fetch(url, "SELECT attempts FROM otp_failure_windows WHERE purpose='schema-test'")) == [(0,)]
    finally:
        sql("DELETE FROM otp_failure_windows WHERE purpose='schema-test'", "DELETE FROM admin_details WHERE id='ADM-9'")
        migrate("upgrade", "head")

@pytest.mark.parametrize("kind", ["sqlite", "postgres"])
def test_private_response_index_and_both_attempt_checks_exist(tmp_path, kind):
    from sqlalchemy import inspect
    from sqlalchemy.ext.asyncio import create_async_engine

    urls = dict(_database_urls(tmp_path))
    if kind not in urls:
        pytest.skip("requires disposable PostgreSQL")
    url = urls[kind]
    result = _run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, result.stderr

    def verify(connection):
        schema = inspect(connection)
        indexes = schema.get_indexes("blood_request_details")
        assert any(i["unique"] and i["column_names"] == ["response_id"] for i in indexes)
        for table in ("otp_codes", "otp_failure_windows"):
            assert f"ck_{table}_attempts" in {item["name"] for item in schema.get_check_constraints(table)}

    async def run():
        engine = create_async_engine(url)
        try:
            async with engine.connect() as connection:
                await connection.run_sync(verify)
        finally:
            await engine.dispose()

    asyncio.run(run())
