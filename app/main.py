"""
LifeConnect API - Blood Donation Management System

FastAPI application factory and main entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.core.database import init_db, db
from app.core.scheduler import init_scheduler, get_scheduler
from app.core.logging import setup_logging
from app.core.exceptions import LifeConnectException
from app.core.rate_limiter import setup_rate_limiting
from app.api.v1 import router as v1_router
from app.api.auth import router as auth_router
from app.tasks import setup_scheduled_jobs

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Initialize database connection pool
    - Start background scheduler
    - Cleanup on shutdown
    """
    settings = get_settings()

    # Startup
    logger.info("Starting LifeConnect API...")

    # Initialize database
    database = init_db(
        database_url=settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )
    logger.info("Database connection pool initialized")

    # Initialize and start scheduler
    scheduler = init_scheduler(timezone=settings.SCHEDULER_TIMEZONE)
    setup_scheduled_jobs(scheduler, database)
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down LifeConnect API...")

    # Stop scheduler
    scheduler = get_scheduler()
    scheduler.shutdown()
    logger.info("Scheduler stopped")

    # Close database connections
    if db:
        await db.close()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    settings = get_settings()

    # Setup logging
    setup_logging()

    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Blood Donation Management System API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure rate limiting
    setup_rate_limiting(app)

    # Exception handlers
    @app.exception_handler(LifeConnectException)
    async def lifeconnect_exception_handler(
        request: Request, exc: LifeConnectException
    ):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message, "error_details": exc.details},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include routers
    app.include_router(v1_router)
    app.include_router(auth_router, prefix="/api/v1")

    return app


# Create the app instance
app = create_app()

