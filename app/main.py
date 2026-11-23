"""
LifeConnect API - Blood Donation Management System

FastAPI application factory and main entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.core.api_limits import ApiRequestLimits
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uuid

from app.config import get_settings
from app.core.database import init_db, db
from app.core.scheduler import start_scheduler_if_enabled
from app.core.logging import setup_logging
from app.core.exceptions import LifeConnectException
from app.core.rate_limiter import setup_rate_limiting
from app.api.v1 import router as v1_router

logger = logging.getLogger(__name__)


async def lifeconnect_exception_handler(
    request: Request, exc: LifeConnectException
) -> JSONResponse:
    """Return a client-safe error body while keeping diagnostics server-side.

    ``exc.details`` can embed submitted values (an email, a phone number) or internal
    identifiers, so its contents stay out of responses and logs. Every
    caller still gets a stable ``error_id`` to quote to support.
    """
    error_id = uuid.uuid4().hex
    logger.warning("Application error error_id=%s type=%s", error_id, type(exc).__name__)
    content = {"detail": exc.message, "error_id": error_id}
    return JSONResponse(status_code=400, content=content)


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
        # Interactive docs and the schema map every route; off in production unless ENABLE_DOCS=true.
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    # Middleware registration proceeds from the innermost layer outward.
    from app.core.middleware import CatchAllMiddleware, SecurityHeadersMiddleware

    # Configure rate limiting
    app.add_middleware(ApiRequestLimits)
    setup_rate_limiting(app)

    app.add_middleware(CatchAllMiddleware)

    # CORS also decorates handled errors. Security headers wrap preflight responses.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Retry-After", "Content-Disposition"],
    )

    app.add_middleware(SecurityHeadersMiddleware)

    # Exception handlers
    app.add_exception_handler(LifeConnectException, lifeconnect_exception_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = [{key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        error_id = uuid.uuid4().hex
        logger.error("Unhandled request failure error_id=%s type=%s", error_id, type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_id": error_id},
        )

    # Include routers
    app.include_router(v1_router)

    return app


# Create the app instance
app = create_app()

