"""Exception details are diagnostics, not API output.

The handler must keep ``error_details`` (submitted values, internal ids) server-side and hand
clients only the message plus an ``error_id`` they can quote in any environment.
"""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import LifeConnectException
from app.main import lifeconnect_exception_handler

SENSITIVE = "jane.doe@example.com"


def _app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(LifeConnectException, lifeconnect_exception_handler)

    @app.get("/boom")
    async def boom():
        raise LifeConnectException("Something went wrong", details={"email": SENSITIVE})

    return app


def _settings(debug: bool, app_env: str) -> SimpleNamespace:
    return SimpleNamespace(DEBUG=debug, APP_ENV=app_env)


async def _get() -> dict:
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://t") as c:
        response = await c.get("/boom")
    assert response.status_code == 400
    return response.json()


@pytest.mark.asyncio
async def test_production_never_returns_exception_details(monkeypatch):
    # DEBUG=true in production must still not leak: the environment gate is deliberately strict.
    monkeypatch.setattr("app.main.get_settings", lambda: _settings(True, "production"))
    body = await _get()
    assert body["detail"] == "Something went wrong"
    assert body["error_id"]
    assert "error_details" not in body
    assert SENSITIVE not in str(body)


@pytest.mark.asyncio
async def test_non_debug_responses_never_return_exception_details(monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: _settings(False, "development"))
    body = await _get()
    assert "error_details" not in body


@pytest.mark.asyncio
async def test_development_debug_also_protects_details(monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: _settings(True, "development"))
    body = await _get()
    assert "error_details" not in body and SENSITIVE not in str(body)
