"""
API Dependencies - Shared dependency injection functions.

Contains database session and service dependencies.
Authentication dependencies are in api/auth/deps.py (partner's domain).
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.config import get_settings, Settings
from app.repositories import (
    DonorRepository,
    AdminRepository,
    BloodRequestRepository,
    HospitalRepository,
)
from app.services import EmailService, DistanceService


# ============ Settings ============


def get_app_settings() -> Settings:
    """Get application settings."""
    return get_settings()


# ============ Repository Dependencies ============


async def get_donor_repository(
    session: AsyncSession = None,
) -> AsyncGenerator[DonorRepository, None]:
    """Get donor repository with session."""
    async for db_session in get_db():
        yield DonorRepository(db_session)


async def get_admin_repository(
    session: AsyncSession = None,
) -> AsyncGenerator[AdminRepository, None]:
    """Get admin repository with session."""
    async for db_session in get_db():
        yield AdminRepository(db_session)


async def get_blood_request_repository(
    session: AsyncSession = None,
) -> AsyncGenerator[BloodRequestRepository, None]:
    """Get blood request repository with session."""
    async for db_session in get_db():
        yield BloodRequestRepository(db_session)


async def get_hospital_repository(
    session: AsyncSession = None,
) -> AsyncGenerator[HospitalRepository, None]:
    """Get hospital repository with session."""
    async for db_session in get_db():
        yield HospitalRepository(db_session)


# ============ Service Dependencies ============


def get_email_service(settings: Settings = None) -> EmailService:
    """Get email service."""
    if settings is None:
        settings = get_settings()
    return EmailService(settings)


def get_distance_service(settings: Settings = None) -> DistanceService:
    """Get distance service."""
    if settings is None:
        settings = get_settings()
    return DistanceService(settings)
