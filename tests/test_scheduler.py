"""Scheduler must be opt-in per process and jobs must not double-run."""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.core.scheduler import start_scheduler_if_enabled
from app.tasks.scheduled_jobs import try_job_lock

BASE = dict(
    DATABASE_URL="sqlite+aiosqlite://", SECRET_KEY="k" * 40, GOOGLE_MAPS_API_KEY="x",
    MAIL_SERVER="x", MAIL_USERNAME="x", MAIL_PASSWORD="x", MAIL_FROM="a@example.com",
)


def test_scheduler_disabled_by_default():
    assert Settings(**BASE).SCHEDULER_ENABLED is False


@pytest.mark.asyncio
async def test_scheduler_not_started_when_disabled():
    assert start_scheduler_if_enabled(Settings(**BASE), object()) is None


@pytest.mark.asyncio
async def test_scheduler_started_when_enabled():
    from app.core import scheduler as sched_mod

    started = start_scheduler_if_enabled(Settings(**BASE, SCHEDULER_ENABLED=True), object())
    try:
        assert started is not None
        assert {"expire_blood_requests", "activate_donor_status", "increment_donor_ages"} <= set(
            started.get_jobs()
        )
    finally:
        started.shutdown()
        sched_mod.scheduler = None


@pytest.mark.asyncio
async def test_job_lock_is_noop_on_sqlite(test_session):
    assert await try_job_lock(test_session, "expire_blood_requests") is True
    assert await try_job_lock(test_session, "expire_blood_requests") is True


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("MIGRATION_TEST_DATABASE_URL"),
    reason="needs a throwaway Postgres (MIGRATION_TEST_DATABASE_URL)",
)
async def test_second_instance_cannot_take_the_same_job_lock():
    engine = create_async_engine(os.environ["MIGRATION_TEST_DATABASE_URL"])
    factory = async_sessionmaker(engine, class_=AsyncSession)
    try:
        async with factory() as first, factory() as second:
            assert await try_job_lock(first, "expire_blood_requests") is True
            assert await try_job_lock(second, "expire_blood_requests") is False
            assert await try_job_lock(second, "activate_donor_status") is True  # different job
            await first.commit()  # releases the transaction-level lock
            assert await try_job_lock(second, "expire_blood_requests") is True
    finally:
        await engine.dispose()
