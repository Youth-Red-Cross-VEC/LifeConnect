"""
Security Headers Middleware.

Adds security headers to all HTTP responses to protect against common attacks.
"""

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from typing import Callable

logger = logging.getLogger(__name__)


class CatchAllMiddleware(BaseHTTPMiddleware):
    """Turn an unhandled exception into a plain 500 without leaking details.

    This middleware is installed inside CORSMiddleware, so the browser still receives the CORS
    headers on the error response; Starlette's built-in ServerErrorMiddleware sits outside CORS
    and its responses have no CORS headers, which the frontend reports as an opaque network error.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            error_id = uuid.uuid4().hex
            logger.error("Unhandled request failure error_id=%s type=%s", error_id, type(exc).__name__)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error_id": error_id},
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply browser isolation and cache controls, including preflights and API errors."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking - page cannot be embedded in iframes
        response.headers["X-Frame-Options"] = "DENY"
        
        # Browsers only honor HSTS over TLS. Never advertise it on plain HTTP responses.
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        
        policy = "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        if (response.headers.get("content-type", "").startswith("text/html")
                and request.url.path in {"/docs", "/docs/oauth2-redirect", "/redoc"}):
            # FastAPI's optional documentation pages use inline bootstrapping and CDN assets.
            policy += ("; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                       "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                       "connect-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
                       "font-src 'self' https://fonts.gstatic.com")
        response.headers["Content-Security-Policy"] = policy

        # Control what referrer info is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Disable browser features we don't need
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Prevent caching of API responses with sensitive data
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response
