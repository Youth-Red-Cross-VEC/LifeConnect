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
from app.core.scheduler import start_scheduler_if_enabled
from app.core.logging import setup_logging
from app.core.exceptions import LifeConnectException
from app.core.rate_limiter import setup_rate_limiting
from app.api.v1 import router as v1_router

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

    # Jobs run in a dedicated process (python -m app.scheduler_worker), not in web workers
    scheduler = start_scheduler_if_enabled(settings, database)

    yield

    # Shutdown
    logger.info("Shutting down LifeConnect API...")

    if scheduler:
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
        # Interactive docs and the schema map every route; off when APP_ENV=production unless DOCS_ENABLED=true.
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    # Middleware add order is inner-to-outer: the LAST added wraps the others. CORS must be the
    # outermost layer so even a 500 produced by CatchAllMiddleware (or the rate limiter) carries
    # Access-Control-Allow-Origin and the browser can read the response.
    from app.core.middleware import CatchAllMiddleware, SecurityHeadersMiddleware
    app.add_middleware(CatchAllMiddleware)

    # Configure rate limiting
    setup_rate_limiting(app)

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Configure CORS (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    return app


# Create the app instance
app = create_app()

