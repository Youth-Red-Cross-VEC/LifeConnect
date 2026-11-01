"""P2-38: the donation cooldown comes from settings, not a literal."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest

from app.config import Settings, get_settings
from app.tasks import scheduled_jobs
from tests.helpers import insert_donor


class _FakeDb:
    def __init__(self, session):
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session
        await self._session.commit()


def _settings(days: int) -> Settings:
    return get_settings().model_copy(update={"DONATION_COOLDOWN_DAYS": days})


def test_default_is_ninety_days():
    assert Settings.model_fields["DONATION_COOLDOWN_DAYS"].default == 90


@pytest.mark.asyncio
@pytest.mark.parametrize("window,reactivated", [(30, True), (90, False)])
async def test_job_uses_configured_window(test_session, monkeypatch, window, reactivated):
    donor = await insert_donor(test_session, active=True)
    donor.is_available = False
    donor.last_donated_date = datetime.now() - timedelta(days=45)
    await test_session.commit()

    monkeypatch.setattr(scheduled_jobs, "get_settings", lambda: _settings(window))
    await scheduled_jobs.activate_donor_status(_FakeDb(test_session))

    await test_session.refresh(donor)
    assert bool(donor.is_available) is reactivated
