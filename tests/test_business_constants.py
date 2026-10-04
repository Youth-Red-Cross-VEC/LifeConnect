"""P3-59: business constants come from settings, not literals scattered through the code."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.config import Settings, get_settings
from app.core.rate_limiter import limiter
from app.models.otp import OtpCode
from app.services import otp_service


def test_defaults():
    f = Settings.model_fields
    assert f["OTP_TTL_SECONDS"].default == 600
    assert f["OTP_MAX_ATTEMPTS"].default == 5
    assert f["AUTH_RATE_LIMIT"].default == "5/minute"
    assert f["PASSWORD_RESET_RATE_LIMIT"].default == "3/minute"


def _limits_for(func_name: str) -> list[str]:
    import app.api.auth.router  # noqa: F401  (registers the route limits)

    return [str(lim.limit) for lim in limiter._route_limits[f"app.api.auth.router.{func_name}"]]


@pytest.mark.parametrize("func,setting", [
    ("donor_login", "AUTH_RATE_LIMIT"),
    ("admin_login", "AUTH_RATE_LIMIT"),
    ("request_donor_password_reset", "PASSWORD_RESET_RATE_LIMIT"),
    ("request_admin_password_reset", "PASSWORD_RESET_RATE_LIMIT"),
])
def test_auth_routes_use_configured_limits(func, setting):
    expected = {"AUTH_RATE_LIMIT": "5 per 1 minute", "PASSWORD_RESET_RATE_LIMIT": "3 per 1 minute"}[setting]
    assert _limits_for(func) == [expected]


@pytest.mark.asyncio
async def test_otp_ttl_and_attempts_follow_settings(test_session, monkeypatch):
    custom = get_settings().model_copy(update={"OTP_TTL_SECONDS": 30, "OTP_MAX_ATTEMPTS": 2})
    monkeypatch.setattr(otp_service, "get_settings", lambda: custom)

    before = datetime.utcnow()
    await otp_service.store_otp(test_session, "z@example.com", "123456", otp_service.PURPOSE_DONOR_RESET)
    row = (await test_session.execute(select(OtpCode))).scalar_one()
    assert timedelta(seconds=25) < row.expires_at - before < timedelta(seconds=35)

    for _ in range(2):
        assert not await otp_service.verify_otp(test_session, "z@example.com", "000000", otp_service.PURPOSE_DONOR_RESET)
    assert not await otp_service.verify_otp(test_session, "z@example.com", "123456", otp_service.PURPOSE_DONOR_RESET)
