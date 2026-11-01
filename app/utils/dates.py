"""Date and time helpers.

The application stores naive UTC datetimes. Use :func:`utcnow` everywhere
instead of the deprecated ``datetime.utcnow()`` so that a single helper can be
patched and audited, and so the intent (UTC) is explicit.
"""

from datetime import date, datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return the current time as a naive UTC datetime.

    Naive UTC is what the existing database columns hold; returning an aware
    datetime here would make comparisons against DB values fail.
    """

    return datetime.now(timezone.utc).replace(tzinfo=None)


def age_on(date_of_birth: Optional[date], today: Optional[date] = None) -> Optional[int]:
    """Age in whole years on ``today`` (defaults to today's local date)."""

    if date_of_birth is None:
        return None
    today = today or date.today()
    years = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


__all__ = ["utcnow", "age_on"]
