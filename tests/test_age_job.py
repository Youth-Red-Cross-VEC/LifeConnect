"""Ages are derived from the date of birth, never incremented by a nightly job."""

from datetime import date

import pytest

from app.core.scheduler import Scheduler
from app.tasks.scheduled_jobs import setup_scheduled_jobs
from app.utils.dates import age_on


# ------------------------------------------------------------------ the age rule

@pytest.mark.parametrize("born,today,expected", [
    (date(1990, 6, 15), date(2026, 6, 14), 35),  # the day before the birthday
    (date(1990, 6, 15), date(2026, 6, 15), 36),  # the birthday itself
    (date(1990, 6, 15), date(2026, 6, 16), 36),  # after
    (date(1990, 12, 31), date(2026, 1, 1), 35),
    (date(1990, 1, 1), date(2026, 12, 31), 36),
])
def test_age_on_ordinary_birthdays(born, today, expected):
    assert age_on(born, today) == expected


@pytest.mark.parametrize("today,expected", [
    (date(2023, 2, 27), 22),
    (date(2023, 2, 28), 22),  # non-leap year: not a year older yet on 28 February
    (date(2023, 3, 1), 23),   # ...but on 1 March, the documented choice
    (date(2024, 2, 28), 23),
    (date(2024, 2, 29), 24),  # leap year: on the real day
    (date(2024, 3, 1), 24),
    (date(2025, 2, 28), 24),
    (date(2025, 3, 1), 25),
])
def test_age_on_for_a_leap_day_birthday(today, expected):
    assert age_on(date(2000, 2, 29), today) == expected


def test_age_on_without_a_date_of_birth():
    assert age_on(None, date(2026, 1, 1)) is None


# ------------------------------------------------------------------ job registration

@pytest.mark.asyncio
async def test_jobs_tolerate_a_late_start_and_never_overlap():
    scheduler = Scheduler()
    setup_scheduled_jobs(scheduler, db=object())
    scheduler.start()  # job defaults are applied when the scheduler starts
    try:
        jobs = scheduler.scheduler.get_jobs()
        assert {j.id for j in jobs} >= {"expire_blood_requests", "activate_donor_status"}
        assert "increment_donor_ages" not in {j.id for j in jobs}
        for job in jobs:
            # APScheduler's default grace is 1 second: a restart a moment after midnight would skip the day.
            assert job.misfire_grace_time is not None and job.misfire_grace_time >= 3600, job.id
            assert job.coalesce is True, job.id
            assert job.max_instances == 1, job.id
    finally:
        scheduler.shutdown()
