"""Refresh-token rotation with reuse detection."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.utils import create_refresh_token, decode_token
from app.models.refresh_session import RefreshSession


async def issue_refresh_token(session: AsyncSession, token_data: dict) -> tuple[str, str]:
    """Create a refresh token and record it. Returns (token, jti)."""
    jti = str(uuid.uuid4())
    token = create_refresh_token({**token_data, "jti": jti})
    exp = decode_token(token)["exp"]  # type: ignore[index]
    session.add(RefreshSession(
        jti=jti,
        user_id=token_data["sub"],
        role=token_data["user_type"],
        expires_at=datetime.utcfromtimestamp(exp),
    ))
    return token, jti


async def revoke_chain(session: AsyncSession, jti: Optional[str]) -> None:
    """Revoke a session and every token that was rotated out of it."""
    now = datetime.utcnow()
    seen: set[str] = set()
    while jti and jti not in seen:
        seen.add(jti)
        row = await session.get(RefreshSession, jti)
        if row is None:
            return
        if row.revoked_at is None:
            row.revoked_at = now
        jti = row.replaced_by
