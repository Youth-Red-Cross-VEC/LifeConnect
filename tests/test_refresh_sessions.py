"""Refresh-token rotation, reuse detection and logout."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.auth.utils import create_refresh_token
from app.models.refresh_session import RefreshSession
from tests.helpers import insert_donor

LOGIN = "/api/v1/auth/donor/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"


async def _login(client: AsyncClient) -> dict:
    r = await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_refresh_rotates_token(client: AsyncClient, test_session):
    await insert_donor(test_session)
    first = await _login(client)

    r = await client.post(REFRESH, json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 200
    second = r.json()
    assert second["refresh_token"] != first["refresh_token"]

    rows = (await test_session.execute(select(RefreshSession))).scalars().all()
    assert len(rows) == 2
    assert sum(1 for x in rows if x.revoked_at is None) == 1


@pytest.mark.asyncio
async def test_reuse_of_old_token_revokes_whole_chain(client: AsyncClient, test_session):
    await insert_donor(test_session)
    first = await _login(client)
    second = (await client.post(REFRESH, json={"refresh_token": first["refresh_token"]})).json()

    replay = await client.post(REFRESH, json={"refresh_token": first["refresh_token"]})
    assert replay.status_code == 401

    # The newest token from the same chain no longer works either.
    after = await client.post(REFRESH, json={"refresh_token": second["refresh_token"]})
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient, test_session):
    await insert_donor(test_session)
    tokens = await _login(client)

    assert (await client.post(LOGOUT, json={"refresh_token": tokens["refresh_token"]})).status_code == 200
    r = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_logout_with_garbage_token_is_ok(client: AsyncClient):
    assert (await client.post(LOGOUT, json={"refresh_token": "nope"})).status_code == 200


@pytest.mark.asyncio
async def test_untracked_refresh_token_rejected(client: AsyncClient, test_session):
    await insert_donor(test_session)
    forged = create_refresh_token({"sub": "DON-1", "user_type": "donor", "email": "donor1@example.com"})
    r = await client.post(REFRESH, json={"refresh_token": forged})
    assert r.status_code == 401
