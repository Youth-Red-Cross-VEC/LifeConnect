"""Database-backed one-time codes (safe across workers and restarts)."""
import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.otp import OtpCode
from app.utils.dates import utcnow


# Each flow gets its own purpose so a code issued for one can never satisfy another.
PURPOSE_ADMIN_INVITE = "admin_invite"  # issued by POST /admins/invite, consumed by POST /admins/register
PURPOSE_DONOR_RESET = "donor_password_reset"
PURPOSE_ADMIN_RESET = "admin_password_reset"


def generate_otp() -> str:
    """Generate a 6-digit OTP using a cryptographically secure RNG."""
    return f"{secrets.randbelow(900000) + 100000}"


def _hash(otp: str, purpose: str, email: str) -> str:
    return hashlib.sha256(f"{purpose}:{email}:{otp}".encode()).hexdigest()


async def store_otp(session: AsyncSession, email: str, otp: str, purpose: str) -> None:
    """Issue a new code for (purpose, email), replacing any outstanding one.

    The attempt budget belongs to the window, not to the code: while a window is still open, a new
    code keeps both the attempts already used and the window's expiry. Requesting codes in a loop
    therefore cannot buy more guesses, and a locked-out user waits for the window to end. An expired
    window starts fresh.
    """
    email = email.lower()
    now = utcnow()
    record = (await session.execute(
        select(OtpCode).where(OtpCode.purpose == purpose, OtpCode.email == email).with_for_update()
    )).scalar_one_or_none()
    if record is not None and record.expires_at > now:
        record.otp_hash = _hash(otp, purpose, email)
    else:
        if record is not None:
            await session.delete(record)
            await session.flush()
        session.add(OtpCode(
            purpose=purpose,
            email=email,
            otp_hash=_hash(otp, purpose, email),
            expires_at=now + timedelta(seconds=get_settings().OTP_TTL_SECONDS),
            attempts=0,
        ))
    await session.commit()  # the code is emailed right after; it must be durable first


async def verify_otp(session: AsyncSession, email: str, otp: str, purpose: str) -> bool:
    """Purpose-bound, expiring, attempt-limited, single-use check."""
    email = email.lower()
    record = (await session.execute(
        select(OtpCode).where(OtpCode.purpose == purpose, OtpCode.email == email).with_for_update()
    )).scalar_one_or_none()
    if record is None:
        return False
    if utcnow() > record.expires_at:
        await session.delete(record)
        await session.commit()
        return False
    if record.attempts >= get_settings().OTP_MAX_ATTEMPTS:
        # Keep the locked record until its window ends; deleting it would let the next
        # "send me a code" request hand out a fresh set of guesses.
        return False
    record.attempts += 1
    ok = hmac.compare_digest(record.otp_hash, _hash(otp, purpose, email))
    if ok:
        await session.delete(record)
    # Commit here: callers raise HTTPException on failure, which rolls the request session back
    # and would otherwise discard the attempt counter.
    await session.commit()
    return ok
