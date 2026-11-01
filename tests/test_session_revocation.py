"""Credential resets and account deactivation revoke all refresh cookies for that user."""

import pytest
from httpx import AsyncClient

from app.services.otp_service import PURPOSE_ADMIN_RESET, PURPOSE_DONOR_RESET, store_otp
from tests.helpers import cookie_headers, insert_admin, insert_donor, refresh_cookie

DONOR_LOGIN = "/api/v1/auth/donor/login"
ADMIN_LOGIN = "/api/v1/auth/admin/login"
REFRESH = "/api/v1/auth/refresh"


async def _login(client: AsyncClient, url: str, email: str, password: str = "Secret123") -> tuple[dict, str]:
    response = await client.post(url, json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json(), refresh_cookie(response)


@pytest.mark.asyncio
async def test_donor_password_reset_revokes_all_refresh_sessions(client: AsyncClient, test_session):
    await insert_donor(test_session)
    _, first_cookie = await _login(client, DONOR_LOGIN, "donor1@example.com")
    _, second_cookie = await _login(client, DONOR_LOGIN, "donor1@example.com")

    await store_otp(test_session, "donor1@example.com", "123456", PURPOSE_DONOR_RESET)
    response = await client.post(
        "/api/v1/auth/donor/password-reset/confirm",
        json={"email": "donor1@example.com", "otp": "123456", "new_password": "NewSecret456"},
    )
    assert response.status_code == 200, response.text

    assert (await client.post(REFRESH, headers=cookie_headers(first_cookie))).status_code == 401
    assert (await client.post(REFRESH, headers=cookie_headers(second_cookie))).status_code == 401

    _, fresh_cookie = await _login(client, DONOR_LOGIN, "donor1@example.com", "NewSecret456")
    assert (await client.post(REFRESH, headers=cookie_headers(fresh_cookie))).status_code == 200


@pytest.mark.asyncio
async def test_admin_password_reset_revokes_all_refresh_sessions(client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    _, old_cookie = await _login(client, ADMIN_LOGIN, "admin1@example.com")
    await store_otp(test_session, "admin1@example.com", "654321", PURPOSE_ADMIN_RESET)
    response = await client.post(
        "/api/v1/auth/admin/password-reset/confirm",
        json={"email": "admin1@example.com", "otp": "654321", "new_password": "NewSecret456"},
    )
    assert response.status_code == 200, response.text
    assert (await client.post(REFRESH, headers=cookie_headers(old_cookie))).status_code == 401


@pytest.mark.asyncio
async def test_admin_deactivation_revokes_sessions_even_after_reactivation(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    _, token = await _login(admin_client, ADMIN_LOGIN, "admin1@example.com")
    assert (await admin_client.patch("/api/v1/admins/ADM-1/deactivate")).status_code == 200
    assert (await admin_client.patch("/api/v1/admins/ADM-1/activate")).status_code == 200
    assert (await admin_client.post(REFRESH, headers=cookie_headers(token))).status_code == 401


@pytest.mark.asyncio
async def test_admin_put_inactive_revokes_sessions(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    _, token = await _login(admin_client, ADMIN_LOGIN, "admin1@example.com")
    assert (await admin_client.put("/api/v1/admins/ADM-1", json={"active_status": "Inactive"})).status_code == 200
    assert (await admin_client.put("/api/v1/admins/ADM-1", json={"active_status": "Active"})).status_code == 200
    assert (await admin_client.post(REFRESH, headers=cookie_headers(token))).status_code == 401


@pytest.mark.asyncio
async def test_donor_deactivation_by_admin_revokes_sessions(admin_client: AsyncClient, test_session):
    await insert_donor(test_session)
    _, token = await _login(admin_client, DONOR_LOGIN, "donor1@example.com")
    assert (await admin_client.post("/api/v1/donors/DON-1/deactivate")).status_code == 200
    assert (await admin_client.post("/api/v1/donors/DON-1/activate")).status_code == 200
    assert (await admin_client.post(REFRESH, headers=cookie_headers(token))).status_code == 401


@pytest.mark.asyncio
async def test_other_users_sessions_survive(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    _, other_cookie = await _login(client, DONOR_LOGIN, "donor2@example.com")
    await store_otp(test_session, "donor1@example.com", "123456", PURPOSE_DONOR_RESET)
    response = await client.post(
        "/api/v1/auth/donor/password-reset/confirm",
        json={"email": "donor1@example.com", "otp": "123456", "new_password": "NewSecret456"},
    )
    assert response.status_code == 200
    assert (await client.post(REFRESH, headers=cookie_headers(other_cookie))).status_code == 200
