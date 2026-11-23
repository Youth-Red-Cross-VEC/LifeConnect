"""Task 5 checks against the ASGI application and disposable counters."""
import os
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from limits.storage import memory
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.core.rate_limiter import build_limiter, check_account_limit
from app.main import app
from app.services.email_service import EmailService
from tests.helpers import insert_admin, insert_donor


async def post_as(peer, path, body):
    async with AsyncClient(transport=ASGITransport(app=app, client=(peer, 4000)), base_url="http://test") as client:
        return await client.post("/api/v1/" + path, json=body)


@pytest.mark.parametrize("role,seed", [("admin", insert_admin), ("donor", insert_donor)])
async def test_account_login_recovers_and_is_independent_of_ip(client, test_session, monkeypatch, role, seed):
    await seed(test_session, email="target@example.com")
    monkeypatch.setattr(get_settings(), "ACCOUNT_AUTH_RATE_LIMIT", "2/minute")
    clock = SimpleNamespace(time=lambda: 100000)
    monkeypatch.setattr(memory, "time", clock)
    from app.core import rate_limiter
    monkeypatch.setattr(rate_limiter, "time", clock)
    path = f"auth/{role}/login"
    for address in ("target@example.com", "absent@example.com"):
        for peer, email in [("192.0.2.1", address), ("192.0.2.2", address.upper())]:
            assert (await post_as(peer, path, {"email": email, "password": "Incorrect123"})).status_code == 401
        response = await post_as("192.0.2.3", path, {"email": address, "password": "Secret123"})
        assert response.status_code == 429
        assert response.json() == {"detail": "Too many attempts. Please try again later."}
        assert response.headers["retry-after"] == "60"
    clock.time = lambda: 100061
    assert (await post_as("192.0.2.3", path, {"email": "target@example.com", "password": "Secret123"})).status_code == 200


@pytest.mark.parametrize("path", ["auth/donor/password-reset/request", "auth/admin/password-reset/request", "donors/register/code"])
async def test_code_delivery_budget_precedes_lookup_and_dispatch(client, test_session, monkeypatch, path):
    seed = insert_admin if "admin" in path else insert_donor
    await seed(test_session, email="target@example.com")
    send = AsyncMock(return_value=True)
    monkeypatch.setattr(EmailService, "send_otp_email", send)
    monkeypatch.setattr(get_settings(), "ACCOUNT_CODE_SEND_RATE_LIMIT", "1/minute")
    for address in ("target@example.com", "unknown@example.com"):
        first = await post_as("192.0.2.1", path, {"email": address})
        assert first.status_code == 200
        sent = send.await_count
        blocked = await post_as("192.0.2.2", path, {"email": address.upper()})
        assert blocked.status_code == 429 and 0 < int(blocked.headers["retry-after"]) <= 60
        assert send.await_count == sent
    assert send.await_count == (2 if path == "donors/register/code" else 1)


@pytest.mark.parametrize("route", ["donors/register", "admins/register", "queries/"])
async def test_invalid_bodies_use_dedicated_ip_budget(client, route):
    for _ in range(5):
        assert (await client.post("/api/v1/" + route, json={})).status_code == 422
    blocked = await client.post("/api/v1/" + route, json={})
    assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) > 0


@pytest.mark.parametrize("invalid", ["", "unlimited", "0/minute"])
def test_invalid_rate_policy_fails_startup(invalid):
    with pytest.raises(ValidationError):
        Settings(ACCOUNT_CODE_SEND_RATE_LIMIT=invalid)


def test_separate_workers_share_an_account_counter_with_redis():
    uri = os.environ.get("LC_RATE_TEST_REDIS_URL")
    if not uri:
        pytest.skip("Set LC_RATE_TEST_REDIS_URL to a disposable Redis database")
    assert uri.startswith(("redis://", "rediss://"))
    from fastapi import HTTPException, Request
    address = f"{uuid4().hex}@example.com"
    for worker in range(2):
        state = SimpleNamespace(limiter=build_limiter(60, uri))
        request = Request({"type": "http", "endpoint": post_as, "app": SimpleNamespace(state=state)})
        if worker == 0:
            check_account_limit(request, address, "1/minute")
        else:
            with pytest.raises(HTTPException) as error:
                check_account_limit(request, address, "1/minute")
            assert error.value.status_code == 429


@pytest.mark.parametrize("peers,other", [
    ([f"2001:db8:12:34::{i}" for i in range(1, 7)], "2001:db8:12:35::1"),
    (["192.0.2.1", "::ffff:192.0.2.1"] * 3, "192.0.2.2"),
])
async def test_equivalent_client_networks_share_ip_quota(client, peers, other):
    codes = [(await post_as(peer, "queries/", {})).status_code for peer in peers]
    assert codes == [422] * 5 + [429]
    assert (await post_as(other, "queries/", {})).status_code == 422


@pytest.mark.parametrize("route", ["donors/register", "auth/donor/password-reset/confirm", "auth/admin/password-reset/confirm"])
async def test_verification_quota_survives_client_change(client, monkeypatch, route):
    from tests.helpers import registration_payload

    email = "visitor@example.com"
    monkeypatch.setattr(get_settings(), "ACCOUNT_AUTH_RATE_LIMIT", "1/minute")
    if route == "donors/register":
        body = {**registration_payload(email), "enrollment_code": "000001"}
    else:
        body = {"email": email, "otp": "000001", "new_password": "Fresh12345"}
    assert (await post_as("192.0.2.1", route, body)).status_code == 400
    blocked = await post_as("192.0.2.2", route, {**body, "email": email.upper()})
    assert blocked.status_code == 429
