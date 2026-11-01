"""A1: credential resets and account deactivation revoke every refresh session of that user."""

import pytest
from httpx import AsyncClient

from app.services.otp_service import PURPOSE_ADMIN_RESET, PURPOSE_DONOR_RESET, store_otp
from tests.helpers import insert_admin, insert_donor

DONOR_LOGIN = "/api/v1/auth/donor/login"
ADMIN_LOGIN = "/api/v1/auth/admin/login"
REFRESH = "/api/v1/auth/refresh"


async def _login(client: AsyncClient, url: str, email: str, password: str = "Secret123") -> dict:
    r = await client.post(url, json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_donor_password_reset_revokes_all_refresh_sessions(client: AsyncClient, test_session):
    await insert_donor(test_session)
    first = await _login(client, DONOR_LOGIN, "donor1@example.com")
    second = await _login(client, DONOR_LOGIN, "donor1@example.com")  # a second device

    await store_otp(test_session, "donor1@example.com", "123456", PURPOSE_DONOR_RESET)
    r = await client.post(
        "/api/v1/auth/donor/password-reset/confirm",
        json={"email": "donor1@example.com", "otp": "123456", "new_password": "NewSecret456"},
    )
    assert r.status_code == 200, r.text

    for tokens in (first, second):
        stale = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
        assert stale.status_code == 401, "a refresh token issued before the reset must stop working"

    # The new password works and gets fresh, working tokens.
    fresh = await _login(client, DONOR_LOGIN, "donor1@example.com", "NewSecret456")
    assert (await client.post(REFRESH, json={"refresh_token": fresh["refresh_token"]})).status_code == 200


@pytest.mark.asyncio
async def test_admin_password_reset_revokes_all_refresh_sessions(client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    old = await _login(client, ADMIN_LOGIN, "admin1@example.com")

    await store_otp(test_session, "admin1@example.com", "654321", PURPOSE_ADMIN_RESET)
    r = await client.post(
        "/api/v1/auth/admin/password-reset/confirm",
        json={"email": "admin1@example.com", "otp": "654321", "new_password": "NewSecret456"},
    )
    assert r.status_code == 200, r.text

    stale = await client.post(REFRESH, json={"refresh_token": old["refresh_token"]})
    assert stale.status_code == 401


@pytest.mark.asyncio
async def test_admin_deactivation_revokes_sessions_even_after_reactivation(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    tokens = await _login(admin_client, ADMIN_LOGIN, "admin1@example.com")

    assert (await admin_client.patch("/api/v1/admins/ADM-1/deactivate")).status_code == 200
    assert (await admin_client.patch("/api/v1/admins/ADM-1/activate")).status_code == 200

    # Reactivation must not resurrect a token that predates the deactivation.
    r = await admin_client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_put_inactive_revokes_sessions(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    tokens = await _login(admin_client, ADMIN_LOGIN, "admin1@example.com")

    assert (await admin_client.put("/api/v1/admins/ADM-1", json={"active_status": "Inactive"})).status_code == 200
    assert (await admin_client.put("/api/v1/admins/ADM-1", json={"active_status": "Active"})).status_code == 200

    r = await admin_client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_donor_deactivation_by_admin_revokes_sessions(admin_client: AsyncClient, test_session):
    await insert_donor(test_session)
    tokens = await _login(admin_client, DONOR_LOGIN, "donor1@example.com")

    assert (await admin_client.post("/api/v1/donors/DON-1/deactivate")).status_code == 200
    assert (await admin_client.post("/api/v1/donors/DON-1/activate")).status_code == 200

    r = await admin_client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_other_users_sessions_survive(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    other = await _login(client, DONOR_LOGIN, "donor2@example.com")

    await store_otp(test_session, "donor1@example.com", "123456", PURPOSE_DONOR_RESET)
    r = await client.post(
        "/api/v1/auth/donor/password-reset/confirm",
        json={"email": "donor1@example.com", "otp": "123456", "new_password": "NewSecret456"},
    )
    assert r.status_code == 200

    assert (await client.post(REFRESH, json={"refresh_token": other["refresh_token"]})).status_code == 200
