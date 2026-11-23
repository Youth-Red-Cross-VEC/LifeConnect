"""B5: a refresh token can be spent exactly once, even when two requests pass the revoked check together."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update

from app.models.refresh_session import RefreshSession
from app.api.auth.utils import decode_token
from app.utils.dates import utcnow
from tests.helpers import cookie_headers, insert_donor, refresh_cookie

LOGIN = "/api/v1/auth/donor/login"
REFRESH = "/api/v1/auth/refresh"


@pytest.mark.asyncio
async def test_concurrent_refresh_cannot_double_spend(client: AsyncClient, test_session):
    await insert_donor(test_session)
    login = await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})
    token = refresh_cookie(login)
    jti = decode_token(token)["jti"]

    # Simulate the losing side of a race: the row is already spent in the database, but this request
    # still holds a stale in-memory copy that says it is live (it read the row before the other
    # request committed). synchronize_session=False keeps the stale copy stale.
    stale_copy = await test_session.get(RefreshSession, jti)  # keep a strong ref so the identity map keeps it
    await test_session.execute(
        update(RefreshSession)
        .where(RefreshSession.jti == jti)
        .values(revoked_at=utcnow())
        .execution_options(synchronize_session=False)
    )

    assert stale_copy.revoked_at is None  # the copy the request will see really is stale
    r = await client.post(REFRESH, headers=cookie_headers(token))
    assert r.status_code == 401, "a token already spent by a concurrent request must not mint new tokens"

    live = (await test_session.execute(
        select(func.count()).select_from(RefreshSession).where(RefreshSession.revoked_at.is_(None))
    )).scalar()
    assert live == 0, "no usable session may be left behind by the lost race"


@pytest.mark.asyncio
async def test_sequential_refresh_still_rotates(client: AsyncClient, test_session):
    await insert_donor(test_session)
    login = await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})
    token = refresh_cookie(login)
    r = await client.post(REFRESH, headers=cookie_headers(token))
    assert r.status_code == 200
    rows = (await test_session.execute(select(RefreshSession).order_by(RefreshSession.created_at))).scalars().all()
    spent = [x for x in rows if x.revoked_at is not None]
    assert len(spent) == 1 and spent[0].replaced_by is not None


@pytest.mark.asyncio
async def test_logout_waits_for_pending_rotation_on_postgresql(postgres_security_engine):
    """Two independent transactions must leave the successor revoked."""
    import asyncio
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.services.refresh_session_service import claim_session, issue_refresh_token, revoke_chain

    sessions = async_sessionmaker(postgres_security_engine, expire_on_commit=False)
    claims = {"sub": "DON-race", "user_type": "donor", "tv": 0}
    async with sessions() as rotating:
        _, first = await issue_refresh_token(rotating, claims)
        await rotating.commit()
        assert await claim_session(rotating, first)
        _, successor = await issue_refresh_token(rotating, claims)
        parent = await rotating.get(RefreshSession, first)
        parent.replaced_by = successor
        await rotating.flush()
        reading = asyncio.Event()

        async def logout():
            async with sessions.begin() as ending:
                connection = await ending.connection()
                event.listen(connection.sync_connection, "before_cursor_execute",
                             lambda *args: reading.set(), once=True)
                await revoke_chain(ending, first)

        pending = asyncio.create_task(logout())
        try:
            await asyncio.wait_for(reading.wait(), timeout=5)
        finally:
            await rotating.commit()
            await asyncio.wait_for(pending, timeout=5)
    async with sessions() as checking:
        assert (await checking.get(RefreshSession, successor)).revoked_at is not None
