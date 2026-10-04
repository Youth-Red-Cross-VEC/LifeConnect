"""Database-backed one-time codes (safe across workers and restarts)."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.otp import OtpCode

OTP_TTL_SECONDS = 600
OTP_MAX_ATTEMPTS = 5

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
    """Replace any outstanding code for (purpose, email) with a new one."""
    email = email.lower()
    await session.execute(delete(OtpCode).where(OtpCode.purpose == purpose, OtpCode.email == email))
    session.add(OtpCode(
        purpose=purpose,
        email=email,
        otp_hash=_hash(otp, purpose, email),
        expires_at=datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS),
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
    if datetime.utcnow() > record.expires_at or record.attempts >= OTP_MAX_ATTEMPTS:
        await session.delete(record)
        await session.commit()
        return False
    record.attempts += 1
    ok = hmac.compare_digest(record.otp_hash, _hash(otp, purpose, email))
    if ok:
        await session.delete(record)
    # Commit here: callers raise HTTPException on failure, which rolls the request session back
    # and would otherwise discard the attempt counter.
    await session.commit()
    return ok
