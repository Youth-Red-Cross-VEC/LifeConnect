"""scripts/migrate_legacy_dump.py: legacy MySQL dump -> current schema."""

import importlib.util
import sqlite3

import pytest

from tests.test_migrations import ROOT, _run_alembic

FIXTURE = ROOT / "tests" / "fixtures" / "legacy_dump_sample.sql"

_spec = importlib.util.spec_from_file_location("migrate_legacy_dump", ROOT / "scripts" / "migrate_legacy_dump.py")
migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate)


def _mapped():
    return migrate.map_rows(migrate.parse_dump(FIXTURE.read_text(encoding="utf-8")))


def test_parses_and_maps_every_table():
    mapped = _mapped()
    counts = {t: len(r) for t, r in mapped.items()}
    assert counts["donor_details"] == 2
    assert counts["personal_details"] == 2
    assert counts["admin_details"] == 1
    assert counts["blood_request_details"] == 1
    assert counts["query_table"] == 1
    assert migrate.check_integrity(mapped) == []


def test_renames_columns_and_drops_aadhaar():
    mapped = _mapped()
    assert "date_of_birth" in mapped["admin_details"][0]
    assert "data_of_birth" not in mapped["admin_details"][0]
    assert all("aadhar_number" not in r for r in mapped["personal_details"])


def test_mysql_escapes_are_decoded():
    mapped = _mapped()
    assert mapped["personal_details"][0]["last_name"] == "O'Brien"
    assert mapped["address_details"][0]["address"] == "1 Sample St, Line\\2"


def test_integrity_problem_is_reported():
    mapped = _mapped()
    mapped["donor_details"][0]["address_id"] = "AD-missing"
    problems = migrate.check_integrity(mapped)
    assert len(problems) == 1 and "AD-missing" in problems[0]


def test_dry_run_is_default_and_writes_nothing(capsys):
    assert migrate.main([str(FIXTURE)]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "donor_details" in out and "Dry run only" in out


def test_apply_requires_database_url():
    with pytest.raises(SystemExit):
        migrate.main([str(FIXTURE), "--apply"])


def test_apply_imports_into_empty_migrated_db_and_refuses_second_run(tmp_path):
    db = tmp_path / "target.db"
    url = f"sqlite+aiosqlite:///{db}"
    assert _run_alembic(url, "upgrade", "head").returncode == 0

    assert migrate.main([str(FIXTURE), "--database-url", url, "--apply"]) == 0

    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM donor_details").fetchone()[0] == 2
        row = conn.execute(
            "SELECT password, active_status, last_donated_date FROM donor_details WHERE id='DNR001'"
        ).fetchone()
        assert row[0].startswith("scrypt:") and row[1] == 1 and row[2].startswith("2024-02-01")
        assert conn.execute("SELECT date_of_birth FROM admin_details").fetchone()[0] == "1990-01-01"
        assert conn.execute("SELECT created_at FROM donor_details LIMIT 1").fetchone()[0]
    finally:
        conn.close()

    with pytest.raises(SystemExit, match="already has"):
        migrate.main([str(FIXTURE), "--database-url", url, "--apply"])
