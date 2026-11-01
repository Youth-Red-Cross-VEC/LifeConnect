"""B4: requesting a new OTP must not reset the attempt counter inside the active window."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.otp import OtpCode
from app.services.otp_service import PURPOSE_DONOR_RESET, store_otp, verify_otp

EMAIL = "donor1@example.com"


async def _row(session) -> OtpCode:
    return (await session.execute(select(OtpCode).where(OtpCode.email == EMAIL))).scalar_one()


@pytest.mark.asyncio
async def test_new_otp_keeps_attempts_inside_the_window(test_session):
    await store_otp(test_session, EMAIL, "111111", PURPOSE_DONOR_RESET)
    for _ in range(3):
        assert await verify_otp(test_session, EMAIL, "000000", PURPOSE_DONOR_RESET) is False

    await store_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET)

    assert (await _row(test_session)).attempts == 3


@pytest.mark.asyncio
async def test_total_attempts_per_window_are_capped_across_requests(test_session):
    await store_otp(test_session, EMAIL, "111111", PURPOSE_DONOR_RESET)
    for _ in range(5):  # OTP_MAX_ATTEMPTS
        assert await verify_otp(test_session, EMAIL, "000000", PURPOSE_DONOR_RESET) is False

    # Locked out: asking for a fresh code must not hand out a fresh set of guesses.
    await store_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET)
    assert await verify_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET) is False


@pytest.mark.asyncio
async def test_new_window_starts_fresh_after_expiry(test_session):
    await store_otp(test_session, EMAIL, "111111", PURPOSE_DONOR_RESET)
    for _ in range(5):
        await verify_otp(test_session, EMAIL, "000000", PURPOSE_DONOR_RESET)
    row = await _row(test_session)
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    await test_session.commit()

    await store_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET)

    assert (await _row(test_session)).attempts == 0
    assert await verify_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET) is True


@pytest.mark.asyncio
async def test_re_request_replaces_the_code_but_not_the_window(test_session):
    await store_otp(test_session, EMAIL, "111111", PURPOSE_DONOR_RESET)
    first_expiry = (await _row(test_session)).expires_at

    await store_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET)

    assert (await _row(test_session)).expires_at == first_expiry
    assert await verify_otp(test_session, EMAIL, "111111", PURPOSE_DONOR_RESET) is False  # old code is dead
    assert await verify_otp(test_session, EMAIL, "222222", PURPOSE_DONOR_RESET) is True
