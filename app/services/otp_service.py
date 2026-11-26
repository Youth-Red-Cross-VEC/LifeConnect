"""Database-backed one-time codes (safe across workers and restarts)."""
import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import case, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.otp import OtpCode, OtpFailureWindow
from app.utils.dates import utcnow


# Each flow gets its own purpose so a code issued for one can never satisfy another.
PURPOSE_ADMIN_INVITE = "admin_invite"  # issued by POST /admins/invite, consumed by POST /admins/register
PURPOSE_DONOR_RESET = "donor_password_reset"
PURPOSE_ADMIN_RESET = "admin_password_reset"


def generate_otp() -> str:
    """Generate a 6-digit OTP using a cryptographically secure RNG."""
    return f"{secrets.randbelow(900000) + 100000}"


def _hash(otp: str, purpose: str, email: str) -> str:
    key = get_settings().SECRET_KEY.encode("utf-8")
    message = f"{purpose}:{email}:{otp}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


async def store_otp(session: AsyncSession, email: str, otp: str, purpose: str) -> None:
    """Issue a new code for (purpose, email), replacing any outstanding one.

    The attempt budget belongs to the window, not to the code: while a window is still open, a new
    code keeps both the attempts already used and the window's expiry. Requesting codes in a loop
    therefore cannot buy more guesses, and a locked-out user waits for the window to end. An expired
    window starts fresh.
    """
    email = email.lower()
    now = utcnow()
    if session.get_bind().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    statement = insert(OtpCode).values(
        purpose=purpose, email=email, code_hmac=_hash(otp, purpose, email),
        expires_at=now + timedelta(seconds=get_settings().OTP_TTL_SECONDS), attempts=0,
    )
    active = OtpCode.expires_at > now
    upsert = statement.on_conflict_do_update(
        index_elements=["purpose", "email"],
        set_={
            "code_hmac": statement.excluded.code_hmac,
            "expires_at": case((active, OtpCode.expires_at), else_=statement.excluded.expires_at),
            "attempts": case((active, OtpCode.attempts), else_=0),
            "created_at": case((active, OtpCode.created_at), else_=statement.excluded.created_at),
        },
    ).returning(OtpCode)
    (await session.scalars(upsert, execution_options={"populate_existing": True})).one()
    await session.commit()  # the code is emailed right after; it must be durable first


async def verify_otp(
    session: AsyncSession, email: str, otp: str, purpose: str, *, commit_success: bool = True,
) -> bool:
    """Purpose-bound, expiring, attempt-limited, single-use check."""
    email = email.lower()
    record = (await session.execute(
        select(OtpCode).where(OtpCode.purpose == purpose, OtpCode.email == email)
        .with_for_update().execution_options(populate_existing=True)
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
    ok = hmac.compare_digest(record.code_hmac, _hash(otp, purpose, email))
    if ok:
        await session.delete(record)
    # Failed attempts must survive the caller's HTTP error. On success, a caller can
    # keep the lock and consume the code in the same transaction as the protected change.
    if not ok or commit_success:
        await session.commit()
    return ok


async def failed_confirmation_count(session: AsyncSession, email: str, purpose: str) -> int:
    email = email.lower()
    row = (await session.execute(
        select(OtpFailureWindow).where(
            OtpFailureWindow.email == email,
            OtpFailureWindow.purpose == purpose,
            OtpFailureWindow.window_started_at > utcnow() - timedelta(hours=1),
        )
    )).scalar_one_or_none()
    return row.attempts if row is not None else 0


async def record_failed_confirmation(session: AsyncSession, email: str, purpose: str) -> int:
    """Atomically add one failure to the email+purpose hourly budget."""
    email = email.lower()
    now = utcnow()
    cutoff = now - timedelta(hours=1)
    if session.get_bind().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    statement = insert(OtpFailureWindow).values(
        email=email, purpose=purpose, attempts=1, window_started_at=now
    )
    statement = statement.on_conflict_do_update(
        index_elements=["purpose", "email"],
        set_={
            "attempts": case(
                (OtpFailureWindow.window_started_at <= cutoff, 1),
                else_=OtpFailureWindow.attempts + 1,
            ),
            "window_started_at": case(
                (OtpFailureWindow.window_started_at <= cutoff, now),
                else_=OtpFailureWindow.window_started_at,
            ),
        },
    ).returning(OtpFailureWindow.attempts)
    attempts = (await session.execute(statement)).scalar_one()
    await session.commit()
    return attempts


async def clear_failed_confirmations(session: AsyncSession, email: str, purpose: str) -> None:
    await session.execute(delete(OtpFailureWindow).where(
        OtpFailureWindow.email == email.lower(), OtpFailureWindow.purpose == purpose
    ))
