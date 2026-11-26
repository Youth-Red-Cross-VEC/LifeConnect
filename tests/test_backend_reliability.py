import logging
from types import SimpleNamespace

import httpx
import pytest

from app.core import recaptcha
from app.services.distance_service import DistanceService
from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_recaptcha_network_failure_fails_closed_without_logging_secret(monkeypatch, caplog):
    secret = "synthetic-provider-secret"
    monkeypatch.setattr(recaptcha, "get_settings", lambda: SimpleNamespace(
        RECAPTCHA_SECRET_KEY=secret, APP_ENV="production"
    ))

    async def fail(*args, **kwargs):
        raise httpx.ConnectError("synthetic network failure")

    monkeypatch.setattr(httpx.AsyncClient, "post", fail)
    caplog.set_level(logging.WARNING)
    assert await recaptcha.verify_recaptcha("synthetic-token") is False
    assert secret not in caplog.text
    assert "ConnectError" in caplog.text


@pytest.mark.asyncio
async def test_distance_network_failure_returns_unavailable_without_location_logging(monkeypatch, caplog):
    async def fail(*args, **kwargs):
        raise httpx.ReadTimeout("provider timed out")

    monkeypatch.setattr(httpx.AsyncClient, "get", fail)
    caplog.set_level(logging.WARNING)
    result = await DistanceService(SimpleNamespace(
        GOOGLE_MAPS_API_KEY="synthetic-key", GOOGLE_MAPS_BASE_URL="https://maps.invalid"
    )).get_distance("Synthetic private origin", "Synthetic private destination")
    assert result is None
    assert "Synthetic private" not in caplog.text
    assert "ReadTimeout" in caplog.text


@pytest.mark.asyncio
async def test_smtp_connection_failure_closes_transport_and_returns_zero(monkeypatch):
    closed = []
    class SMTP:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 10
            self.closed = False

        async def connect(self):
            raise OSError("synthetic connection failure")

        def close(self):
            closed.append(True)

    monkeypatch.setattr("app.services.email_service.aiosmtplib.SMTP", SMTP)
    service = EmailService(SimpleNamespace(
        MAIL_SERVER="mail.invalid", MAIL_PORT=587, MAIL_USE_TLS=True, MAIL_USERNAME="", MAIL_PASSWORD=""
    ))
    result = await service.send_many([{
        "to": "recipient@example.test", "subject": "test", "html_body": "test"
    }])
    assert result == 0
    assert closed == [True]

@pytest.mark.asyncio
async def test_recaptcha_malformed_reply_then_recovery(monkeypatch):
    monkeypatch.setattr(recaptcha, "get_settings", lambda: SimpleNamespace(
        RECAPTCHA_SECRET_KEY="synthetic", APP_ENV="test"
    ))
    replies = iter([[], {"success": True, "score": True}, {"success": True, "score": .9, "action": "login"}])
    async def reply(*args, **kwargs):
        return httpx.Response(200, json=next(replies), request=httpx.Request("POST", "https://provider.invalid"))
    monkeypatch.setattr(httpx.AsyncClient, "post", reply)
    assert not await recaptcha.verify_recaptcha("test", "login")
    assert not await recaptcha.verify_recaptcha("test", "login")
    assert await recaptcha.verify_recaptcha("test", "login")


@pytest.mark.asyncio
async def test_distance_malformed_reply_then_recovery(monkeypatch):
    replies = iter([{"status": "OK", "rows": [None]}, {"status": "OK", "rows": [
        {"elements": [{"status": "OK", "distance": {"value": 750, "text": "750 m"}}]}
    ]}])
    async def reply(*args, **kwargs):
        return httpx.Response(200, json=next(replies))
    monkeypatch.setattr(httpx.AsyncClient, "get", reply)
    service = DistanceService(SimpleNamespace(GOOGLE_MAPS_API_KEY="test", GOOGLE_MAPS_BASE_URL="https://provider.invalid"))
    assert await service.get_distance("a", "b") is None
    assert await service.get_distance("a", "b") == .75


@pytest.mark.asyncio
async def test_pool_closed_on_scheduler_startup_failure(monkeypatch):
    import app.main as main
    from unittest.mock import AsyncMock
    pool = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(main, "init_db", lambda **kwargs: pool)
    def fail(*args):
        raise RuntimeError("startup failed")
    monkeypatch.setattr(main, "start_scheduler_if_enabled", fail)
    with pytest.raises(RuntimeError, match="startup failed"):
        async with main.lifespan(main.app):
            pytest.fail("startup should have failed")
    pool.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_rollback_invalidates_session_and_preserves_original_error():
    from unittest.mock import AsyncMock, MagicMock
    from app.core.database import Database
    session = AsyncMock()
    session.rollback.side_effect = ConnectionError("secondary failure")
    manager = MagicMock()
    manager.__aenter__.return_value = session
    database = Database.__new__(Database)
    database.session_factory = lambda: manager
    with pytest.raises(ValueError, match="original failure"):
        async with database.session():
            raise ValueError("original failure")
    session.invalidate.assert_awaited_once()
    manager.__aexit__.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["running", "shutdown"])
async def test_lifespan_closes_owned_pool_even_on_failure(monkeypatch, stage):
    from unittest.mock import AsyncMock, Mock
    import app.main as main

    pool = SimpleNamespace(close=AsyncMock())
    scheduler = Mock()
    monkeypatch.setattr(main, "init_db", lambda **kwargs: pool)
    monkeypatch.setattr(main, "start_scheduler_if_enabled", lambda *args: scheduler)
    if stage == "shutdown":
        scheduler.shutdown.side_effect = RuntimeError(stage)
    with pytest.raises(RuntimeError, match=stage):
        async with main.lifespan(main.app):
            if stage == "running":
                raise RuntimeError(stage)
    scheduler.shutdown.assert_called_once()
    pool.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_provider_error_uses_503_and_correlation_id():
    import json
    from app.core.exceptions import ExternalServiceError
    from app.main import lifeconnect_exception_handler

    response = await lifeconnect_exception_handler(None, ExternalServiceError("synthetic", "private marker"))
    body = json.loads(response.body)
    assert response.status_code == 503
    assert body["error_id"] and "private marker" not in str(body)

@pytest.mark.asyncio
async def test_login_recovers_after_transient_failure(client, test_session, monkeypatch, caplog):
    import importlib
    from tests.helpers import insert_donor

    router = importlib.import_module("app.api.auth.router")
    await insert_donor(test_session)
    credentials = {"email": "donor1@example.com", "password": "Secret123"}
    async def fail(*args):
        raise RuntimeError("private test marker")

    with monkeypatch.context() as scoped:
        scoped.setattr(router, "verify_password_async", fail)
        response = await client.post("/api/v1/auth/donor/login", json=credentials)
    assert response.status_code == 500
    assert response.json()["error_id"] in caplog.text
    assert "private test marker" not in caplog.text + response.text
    recovered = await client.post("/api/v1/auth/donor/login", json=credentials)
    assert recovered.status_code == 200
