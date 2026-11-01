"""
Rate Limiting Configuration.

Uses slowapi to implement rate limiting for API endpoints.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI
import importlib.util
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


REDIS_SCHEMES = ("redis://", "rediss://", "redis+unix://")


def build_limiter(per_minute: int, storage_uri: str) -> Limiter:
    """IP-keyed limiter that applies `per_minute` to every route that has no explicit limit."""
    if storage_uri.startswith(REDIS_SCHEMES) and importlib.util.find_spec("redis") is None:
        # Fail at startup with an actionable message instead of at the first rate-limited request.
        scheme = storage_uri.split("://", 1)[0]
        raise RuntimeError(
            f"RATE_LIMIT_STORAGE_URI uses {scheme}:// but the 'redis' Python package is not installed. "
            "Install it with: pip install -r requirements-redis.txt "
            "(or set RATE_LIMIT_STORAGE_URI=memory:// for a single worker)."
        )
    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{per_minute}/minute"],
        storage_uri=storage_uri,
    )


_settings = get_settings()
limiter = build_limiter(_settings.RATE_LIMIT_PER_MINUTE, _settings.RATE_LIMIT_STORAGE_URI)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add limiter to app state
    app.state.limiter = limiter
    
    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add middleware
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("Rate limiting configured successfully")


def get_limiter() -> Limiter:
    """Get the global limiter instance."""
    return limiter
