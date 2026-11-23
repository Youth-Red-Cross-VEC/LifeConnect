import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.core.middleware import CatchAllMiddleware, SecurityHeadersMiddleware


async def test_safe_headers_cover_preflight_and_validation(client):
    for response in (
        await client.options("/api/v1/auth/refresh", headers={"Origin":"http://localhost:5173", "Access-Control-Request-Method":"POST"}),
        await client.post("/api/v1/auth/donor/login", json={}),
    ):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["content-security-policy"].startswith("default-src 'none'")
        assert "no-store" in response.headers["cache-control"]
        assert "strict-transport-security" not in response.headers
        assert "x-xss-protection" not in response.headers


async def test_private_failure_is_correlatable_over_https(caplog):
    app = FastAPI()
    app.add_middleware(CatchAllMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/api/example")
    def fail():
        raise RuntimeError("synthetic-private-value")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://local.test") as client:
        response = await client.get("/api/example")
    assert response.status_code == 500
    assert response.json()["error_id"] in caplog.text
    assert "RuntimeError" in caplog.text
    assert "synthetic-private-value" not in caplog.text + response.text
    assert response.headers["strict-transport-security"] == "max-age=31536000"


@pytest.mark.parametrize("field,value", [
    ("ALGORITHM", "HS512"), ("ACCESS_TOKEN_EXPIRE_MINUTES", 0), ("REFRESH_TOKEN_EXPIRE_DAYS", 31),
    ("APP_ENV", "prodution"), ("MAIL_USE_TLS", False), ("MAIL_PASSWORD", "CHANGE_ME"),
    ("RECAPTCHA_SECRET_KEY", "CHANGE_ME"), ("RATE_LIMIT_STORAGE_URI", "memory://"),
])
def test_unsafe_production_settings_fail_before_serving(field, value):
    from pydantic import ValidationError
    from tests.test_config_validation import build
    settings = dict(APP_ENV="production", RECAPTCHA_SECRET_KEY="test-key", RECAPTCHA_ENFORCED=True,
                    RATE_LIMIT_STORAGE_URI="redis://localhost:6379/0")
    settings[field] = value
    with pytest.raises(ValidationError):
        build(**settings)
