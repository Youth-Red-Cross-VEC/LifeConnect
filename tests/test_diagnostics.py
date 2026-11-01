"""B11: the public health endpoint leaks nothing, and API docs are off in production."""

import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.core.database import get_db
from app.main import app, create_app

SECRET_DETAIL = "connection to server at db.internal.corp (10.1.2.3), port 5432 failed: FATAL password authentication failed for user lifeconnect_admin"


class _BrokenSession:
    async def execute(self, *args, **kwargs):
        raise ConnectionError(SECRET_DETAIL)

    async def rollback(self):
        pass


@pytest.fixture
async def broken_db_client():
    async def broken():
        yield _BrokenSession()

    app.dependency_overrides[get_db] = broken
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_hides_database_error_details(broken_db_client, caplog):
    caplog.set_level(logging.ERROR)

    response = await broken_db_client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body == {"status": "unhealthy"}
    for leaked in ("db.internal.corp", "10.1.2.3", "lifeconnect_admin", "password", "ConnectionError"):
        assert leaked not in response.text
    # ...but an operator can still find out what went wrong, in the server log.
    assert "database unreachable" in caplog.text


@pytest.mark.asyncio
async def test_health_reports_connected_when_the_database_answers(client):
    body = (await client.get("/api/v1/health")).json()
    assert body["status"] == "healthy" and body["database"] == "connected"


async def _status(application, path: str) -> int:
    async with AsyncClient(transport=ASGITransport(app=application), base_url="http://test") as c:
        return (await c.get(path)).status_code


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
async def test_docs_are_served_in_development(path):
    assert get_settings().docs_enabled is True
    assert await _status(create_app(), path) == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
async def test_docs_are_off_in_production(monkeypatch, path):
    monkeypatch.setattr(get_settings(), "APP_ENV", "production")
    assert get_settings().docs_enabled is False
    assert await _status(create_app(), path) == 404


@pytest.mark.asyncio
async def test_docs_can_be_switched_on_explicitly_in_production(monkeypatch):
    monkeypatch.setattr(get_settings(), "APP_ENV", "production")
    monkeypatch.setattr(get_settings(), "ENABLE_DOCS", True)
    assert await _status(create_app(), "/docs") == 200


@pytest.mark.asyncio
async def test_the_api_itself_still_works_when_docs_are_off(monkeypatch):
    monkeypatch.setattr(get_settings(), "ENABLE_DOCS", False)
    assert await _status(create_app(), "/api/v1/") == 200
