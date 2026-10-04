"""Seed SQL under docs/ must be synthetic and load into the current schema."""

import re
import sqlite3
from pathlib import Path

import pytest

from tests.test_migrations import ROOT, _run_alembic

SEED_FILES = ["docs/initial_data.sql", "docs/SyntheticData.sql"]


@pytest.mark.parametrize("path", SEED_FILES)
def test_seed_contains_only_synthetic_identities(path):
    sql = (ROOT / path).read_text(encoding="utf-8")
    emails = set(re.findall(r"[\w.+-]+@[\w.-]+\.\w+", sql))
    assert emails, "seed file should contain sample accounts"
    assert all(e.endswith("@example.com") for e in emails), emails
    assert "scrypt:" not in sql  # legacy hashes of real accounts must not be shipped


def test_seed_files_load_into_migrated_schema(tmp_path):
    db = tmp_path / "seed.db"
    assert _run_alembic(f"sqlite+aiosqlite:///{db}", "upgrade", "head").returncode == 0
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for path in SEED_FILES:
            if path.endswith("initial_data.sql"):
                continue  # bootstrap admin duplicates a row in SyntheticData.sql
            conn.executescript((ROOT / path).read_text(encoding="utf-8"))
        assert conn.execute("SELECT COUNT(*) FROM donor_details").fetchone()[0] == 10
        assert conn.execute("SELECT COUNT(*) FROM admin_details").fetchone()[0] == 2
    finally:
        conn.close()

    fresh = tmp_path / "bootstrap.db"
    assert _run_alembic(f"sqlite+aiosqlite:///{fresh}", "upgrade", "head").returncode == 0
    conn = sqlite3.connect(fresh)
    try:
        conn.executescript((ROOT / "docs/initial_data.sql").read_text(encoding="utf-8"))
        assert conn.execute("SELECT COUNT(*) FROM admin_details").fetchone()[0] == 1
    finally:
        conn.close()


def test_dev_password_hash_matches_documented_password():
    from app.api.auth.utils import verify_password

    sql = (ROOT / "docs/SyntheticData.sql").read_text(encoding="utf-8")
    hashes = set(re.findall(r"\$2b\$12\$[./A-Za-z0-9]{53}", sql))
    assert len(hashes) == 1
    assert verify_password("DevOnly#2026", hashes.pop())
