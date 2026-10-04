"""
Dedicated scheduler process: `python -m app.scheduler_worker`.

Runs the background jobs without serving HTTP. Run exactly one of these;
web workers keep SCHEDULER_ENABLED=false.
"""

import asyncio
import logging

from app.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.scheduler import start_scheduler_if_enabled

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    settings = get_settings()
    database = init_db(
        database_url=settings.DATABASE_URL,
        pool_size=2,
        max_overflow=2,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )
    scheduler = start_scheduler_if_enabled(settings, database)
    if scheduler is None:
        logger.error("SCHEDULER_ENABLED is false; the scheduler process has nothing to do")
        return
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
