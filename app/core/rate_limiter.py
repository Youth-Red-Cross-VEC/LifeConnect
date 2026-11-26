"""
Rate Limiting Configuration.

Uses slowapi to implement rate limiting for API endpoints.
"""

import hashlib
import hmac
import importlib.util
import logging
import math
import time
from typing import Any, cast
from collections.abc import Sequence
from functools import lru_cache
from ipaddress import IPv6Address, ip_address, ip_network

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from limits import RateLimitItem, parse_many
from limits.errors import StorageError
from limits.storage import RedisStorage
from limits.strategies import RateLimiter
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.utils.emails import normalize_email

logger = logging.getLogger(__name__)


REDIS_SCHEMES = ("redis://", "rediss://", "redis+unix://")


def client_bucket(request: Request) -> str:
    peer = get_remote_address(request)
    try:
        address = ip_address(peer)
    except ValueError:
        return peer
    if isinstance(address, IPv6Address):
        if address.ipv4_mapped:
            return str(address.ipv4_mapped)
        return str(ip_network((address, 64), strict=False))
    return str(address)


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
    options = {}
    if storage_uri.startswith(REDIS_SCHEMES):
        from redis.backoff import NoBackoff
        from redis.retry import Retry
        if "?" in storage_uri:
            raise ValueError("Use a Redis URI without query overrides for rate limiting")
        options = dict(socket_connect_timeout=1, socket_timeout=1, max_connections=32,
                       retry=Retry(NoBackoff(), 0), wrap_exceptions=True, key_prefix="lifeconnect:limits")
    active = Limiter(
        key_func=private_client_bucket,
        storage_options=cast(Any, options),
        key_style="endpoint",
        default_limits=[f"{per_minute}/minute"],
        storage_uri=storage_uri,
    )

    if options and (not active.enabled or active._swallow_errors or active._in_memory_fallback_enabled):
        raise ValueError("Shared rate limiting requires enforcement without local fallback")
    return active


def private_client_bucket(request: Request) -> str:
    return hmac.new(get_settings().SECRET_KEY.encode(), b"rate-limit/ip/" + client_bucket(request).encode(),
                    hashlib.sha256).hexdigest()


def close_rate_storage(active: Limiter) -> None:
    if isinstance(active._storage, RedisStorage):
        cast(Any, active._storage.get_connection()).close()


async def _storage_unavailable(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Rate limit storage unavailable")
    return JSONResponse({"detail": "Service temporarily unavailable"}, status_code=503,
                        headers={"Retry-After": "1", "Cache-Control": "no-store"})


_settings = get_settings()
limiter = build_limiter(_settings.RATE_LIMIT_PER_MINUTE, _settings.RATE_LIMIT_STORAGE_URI)


def _retry_headers(strategy: RateLimiter, window: RateLimitItem, bucket: Sequence[str]) -> dict[str, str]:
    try:
        reset_at, _ = strategy.get_window_stats(window, *bucket)
    except StorageError:
        return {"Retry-After": "1"}
    return {"Retry-After": str(max(1, math.ceil(reset_at - time.time())))}


async def _ip_limit_exceeded(request: Request, exc: Exception) -> JSONResponse:
    window, bucket = request.state.view_rate_limit
    return JSONResponse(
        {"error": "Too many attempts. Please try again later."}, status_code=429,
        headers=await run_in_threadpool(_retry_headers, request.app.state.limiter.limiter, window, bucket),
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add limiter to app state
    app.state.limiter = limiter

    # Add exception handler for rate limit exceeded
    app.add_exception_handler(StorageError, _storage_unavailable)
    app.add_exception_handler(RateLimitExceeded, _ip_limit_exceeded)

    logger.info("Rate limiting configured successfully")


async def check_default_api_limit(request: Request) -> None:
    # SlowAPI's middleware only discovers top-level Starlette routes. FastAPI
    # has resolved nested routers by the time this dependency runs.
    active = request.app.state.limiter
    endpoint = request.scope["endpoint"]
    await run_in_threadpool(active._check_request_limit, request, endpoint, in_middleware=False)
    # The SlowAPI decorator observes this flag and does not charge the IP twice.
    request.state._rate_limiting_complete = True


@lru_cache(maxsize=16)
def _windows(policy: str) -> list[RateLimitItem]:
    return parse_many(policy)


def check_account_limit(request: Request, email: str, policy: str) -> None:
    """Charge the validated address before lookup, hashing, OTP work or email delivery."""
    account = hmac.new(
        get_settings().SECRET_KEY.encode(), b"rate-limit/account/" + normalize_email(email).encode(),
        hashlib.sha256,
    ).hexdigest()
    endpoint = request.scope["endpoint"]
    bucket = ("lifeconnect-account", endpoint.__module__, endpoint.__name__, account)
    strategy = request.app.state.limiter.limiter
    for window in _windows(policy):
        if not strategy.hit(window, *bucket):
            raise HTTPException(
                status_code=429, detail="Too many attempts. Please try again later.",
                headers=_retry_headers(strategy, window, bucket),
            )


async def enforce_account_limit(request: Request, email: str, policy: str) -> None:
    await run_in_threadpool(check_account_limit, request, email, policy)


def get_limiter() -> Limiter:
    """Get the global limiter instance."""
    return limiter
