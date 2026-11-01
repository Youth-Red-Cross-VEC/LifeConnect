"""B5: a refresh token can be spent exactly once, even when two requests pass the revoked check together."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update

from app.models.refresh_session import RefreshSession
from app.api.auth.utils import decode_token
from datetime import datetime
from tests.helpers import insert_donor

LOGIN = "/api/v1/auth/donor/login"
REFRESH = "/api/v1/auth/refresh"


@pytest.mark.asyncio
async def test_concurrent_refresh_cannot_double_spend(client: AsyncClient, test_session):
    await insert_donor(test_session)
    tokens = (await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})).json()
    jti = decode_token(tokens["refresh_token"])["jti"]

    # Simulate the losing side of a race: the row is already spent in the database, but this request
    # still holds a stale in-memory copy that says it is live (it read the row before the other
    # request committed). synchronize_session=False keeps the stale copy stale.
    stale_copy = await test_session.get(RefreshSession, jti)  # keep a strong ref so the identity map keeps it
    await test_session.execute(
        update(RefreshSession)
        .where(RefreshSession.jti == jti)
        .values(revoked_at=datetime.utcnow())
        .execution_options(synchronize_session=False)
    )

    assert stale_copy.revoked_at is None  # the copy the request will see really is stale
    r = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401, "a token already spent by a concurrent request must not mint new tokens"

    live = (await test_session.execute(
        select(func.count()).select_from(RefreshSession).where(RefreshSession.revoked_at.is_(None))
    )).scalar()
    assert live == 0, "no usable session may be left behind by the lost race"


@pytest.mark.asyncio
async def test_sequential_refresh_still_rotates(client: AsyncClient, test_session):
    await insert_donor(test_session)
    tokens = (await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})).json()
    r = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    rows = (await test_session.execute(select(RefreshSession).order_by(RefreshSession.created_at))).scalars().all()
    spent = [x for x in rows if x.revoked_at is not None]
    assert len(spent) == 1 and spent[0].replaced_by is not None
