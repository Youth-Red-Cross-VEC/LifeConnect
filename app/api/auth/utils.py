"""
JWT Token Utilities and Password Management

Handles JWT token creation/validation, password hashing/verification,
and all cryptographic operations for authentication.
"""

import asyncio
import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.utils.dates import utcnow

# ============================================================
# CONFIGURATION - Load from shared settings (single source of truth)
# ============================================================

_settings = get_settings()
SECRET_KEY = _settings.SECRET_KEY
ALGORITHM = _settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = _settings.REFRESH_TOKEN_EXPIRE_DAYS

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# ============================================================
# PASSWORD UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password
        
    Example:
        >>> hashed = hash_password("mypassword")
    """
    return pwd_context.hash(password)


async def hash_password_async(password: str) -> str:
    """hash_password on a worker thread: bcrypt takes ~0.25 s and must not stall the event loop."""
    return await asyncio.to_thread(hash_password, password)


def _verify_legacy_scrypt(plain_password: str, hashed_password: str) -> bool:
    """Verify a legacy werkzeug-style hash: scrypt:N:r:p$salt$hexdigest."""
    try:
        method, salt, expected = hashed_password.split("$")
        _, n, r, p = method.split(":")
        n, r, p = int(n), int(r), int(p)
        digest = hashlib.scrypt(
            plain_password.encode(),
            salt=salt.encode(),
            n=n,
            r=r,
            p=p,
            maxmem=132 * n * r * p,
        ).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.

    Supports bcrypt and legacy scrypt hashes (migrated from the old Flask app).
    Callers should check needs_rehash() after a successful verification.
    """
    if hashed_password.startswith("scrypt:"):
        return _verify_legacy_scrypt(plain_password, hashed_password)
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """verify_password on a worker thread (bcrypt, and the heavier legacy scrypt check)."""
    return await asyncio.to_thread(verify_password, plain_password, hashed_password)


# A real bcrypt hash of a random value nobody knows. Login verifies against it when the email is unknown,
# so "no such account" costs the same time as "wrong password" and cannot be told apart by timing.
# Computed once at import (a quarter second) rather than lazily, so no request pays for it.
DUMMY_PASSWORD_HASH = pwd_context.hash(secrets.token_urlsafe(24))


def needs_rehash(hashed_password: str) -> bool:
    """True if the stored hash is a legacy scrypt hash and should become bcrypt."""
    return hashed_password.startswith("scrypt:")


# ============================================================
# JWT TOKEN UTILITIES
# ============================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token
               Required keys: "sub" (user_id), "user_type", "email"
        expires_delta: Optional custom expiration time
                      Default: ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT access token
        
    Example:
        >>> token = create_access_token({
        ...     "sub": "DON-123456",
        ...     "user_type": "donor",
        ...     "email": "user@example.com"
        ... })
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in token
               Required keys: "sub" (user_id), "user_type", "email"
        
    Returns:
        str: Encoded JWT refresh token
        
    Example:
        >>> token = create_refresh_token({
        ...     "sub": "DON-123456",
        ...     "user_type": "donor",
        ...     "email": "user@example.com"
        ... })
    """
    to_encode = data.copy()
    expire = utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        dict: Decoded token payload, or None if invalid/expired
        
    Example:
        >>> payload = decode_token(token_string)
        >>> if payload:
        ...     user_id = payload.get("sub")
        ...     user_type = payload.get("user_type")
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None