"""Manually clear any legacy Aadhaar values while retaining the nullable DB column.

Run only after reviewing a database backup: ``python scripts/purge_aadhaar.py``.
This is never called automatically by the application or migrations.
"""

import asyncio

from sqlalchemy import text

from app.config import get_settings
from app.core.database import Database


async def main() -> None:
    database = Database(get_settings().DATABASE_URL)
    try:
        async with database.session() as session:
            result = await session.execute(
                text("UPDATE personal_details SET aadhar_number = NULL WHERE aadhar_number IS NOT NULL")
            )
            print(f"Cleared Aadhaar values from {result.rowcount} row(s).")
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
