"""Aadhaar numbers are no longer collected, stored or returned (P2-40)."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.models.donor import PersonalDetails
from tests.test_migrations import _run_alembic


def test_model_has_no_aadhaar_column():
    assert "aadhar_number" not in PersonalDetails.__table__.columns


@pytest.mark.asyncio
async def test_register_rejects_and_never_returns_aadhaar(client: AsyncClient, verified_registration):
    payload = {
        "name": "No Aadhaar", "email": "noaadhaar@example.com", "password": "SecurePass123",
        "blood_group": "O+",
        "personal_details": {
            "first_name": "No", "last_name": "Aadhaar", "age": 25, "date_of_birth": "1999-01-15",
            "contact_number": "+919876543210", "aadhar_number": "123412341234",
        },
        "address_details": {
            "address": "123 Test Street", "pincode": "600001", "country": "India",
            "state": "TN", "city": "Chennai",
        },
        "disease_details": {"name": "None"},
    }
    r = await verified_registration(client, payload)
    assert r.status_code == 422
    assert "123412341234" not in r.text
    del payload["personal_details"]["aadhar_number"]
    registered = await verified_registration(client, payload)
    assert registered.status_code == 201 and "aadhar" not in registered.text.lower()


def _seed_aadhaar(db_path, value):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO personal_details (id, first_name, age, date_of_birth, contact_number, "
            "aadhar_number, created_at) VALUES ('PD-1', 'A', 30, '1990-01-01', '9000000000', ?, '2026-01-01')",
            (value,),
        )
        conn.commit()
    finally:
        conn.close()


def _columns(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(personal_details)")}
    finally:
        conn.close()


def _aadhaar_values(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return [r[0] for r in conn.execute("SELECT aadhar_number FROM personal_details")]
    finally:
        conn.close()


def test_upgrade_head_on_empty_db_keeps_chain_unblocked(tmp_path):
    url = f"sqlite+aiosqlite:///{tmp_path / 'e.db'}"
    assert _run_alembic(url, "upgrade", "head").returncode == 0
    assert _run_alembic(url, "check").returncode == 0


def test_db_at_0004_with_aadhaar_values_upgrades_to_head_without_errors(tmp_path, monkeypatch):
    """Regression: a destructive guard in the chain used to block 0006+ (audit log table)."""
    db = tmp_path / "a.db"
    url = f"sqlite+aiosqlite:///{db}"
    assert _run_alembic(url, "upgrade", "0004").returncode == 0
    _seed_aadhaar(db, "123412341234")

    monkeypatch.delenv("LIFECONNECT_ALLOW_AADHAAR_DROP", raising=False)
    result = _run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db)
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert "admin_audit_log" in tables, "later migrations must have run"
    assert _aadhaar_values(db) == ["123412341234"], "automatic upgrade must never destroy data"
    # the column left behind is intentional and must not count as drift
    assert _run_alembic(url, "check").returncode == 0


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "drop_aadhaar_column.py"


def _drop(db, *args, allow=True):
    env = {k: v for k, v in os.environ.items() if k != "LIFECONNECT_ALLOW_AADHAAR_DROP"}
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{db}"
    if allow:
        env["LIFECONNECT_ALLOW_AADHAAR_DROP"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True, timeout=60
    )


def _migrated_db_with_value(tmp_path):
    db = tmp_path / "d.db"
    assert _run_alembic(f"sqlite+aiosqlite:///{db}", "upgrade", "head").returncode == 0
    _seed_aadhaar(db, "123412341234")
    return db


def test_drop_script_refuses_without_env_flag(tmp_path):
    db = _migrated_db_with_value(tmp_path)
    r = _drop(db, "--i-have-a-backup", allow=False)
    assert r.returncode == 2 and "1 row(s)" in r.stdout
    assert "aadhar_number" in _columns(db)


def test_drop_script_refuses_without_backup_confirmation(tmp_path):
    db = _migrated_db_with_value(tmp_path)
    r = _drop(db)
    assert r.returncode == 2 and "--i-have-a-backup" in r.stderr
    assert _aadhaar_values(db) == ["123412341234"]


def test_drop_script_drops_when_fully_confirmed_and_rerun_is_a_noop(tmp_path):
    db = _migrated_db_with_value(tmp_path)
    r = _drop(db, "--i-have-a-backup")
    assert r.returncode == 0 and "Dropped" in r.stdout
    assert "aadhar_number" not in _columns(db)
    again = _drop(db, "--i-have-a-backup")
    assert again.returncode == 0 and "nothing to do" in again.stdout
    # the migration chain still works on a database where the column is already gone
    url = f"sqlite+aiosqlite:///{db}"
    assert _run_alembic(url, "upgrade", "head").returncode == 0
    assert _run_alembic(url, "check").returncode == 0
