"""
Health check and utility endpoints.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.utils.dates import utcnow
from app.config import get_settings, Settings
from app.schemas.common import HealthResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_db, scope="function"),
    settings: Settings = Depends(get_settings),
):
    """
    Health check endpoint.
    
    Returns application health status and database connectivity.
    """
    try:
        # Test database connection
        await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        # This endpoint is public: driver errors carry hostnames, usernames and addresses. The
        # details go to the server log, the client only learns that the database is down.
        logger.error("Health check: database unreachable", exc_info=True)
        db_status = "unavailable"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        version=settings.APP_VERSION,
        timestamp=utcnow(),
    )


@router.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint - API information."""
    return MessageResponse(
        message="Welcome to LifeConnect API. Visit /docs for documentation.",
        success=True,
    )
