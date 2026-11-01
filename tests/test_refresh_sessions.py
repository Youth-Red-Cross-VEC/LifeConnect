"""Refresh-token rotation, cookie transport, reuse detection and logout."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.auth.utils import create_refresh_token
from app.models.refresh_session import RefreshSession
from tests.helpers import cookie_headers, insert_donor, refresh_cookie

LOGIN = "/api/v1/auth/donor/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"


async def _login(client: AsyncClient) -> tuple[dict, str]:
    response = await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})
    assert response.status_code == 200, response.text
    assert "refresh_token" not in response.json()
    return response.json(), refresh_cookie(response)


@pytest.mark.asyncio
async def test_refresh_rotates_http_only_cookie(client: AsyncClient, test_session):
    await insert_donor(test_session)
    _, first_cookie = await _login(client)
    response = await client.post(REFRESH, headers=cookie_headers(first_cookie))
    assert response.status_code == 200
    second_cookie = refresh_cookie(response)
    assert second_cookie != first_cookie
    assert "refresh_token" not in response.json()

    rows = (await test_session.execute(select(RefreshSession))).scalars().all()
    assert len(rows) == 2
    assert sum(1 for row in rows if row.revoked_at is None) == 1


@pytest.mark.asyncio
async def test_reuse_revokes_every_token_for_the_user(client: AsyncClient, test_session):
    await insert_donor(test_session)
    _, first = await _login(client)
    rotated = await client.post(REFRESH, headers=cookie_headers(first))
    second = refresh_cookie(rotated)

    replay = await client.post(REFRESH, headers=cookie_headers(first))
    assert replay.status_code == 401
    after = await client.post(REFRESH, headers=cookie_headers(second))
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_cookie(client: AsyncClient, test_session):
    await insert_donor(test_session)
    _, token = await _login(client)
    response = await client.post(LOGOUT, headers=cookie_headers(token))
    assert response.status_code == 200
    assert "lc_refresh_token" in response.headers.get("set-cookie", "")
    assert (await client.post(REFRESH, headers=cookie_headers(token))).status_code == 401


@pytest.mark.asyncio
async def test_logout_with_garbage_cookie_is_ok(client: AsyncClient):
    assert (await client.post(LOGOUT, headers=cookie_headers("nope"))).status_code == 200


@pytest.mark.asyncio
async def test_untracked_signed_refresh_token_is_rejected_and_revokes_user_sessions(client: AsyncClient, test_session):
    donor = await insert_donor(test_session)
    _, live = await _login(client)
    forged = create_refresh_token({
        "sub": donor.id,
        "user_type": "donor",
        "email": donor.email,
        "tv": donor.token_version,
    })
    rejected = await client.post(REFRESH, headers=cookie_headers(forged))
    assert rejected.status_code == 401
    assert (await client.post(REFRESH, headers=cookie_headers(live))).status_code == 401
