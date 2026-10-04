"""Database.session() owns the commit; routes must not commit on their own."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.query import QueryTable
from app.models.refresh_session import RefreshSession
from tests.helpers import insert_donor


@pytest.fixture
async def uow_client(test_engine):
    """Client whose DB dependency behaves like Database.session(): commit after the route returns."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    route_commits: list[int] = []

    async def override_get_db():
        async with factory() as session:
            real_commit = session.commit
            count = 0

            async def counting_commit():
                nonlocal count
                count += 1
                await real_commit()

            session.commit = counting_commit  # type: ignore[method-assign]
            try:
                yield session
                route_commits.append(count)  # commits made by the route itself
                await real_commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.route_commits = route_commits  # type: ignore[attr-defined]
        ac.factory = factory  # type: ignore[attr-defined]
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_query_relies_on_session_commit(uow_client):
    r = await uow_client.post("/api/v1/queries/", json={
        "user_name": "Sam", "user_email": "sam@example.com", "user_query": "How do I update my profile?",
    })
    assert r.status_code == 201
    assert uow_client.route_commits == [0]
    async with uow_client.factory() as other:
        assert len((await other.execute(select(QueryTable))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_login_relies_on_session_commit_and_persists(uow_client, test_session):
    await insert_donor(test_session)
    r = await uow_client.post(
        "/api/v1/auth/donor/login", json={"email": "donor1@example.com", "password": "Secret123"}
    )
    assert r.status_code == 200
    assert uow_client.route_commits == [0]
    async with uow_client.factory() as other:
        assert len((await other.execute(select(RefreshSession))).scalars().all()) == 1
