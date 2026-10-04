#!/usr/bin/env python
"""
Migrate data from a legacy MySQL dump (old Flask schema) into the current schema.

    python scripts/migrate_legacy_dump.py path/to/dump.sql                 # dry run (default)
    python scripts/migrate_legacy_dump.py dump.sql --database-url URL --apply

* Dry run parses the dump, maps old tables/columns to the new ones, checks
  foreign-key integrity and prints row counts. It never touches a database.
* --apply writes into an EMPTY, already-migrated target database
  (`alembic upgrade head` first). It refuses to run if any target table has rows.
* Password hashes are copied unchanged: legacy `scrypt:` hashes keep working and are
  upgraded to bcrypt on first login.
* aadhar_number is intentionally NOT migrated (the application no longer stores it).
* Never commit a real dump. Keep dumps out of the repository.
"""

import argparse
import asyncio
import re
import sys
from collections import defaultdict
from datetime import date, datetime, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# old table -> (new table, {old column: new column}, columns to drop)
TABLE_MAP = {
    "termsandconditions": ("terms_and_conditions", {}, set()),
    "personaldetailsuser": ("personal_details", {}, {"aadhar_number"}),
    "addressdetailsuser": ("address_details", {}, set()),
    "diseasedetailsuser": ("disease_details", {}, set()),
    "hospitaldetails": ("hospital_details", {}, set()),
    "admindetails": ("admin_details", {"data_of_birth": "date_of_birth"}, set()),
    "donordetail": ("donor_details", {}, set()),
    "responsedetails": ("response_details", {}, set()),
    "bloodrequestdetails": ("blood_request_details", {}, set()),
    "querytable": ("query_table", {}, set()),
    "authenticationdetailsadmin": ("authentication_details_admin", {}, set()),
    "authenticationdetailsdonor": ("authentication_details_donor", {}, set()),
}
# insertion order that satisfies foreign keys
INSERT_ORDER = [v[0] for v in TABLE_MAP.values()]

# (table, column, parent table) integrity checks
FOREIGN_KEYS = [
    ("donor_details", "personal_details_id", "personal_details"),
    ("donor_details", "address_id", "address_details"),
    ("donor_details", "disease_id", "disease_details"),
    ("donor_details", "terms_and_conditions_id", "terms_and_conditions"),
    ("blood_request_details", "hospital_id", "hospital_details"),
    ("blood_request_details", "response_id", "response_details"),
]


# ---------------------------------------------------------------- parsing

_CREATE_RE = re.compile(r"CREATE TABLE `(\w+)` \((.*?)\n\) ENGINE", re.S)
_COL_RE = re.compile(r"^\s*`(\w+)`\s", re.M)
_INSERT_RE = re.compile(r"INSERT INTO `(\w+)` VALUES ", re.I)
_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "Z": "\x1a", "b": "\b"}


def parse_columns(sql: str) -> dict[str, list[str]]:
    cols = {}
    for table, body in _CREATE_RE.findall(sql):
        cols[table.lower()] = [c for c in _COL_RE.findall(body)]
    return cols


def _parse_values(sql: str, pos: int):
    """Parse '(...),(...);' starting at pos. Returns (rows, new_pos)."""
    rows, row, i, n = [], None, pos, len(sql)
    while i < n:
        ch = sql[i]
        if row is None:
            if ch == "(":
                row = []
                i += 1
            elif ch == ";":
                return rows, i + 1
            else:
                i += 1
            continue
        if ch in " \n\r\t":
            i += 1
        elif ch == ",":
            i += 1
        elif ch == ")":
            rows.append(row)
            row = None
            i += 1
        elif ch == "'":
            i += 1
            buf = []
            while i < n:
                c = sql[i]
                if c == "\\" and i + 1 < n:
                    buf.append(_ESCAPES.get(sql[i + 1], sql[i + 1]))
                    i += 2
                elif c == "'" and i + 1 < n and sql[i + 1] == "'":
                    buf.append("'")
                    i += 2
                elif c == "'":
                    i += 1
                    break
                else:
                    buf.append(c)
                    i += 1
            row.append("".join(buf))
        else:
            j = i
            while j < n and sql[j] not in ",)":
                j += 1
            token = sql[i:j].strip()
            row.append(None if token.upper() == "NULL" else token)
            i = j
    return rows, i


def parse_dump(sql: str) -> dict[str, list[dict]]:
    """Return {old_table: [ {column: raw_value} ]}."""
    columns = parse_columns(sql)
    data = defaultdict(list)
    for m in _INSERT_RE.finditer(sql):
        table = m.group(1).lower()
        if table not in columns:
            continue
        rows, _ = _parse_values(sql, m.end())
        for r in rows:
            if len(r) != len(columns[table]):
                raise ValueError(f"{table}: row has {len(r)} values, expected {len(columns[table])}")
            data[table].append(dict(zip(columns[table], r)))
    return data


# ---------------------------------------------------------------- mapping

def map_rows(old_data: dict[str, list[dict]]) -> dict[str, list[dict]]:
    mapped = {}
    for old, (new, renames, drops) in TABLE_MAP.items():
        rows = []
        for row in old_data.get(old, []):
            rows.append({renames.get(k, k): v for k, v in row.items() if k not in drops})
        mapped[new] = rows
    return mapped


def check_integrity(mapped: dict[str, list[dict]]) -> list[str]:
    problems = []
    ids = {t: {r.get("id") for r in rows} for t, rows in mapped.items()}
    for table, col, parent in FOREIGN_KEYS:
        for r in mapped.get(table, []):
            if r.get(col) not in ids.get(parent, set()):
                problems.append(f"{table}[{r.get('id')}].{col} -> missing {parent} '{r.get(col)}'")
    return problems


def coerce(table, row: dict) -> dict:
    """Convert raw dump strings to Python types per target column type."""
    out = {}
    for name, value in row.items():
        col = table.c[name]
        if value is None:
            out[name] = None
            continue
        t = col.type.python_type
        if t is bool:
            out[name] = bool(int(value))
        elif t is int:
            out[name] = int(value)
        elif t is datetime:
            out[name] = datetime.fromisoformat(value)
        elif t is date:
            out[name] = date.fromisoformat(value)
        elif t is time:
            out[name] = time.fromisoformat(value)
        else:
            out[name] = value
    if "created_at" in table.c and "created_at" not in out:
        out["created_at"] = datetime.utcnow()
    return out


# ---------------------------------------------------------------- apply

async def apply(mapped: dict[str, list[dict]], database_url: str) -> None:
    from sqlalchemy import func, insert, select
    from sqlalchemy.ext.asyncio import create_async_engine

    import app.models  # noqa: F401
    from app.models.base import Base

    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            for name in INSERT_ORDER:
                table = Base.metadata.tables[name]
                count = (await conn.execute(select(func.count()).select_from(table))).scalar()
                if count:
                    raise SystemExit(f"Refusing to apply: target table '{name}' already has {count} rows")
            for name in INSERT_ORDER:
                table = Base.metadata.tables[name]
                rows = [coerce(table, r) for r in mapped[name]]
                if rows:
                    await conn.execute(insert(table), rows)
    finally:
        await engine.dispose()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dump", type=Path, help="path to the legacy MySQL dump (.sql)")
    parser.add_argument("--database-url", help="target DB (async URL); required with --apply")
    parser.add_argument("--apply", action="store_true", help="write to the target DB (default: dry run)")
    args = parser.parse_args(argv)

    if args.apply and not args.database_url:
        parser.error("--apply requires --database-url")

    mapped = map_rows(parse_dump(args.dump.read_text(encoding="utf-8")))
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"[{mode}] rows found per target table:")
    for name in INSERT_ORDER:
        print(f"  {name:32s} {len(mapped[name])}")

    problems = check_integrity(mapped)
    if problems:
        print(f"\n{len(problems)} integrity problem(s):")
        for p in problems[:50]:
            print("  -", p)
        return 1

    if args.apply:
        asyncio.run(apply(mapped, args.database_url))
        print("\nApplied.")
    else:
        print("\nDry run only: nothing was written. Re-run with --apply --database-url ... to import.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
