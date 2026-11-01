"""Docs must match the code (P3-47..P3-50, P1-30)."""

import importlib.util
import re
import tomllib
from pathlib import Path

from app.config import Settings

ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_database_md_is_generated_from_the_models():
    spec = importlib.util.spec_from_file_location("gen_db_docs", ROOT / "scripts" / "gen_db_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert _read("docs/database.md") == module.render(), "run: python scripts/gen_db_docs.py"


def test_database_md_has_no_obsolete_table_names():
    text = _read("docs/database.md")
    for old in ("PersonalDetailsUser", "AddressDetailsUser", "DiseaseDetailsUser"):
        assert old not in text
    for table in ("personal_details", "address_details", "otp_codes", "refresh_tokens"):
        assert f"`{table}`" in text


def test_python_version_matches_pyproject():
    requires = tomllib.loads(_read("pyproject.toml"))["project"]["requires-python"]
    minimum = re.search(r"(\d+\.\d+)", requires).group(1)
    for rel in ("README.md", "docs/setup.md"):
        assert f"Python {minimum}+" in _read(rel), rel
        assert "3.10" not in _read(rel), rel
    assert f"python:{minimum}" in _read("Dockerfile")


def test_docs_do_not_advertise_sqlite_or_recharts():
    readme, setup = _read("README.md"), _read("docs/setup.md")
    assert "SQLite (Development)" not in readme and "Recharts" not in readme
    assert "default for development" not in setup and "local SQLite" not in setup
    assert "sqlite+aiosqlite" not in setup


def test_setup_env_names_exist_in_settings():
    setup = _read("docs/setup.md")
    assert "SMTP_" not in setup
    block = re.search(r"```plaintext\n(.*?)```", setup, re.S).group(1)
    names = re.findall(r"^ *([A-Z][A-Z0-9_]+)=", block, re.M)
    assert names, "expected an env example block"
    unknown = [n for n in names if n not in Settings.model_fields]
    assert not unknown, unknown


# Tables that hold no personal data and need no retention row.
RETENTION_EXEMPT = {"hospital_details", "terms_and_conditions"}


def test_retention_doc_covers_every_table_with_personal_data():
    from app.models.base import Base

    text = _read("docs/DATA_RETENTION.md")
    for table in sorted(set(Base.metadata.tables) - RETENTION_EXEMPT):
        assert f"`{table}`" in text, f"add {table} to docs/DATA_RETENTION.md"
