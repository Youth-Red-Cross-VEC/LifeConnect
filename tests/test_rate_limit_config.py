"""P2-43: configurable rate-limit storage and default limits."""

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings, get_settings
from app.core.rate_limiter import build_limiter, limiter
from tests.test_config_validation import GOOD_KEY

PRODUCTION = dict(
    DATABASE_URL="sqlite+aiosqlite://",
    GOOGLE_MAPS_API_KEY="x",
    MAIL_SERVER="x",
    MAIL_USERNAME="x",
    MAIL_PASSWORD="x",
    MAIL_FROM="a@example.com",
    SECRET_KEY=GOOD_KEY,
    APP_ENV="production",
    RECAPTCHA_SECRET_KEY="r",
    RECAPTCHA_ENFORCED=True,
)


def test_storage_uri_defaults_to_memory_and_is_configurable(monkeypatch):
    assert Settings.model_fields["RATE_LIMIT_STORAGE_URI"].default == "memory://"
    monkeypatch.setenv("RATE_LIMIT_STORAGE_URI", "memory://custom")
    assert Settings().RATE_LIMIT_STORAGE_URI == "memory://custom"


def test_app_limiter_has_default_limit_from_settings():
    configured = [str(item.limit) for item in limiter._default_limits[0]]
    assert configured == [f"{get_settings().RATE_LIMIT_PER_MINUTE} per 1 minute"]


@pytest.mark.parametrize("bad_uri", ["memory://", "memory://custom", ""])
def test_production_refuses_per_process_rate_limit_storage(bad_uri):
    with pytest.raises(ValidationError, match="RATE_LIMIT_STORAGE_URI"):
        Settings(_env_file=None, **{**PRODUCTION, "RATE_LIMIT_STORAGE_URI": bad_uri})


def test_production_accepts_a_shared_rate_limit_store():
    settings = Settings(
        _env_file=None, **{**PRODUCTION, "RATE_LIMIT_STORAGE_URI": "redis://redis:6379/0"}
    )
    assert settings.RATE_LIMIT_STORAGE_URI == "redis://redis:6379/0"


@pytest.mark.asyncio
async def test_default_limit_applies_to_undecorated_routes():
    lim = build_limiter(2, "memory://")
    app = FastAPI()
    app.state.limiter = lim
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/ping")
    async def ping(request: Request):
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        codes = [(await c.get("/ping")).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
