"""Refresh-token rotation with reuse detection."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_session import RefreshSession
from app.utils.dates import utcnow


async def issue_refresh_token(session: AsyncSession, token_data: dict) -> tuple[str, str]:
    """Create a refresh token and record it. Returns (token, jti)."""
    # Imported here, not at module level: app.api.auth's package init imports its router, which imports
    # this module, so a top-level import makes the import order of every caller matter.
    from app.api.auth.utils import create_refresh_token, decode_token

    jti = str(uuid.uuid4())
    token = create_refresh_token({**token_data, "jti": jti})
    exp = decode_token(token)["exp"]  # type: ignore[index]
    session.add(RefreshSession(
        jti=jti,
        user_id=token_data["sub"],
        role=token_data["user_type"],
        expires_at=datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None),
    ))
    return token, jti


async def revoke_chain(session: AsyncSession, jti: Optional[str]) -> None:
    """Revoke a session and every token that was rotated out of it."""
    now = utcnow()
    seen: set[str] = set()
    while jti and jti not in seen:
        seen.add(jti)
        # populate_existing: walk the chain as stored, not a stale in-memory copy of a row another request just rotated.
        row = await session.get(RefreshSession, jti, with_for_update=True, populate_existing=True)
        if row is None:
            return
        if row.revoked_at is None:
            row.revoked_at = now
        jti = row.replaced_by


async def revoke_all_for_user(session: AsyncSession, user_id: str, role: str) -> None:
    """Revoke every live refresh session of one account (password reset, deactivation).

    Access tokens already issued stay valid until they expire (ACCESS_TOKEN_EXPIRE_MINUTES),
    except that get_current_user rejects deactivated accounts immediately.
    """
    await session.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.role == role,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=utcnow())
        .execution_options(synchronize_session=False)
    )


async def claim_session(session: AsyncSession, jti: str) -> bool:
    """Atomically spend a live refresh session. True only for the single caller that wins.

    The conditional UPDATE (WHERE revoked_at IS NULL) is what makes rotation safe under concurrency:
    a second request holding the same token matches zero rows, even if it read the row as live before
    the first request committed.
    """
    result = await session.execute(
        update(RefreshSession)
        .where(RefreshSession.jti == jti, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1
