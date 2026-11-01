"""P3-57: expired one-time codes and refresh sessions are purged by a scheduled job."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.scheduler import Scheduler
from app.models.otp import OtpCode
from app.models.refresh_session import RefreshSession
from app.tasks import scheduled_jobs


class _FakeDb:
    def __init__(self, session):
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session
        await self._session.commit()


@pytest.mark.asyncio
async def test_job_removes_only_expired_rows(test_session):
    now = datetime.utcnow()
    test_session.add_all([
        OtpCode(purpose="admin_invite", email="old@example.com", code_hmac="h", expires_at=now - timedelta(minutes=1)),
        OtpCode(purpose="admin_invite", email="new@example.com", code_hmac="h", expires_at=now + timedelta(minutes=5)),
        RefreshSession(jti="old", user_id="DON-1", role="donor", expires_at=now - timedelta(days=1)),
        RefreshSession(jti="live", user_id="DON-1", role="donor", expires_at=now + timedelta(days=1)),
    ])
    await test_session.commit()

    await scheduled_jobs.purge_expired_auth_records(_FakeDb(test_session))

    assert [o.email for o in (await test_session.execute(select(OtpCode))).scalars()] == ["new@example.com"]
    assert [r.jti for r in (await test_session.execute(select(RefreshSession))).scalars()] == ["live"]


def test_job_is_registered():
    sched = Scheduler()
    scheduled_jobs.setup_scheduled_jobs(sched, object())
    assert "purge_expired_auth_records" in sched.get_jobs()
