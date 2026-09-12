"""
Pytest configuration and fixtures.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
from typing import AsyncGenerator

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.api.auth.utils import create_access_token


# Use in-memory SQLite for tests (faster than PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create fresh test database engine for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up after each test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden database dependency."""
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token() -> str:
    """
    Create a valid JWT access token for a mock admin user.

    Used by tests that call admin-protected endpoints.
    No real DB admin is needed — the token is minted directly.
    """
    return create_access_token({
        "sub": "ADM-test123",
        "user_type": "admin",
        "email": "testadmin@example.com",
    })


from app.models.admin import AdminDetails
from datetime import date
from app.api.auth.utils import hash_password

@pytest.fixture
async def admin_client(test_session, admin_token) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP test client pre-configured with an admin Bearer token.

    Use this fixture for any test that calls an admin-only endpoint.
    """
    # Insert the mock admin into the test database
    mock_admin = AdminDetails(
        id="ADM-test123",
        email="testadmin@example.com",
        password=hash_password("testpass123"),
        username="Test Admin",
        authentication_id="AUTH-test123",
        vec_registration_number="VEC-0001",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9999999999",
        department="IT",
        active_status="active",
        approved_donation_count=0,
        closed_requests_count=0,
    )
    await test_session.merge(mock_admin)
    await test_session.commit()

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    headers = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


