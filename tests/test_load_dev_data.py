"""B15: the synthetic dev seed can only be loaded into an empty, non-production database."""

import importlib.util
import sqlite3

import pytest

from app.config import get_settings
from tests.test_migrations import ROOT, _run_alembic

_spec = importlib.util.spec_from_file_location("load_dev_data", ROOT / "scripts" / "load_dev_data.py")
loader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(loader)


def _counts(path, *tables):
    conn = sqlite3.connect(path)
    try:
        return [conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables]
    finally:
        conn.close()


@pytest.fixture
def empty_db(tmp_path):
    path = tmp_path / "dev.db"
    assert _run_alembic(f"sqlite+aiosqlite:///{path}", "upgrade", "head").returncode == 0
    return path, f"sqlite+aiosqlite:///{path}"


# ------------------------------------------------------------------ the decision

@pytest.mark.parametrize("env", ["production", "Production", " PRODUCTION ", "PRODUCTION"])
def test_production_is_refused_in_any_spelling(env):
    reason = loader.refuse_reason(env, {"admin_details": 0, "donor_details": 0})
    assert reason and "production" in reason.lower()


@pytest.mark.parametrize("existing", [
    {"admin_details": 1, "donor_details": 0},
    {"admin_details": 0, "donor_details": 3},
])
def test_a_database_that_already_has_accounts_is_refused(existing):
    assert "not empty" in loader.refuse_reason("development", existing)


def test_an_empty_development_database_is_allowed():
    assert loader.refuse_reason("development", {"admin_details": 0, "donor_details": 0}) is None


# ------------------------------------------------------------------ statement splitting

def test_split_statements_respects_quotes_and_comments():
    sql = """
    -- a comment; with a semicolon
    INSERT INTO t VALUES ('a;b', 'it''s');
    INSERT INTO t VALUES ('-- not a comment');   -- trailing; comment
    INSERT INTO t VALUES (1)
    """
    assert loader.split_statements(sql) == [
        "INSERT INTO t VALUES ('a;b', 'it''s')",
        "INSERT INTO t VALUES ('-- not a comment')",
        "INSERT INTO t VALUES (1)",
    ]


# ------------------------------------------------------------------ end to end (SQLite)

def test_loads_the_bootstrap_admin_into_an_empty_database(empty_db, monkeypatch):
    path, url = empty_db
    monkeypatch.setattr(get_settings(), "APP_ENV", "development")
    from app.api.auth.utils import verify_password
    secret = "PrivateLocal123"
    monkeypatch.setenv("DEV_SEED_PASSWORD", secret)
    assert loader.main(["--database-url", url]) == 0
    assert _counts(path, "admin_details", "donor_details") == [1, 0]
    with sqlite3.connect(path) as conn:
        stored = conn.execute("SELECT password FROM admin_details").fetchone()[0]
    assert stored != secret and verify_password(secret, stored)



def test_full_flag_loads_the_synthetic_donors(empty_db, monkeypatch):
    path, url = empty_db
    monkeypatch.setattr(get_settings(), "APP_ENV", "development")
    assert loader.main(["--database-url", url, "--full"]) == 0
    assert _counts(path, "admin_details", "donor_details") == [2, 10]


def test_production_loads_nothing(empty_db, monkeypatch, capsys):
    path, url = empty_db
    monkeypatch.setattr(get_settings(), "APP_ENV", "production")
    assert loader.main(["--database-url", url]) == 2
    assert "production" in capsys.readouterr().err.lower()
    assert _counts(path, "admin_details", "donor_details") == [0, 0]


def test_a_second_load_is_refused_and_changes_nothing(empty_db, monkeypatch, capsys):
    path, url = empty_db
    monkeypatch.setattr(get_settings(), "APP_ENV", "development")
    assert loader.main(["--database-url", url]) == 0
    assert loader.main(["--database-url", url, "--full"]) == 2
    assert "not empty" in capsys.readouterr().err
    assert _counts(path, "admin_details", "donor_details") == [1, 0]


def test_a_database_with_real_looking_data_is_refused(empty_db, monkeypatch):
    path, url = empty_db
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT INTO admin_details (id, email, password, username, authentication_id, vec_registration_number, "
        "date_of_birth, mobile_number, active_status, approved_donation_count, closed_requests_count, created_at) "
        "VALUES ('ADM-1', 'real.person@hospital.org', 'x', 'Real', 'A', 'V', '1980-01-01', '1', 'Active', 0, 0, '2026-01-01')"
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(get_settings(), "APP_ENV", "development")  # e.g. a copy of production restored for testing
    assert loader.main(["--database-url", url]) == 2
    assert _counts(path, "admin_details") == [1]


# ------------------------------------------------------------------ the documentation says the same

def test_docs_point_to_the_guarded_loader_not_raw_psql():
    setup = (ROOT / "docs" / "setup.md").read_text(encoding="utf-8")
    assert "scripts/load_dev_data.py" in setup
    for name in ("initial_data.sql", "SyntheticData.sql"):
        header = (ROOT / "docs" / name).read_text(encoding="utf-8").split("\n\n", 1)[0]
        assert "scripts/load_dev_data.py" in header, f"{name} header should name the guarded loader"
