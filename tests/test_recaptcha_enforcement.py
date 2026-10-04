"""Login must reject missing/invalid reCAPTCHA tokens when RECAPTCHA_ENFORCED=true (P1-16)."""

import pytest
from httpx import AsyncClient

import importlib

auth_router = importlib.import_module("app.api.auth.router")
from app.config import get_settings
from tests.helpers import insert_donor


@pytest.fixture
def enforced(monkeypatch):
    monkeypatch.setattr(get_settings(), "RECAPTCHA_ENFORCED", True)


def _stub_verify(monkeypatch, result: bool):
    calls = []

    async def fake(token, action=None):
        calls.append((token, action))
        return result

    monkeypatch.setattr(auth_router, "verify_recaptcha", fake)
    return calls


CREDS = {"email": "donor1@example.com", "password": "Secret123"}


@pytest.mark.asyncio
async def test_not_enforced_by_default_login_works_without_token(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    assert get_settings().RECAPTCHA_ENFORCED is False
    assert (await client.post("/api/v1/auth/donor/login", json=CREDS)).status_code == 200


@pytest.mark.asyncio
async def test_enforced_missing_token_is_rejected(client: AsyncClient, test_session, enforced, monkeypatch):
    await insert_donor(test_session, 1)
    calls = _stub_verify(monkeypatch, True)
    response = await client.post("/api/v1/auth/donor/login", json=CREDS)
    assert response.status_code == 400
    assert calls == []  # never even reaches Google without a token


@pytest.mark.asyncio
async def test_enforced_invalid_token_is_rejected(client: AsyncClient, test_session, enforced, monkeypatch):
    await insert_donor(test_session, 1)
    _stub_verify(monkeypatch, False)
    response = await client.post("/api/v1/auth/donor/login", json={**CREDS, "recaptcha_token": "bad"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_enforced_valid_token_allows_login_and_checks_action(client: AsyncClient, test_session, enforced, monkeypatch):
    await insert_donor(test_session, 1)
    calls = _stub_verify(monkeypatch, True)
    response = await client.post("/api/v1/auth/donor/login", json={**CREDS, "recaptcha_token": "good"})
    assert response.status_code == 200
    assert calls == [("good", "donor_login")]


@pytest.mark.asyncio
async def test_enforced_admin_login_checks_admin_action(client: AsyncClient, enforced, monkeypatch):
    calls = _stub_verify(monkeypatch, True)
    await client.post(
        "/api/v1/auth/admin/login",
        json={"email": "nobody@example.com", "password": "x", "recaptcha_token": "t"},
    )
    assert calls == [("t", "admin_login")]
