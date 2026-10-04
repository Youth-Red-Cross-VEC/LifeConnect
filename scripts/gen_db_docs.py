"""Regenerate docs/database.md from the ORM metadata.

    python scripts/gen_db_docs.py          # rewrite docs/database.md
    python scripts/gen_db_docs.py --check  # exit 1 if the file is out of date

The settings object needs no environment here: only the model classes are imported.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.models  # noqa: E402,F401  (registers every table)
from app.models.base import Base  # noqa: E402

TARGET = ROOT / "docs" / "database.md"

INTRO = """# Database Structure

This document is generated from the SQLAlchemy models in `app/models/` by
`python scripts/gen_db_docs.py` (a test fails if it drifts). The schema itself is created by
Alembic migrations (`alembic upgrade head`); PostgreSQL is the supported database. SQLite is used
only by the automated test suite.

Status columns are plain strings or booleans; blood request statuses and their allowed
transitions are defined in `app/core/request_status.py`.
"""


def render() -> str:
    out = [INTRO]
    for name in sorted(Base.metadata.tables):
        table = Base.metadata.tables[name]
        out.append(f"\n## `{name}`\n")
        out.append("| Column | Type | Nullable | Notes |")
        out.append("| ------ | ---- | -------- | ----- |")
        for col in table.columns:
            notes = []
            if col.primary_key:
                notes.append("primary key")
            if col.unique:
                notes.append("unique")
            if col.index and not col.unique:
                notes.append("indexed")
            for fk in col.foreign_keys:
                notes.append(f"FK -> `{fk.column.table.name}.{fk.column.name}`")
            out.append(f"| {col.name} | {col.type} | {'yes' if col.nullable else 'no'} | {', '.join(notes)} |")
        checks = [c.name for c in table.constraints if c.__class__.__name__ == "CheckConstraint" and c.name]
        if checks:
            out.append("\nCheck constraints: " + ", ".join(f"`{c}`" for c in checks))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    text = render()
    if "--check" in sys.argv:
        sys.exit(0 if TARGET.read_text(encoding="utf-8") == text else 1)
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET}")
