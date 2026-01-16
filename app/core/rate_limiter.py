"""
Rate Limiting Configuration.

Uses slowapi to implement rate limiting for API endpoints.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
import logging

logger = logging.getLogger(__name__)


# Create limiter instance with IP-based key function
limiter = Limiter(key_func=get_remote_address)


# ============================
# Rate Limit Decorators
# ============================

# Default limits by endpoint type (can be used in routes)
# Quick reference:
#   @limiter.limit("10/minute")  - 10 requests per minute
#   @limiter.limit("100/hour")   - 100 requests per hour
#   @limiter.limit("5/second")   - 5 requests per second

# Standard limits (adjust as needed):
RATE_LIMITS = {
    "default": "60/minute",        # General endpoints
    "auth": "5/minute",            # Login attempts (prevent brute force)
    "registration": "3/minute",    # Registration (prevent spam)
    "public": "100/minute",        # Public read endpoints
    "admin": "120/minute",         # Admin endpoints (higher limit)
    "certificate": "10/minute",    # Certificate generation (resource intensive)
    "email": "5/minute",           # Email sending (prevent spam)
}


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


# ============================
# Common Rate Limit Helpers
# ============================

def limit_auth(func):
    """Apply auth rate limit (5/minute) to prevent brute force."""
    return limiter.limit(RATE_LIMITS["auth"])(func)


def limit_registration(func):
    """Apply registration rate limit (3/minute) to prevent spam."""
    return limiter.limit(RATE_LIMITS["registration"])(func)


def limit_public(func):
    """Apply public endpoint rate limit (100/minute)."""
    return limiter.limit(RATE_LIMITS["public"])(func)


def limit_admin(func):
    """Apply admin endpoint rate limit (120/minute)."""
    return limiter.limit(RATE_LIMITS["admin"])(func)


def limit_certificate(func):
    """Apply certificate generation rate limit (10/minute)."""
    return limiter.limit(RATE_LIMITS["certificate"])(func)


def limit_email(func):
    """Apply email sending rate limit (5/minute)."""
    return limiter.limit(RATE_LIMITS["email"])(func)
