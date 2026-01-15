"""
Health check and utility endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from app.core.database import get_db
from app.config import get_settings, Settings
from app.schemas.common import HealthResponse, MessageResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_db),
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
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
    )


@router.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint - API information."""
    return MessageResponse(
        message="Welcome to LifeConnect API. Visit /docs for documentation.",
        success=True,
    )
