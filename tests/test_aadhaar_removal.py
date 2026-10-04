"""Aadhaar numbers are no longer collected, stored or returned (P2-40)."""

import sqlite3

import pytest
from httpx import AsyncClient

from app.models.donor import PersonalDetails
from tests.test_migrations import _run_alembic


def test_model_has_no_aadhaar_column():
    assert "aadhar_number" not in PersonalDetails.__table__.columns


@pytest.mark.asyncio
async def test_register_ignores_and_never_returns_aadhaar(client: AsyncClient):
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
    r = await client.post("/api/v1/donors/register", json=payload)
    assert r.status_code == 201
    assert "123412341234" not in r.text and "aadhar" not in r.text.lower()


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


def test_drop_migration_refuses_when_data_present(tmp_path, monkeypatch):
    db = tmp_path / "a.db"
    url = f"sqlite+aiosqlite:///{db}"
    assert _run_alembic(url, "upgrade", "0004").returncode == 0
    _seed_aadhaar(db, "123412341234")

    monkeypatch.delenv("LIFECONNECT_ALLOW_AADHAAR_DROP", raising=False)
    refused = _run_alembic(url, "upgrade", "head")
    assert refused.returncode != 0 and "Refusing to drop" in refused.stderr
    assert "aadhar_number" in _columns(db)


def test_drop_migration_runs_when_explicitly_allowed(tmp_path, monkeypatch):
    db = tmp_path / "b.db"
    url = f"sqlite+aiosqlite:///{db}"
    assert _run_alembic(url, "upgrade", "0004").returncode == 0
    _seed_aadhaar(db, "123412341234")

    monkeypatch.setenv("LIFECONNECT_ALLOW_AADHAAR_DROP", "1")
    assert _run_alembic(url, "upgrade", "head").returncode == 0
    assert "aadhar_number" not in _columns(db)


def test_drop_migration_is_silent_on_empty_column(tmp_path, monkeypatch):
    db = tmp_path / "c.db"
    url = f"sqlite+aiosqlite:///{db}"
    assert _run_alembic(url, "upgrade", "0004").returncode == 0
    _seed_aadhaar(db, None)
    monkeypatch.delenv("LIFECONNECT_ALLOW_AADHAAR_DROP", raising=False)
    assert _run_alembic(url, "upgrade", "head").returncode == 0
