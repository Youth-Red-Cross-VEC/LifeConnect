from datetime import date, datetime, timedelta
import asyncio
import logging
import zlib
from datetime import timezone

from zoneinfo import ZoneInfo

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import Database
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.models.otp import OtpCode, OtpFailureWindow
from app.models.refresh_session import RefreshSession
from app.utils.dates import utcnow
from app.services.certificate_service import get_certificate_service
from app.models.privacy import ErasureFile

logger = logging.getLogger(__name__)


async def try_job_lock(session: AsyncSession, job_name: str) -> bool:
    """
    Take a transaction-level Postgres advisory lock for this job.

    Returns False if another instance already holds it, so an accidental second
    scheduler cannot double-run a job. The lock is released when the session's
    transaction ends. No-op (True) on non-Postgres databases.
    """
    if session.get_bind().dialect.name != "postgresql":
        return True
    key = zlib.crc32(f"lifeconnect:{job_name}".encode())
    result = await session.execute(text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": key})
    return bool(result.scalar())


def _scheduler_today() -> date:
    """Today's date in the scheduler's configured timezone.

    The server (and everything stored) runs in UTC, but "midnight" for the job means midnight where
    the users are. Around UTC 00:00 the two can be different days, so a UTC date would expire
    requests a day early or late.
    """

    return datetime.now(ZoneInfo(get_settings().SCHEDULER_TIMEZONE)).date()


async def expire_blood_requests(db: Database) -> None:
    """
    Mark overdue pending and approved requests as expired.
    Runs daily at midnight.
    """
    try:
        async with db.session() as session:
            if not await try_job_lock(session, "expire_blood_requests"):
                logger.info("expire_blood_requests already running elsewhere; skipping")
                return
            repo = BloodRequestRepository(session)
            count = await repo.expire_overdue_requests(_scheduler_today())
            logger.info(f"Expired {count} blood request(s)")
    except Exception as e:
        logger.error(f"Error in expire_blood_requests: {type(e).__name__}")
        raise RuntimeError("Scheduled job failed") from None


async def activate_donor_status(db: Database) -> None:
    """
    Make donors available again once DONATION_COOLDOWN_DAYS have passed since their last donation.
    Runs daily at midnight.

    Only ``is_available`` is touched: a donor an admin disabled (``active_status=False``) must stay
    disabled, whatever their donation history.
    """
    try:
        async with db.session() as session:
            if not await try_job_lock(session, "activate_donor_status"):
                logger.info("activate_donor_status already running elsewhere; skipping")
                return
            repo = DonorRepository(session)
            cutoff_date = _scheduler_today() - timedelta(days=get_settings().DONATION_COOLDOWN_DAYS)
            count = await repo.reactivate_eligible_donors(cutoff_date)
            logger.info(f"Reactivated {count} donor(s)")
    except Exception as e:
        logger.error(f"Error in activate_donor_status: {type(e).__name__}")
        raise RuntimeError("Scheduled job failed") from None


async def purge_expired_auth_records(db: Database) -> None:
    """
    Delete expired one-time codes and refresh sessions (nothing can use them any more).
    Runs daily; see docs/DATA_RETENTION.md.
    """
    try:
        async with db.session() as session:
            if not await try_job_lock(session, "purge_expired_auth_records"):
                logger.info("purge_expired_auth_records already running elsewhere; skipping")
                return
            now = utcnow()
            otps = await session.execute(delete(OtpCode).where(OtpCode.expires_at <= now))
            sessions = await session.execute(delete(RefreshSession).where(
                RefreshSession.expires_at <= now
            ))
            failures = await session.execute(delete(OtpFailureWindow).where(
                OtpFailureWindow.window_started_at <= now - timedelta(hours=1)
            ))
            logger.info(
                "Purged %s OTP(s), %s refresh token(s), and %s OTP failure window(s)",
                otps.rowcount, sessions.rowcount, failures.rowcount,
            )
    except Exception as e:
        logger.error(f"Error in purge_expired_auth_records: {type(e).__name__}")
        raise RuntimeError("Scheduled job failed") from None


async def purge_old_certificates(db: Database) -> None:
    """Delete certificate files older than the configured retention period."""
    try:
        async with db.session() as session:
            if not await try_job_lock(session, "purge_old_certificates"):
                logger.info("purge_old_certificates already running elsewhere; skipping")
                return
            service = get_certificate_service()
            pending = await session.scalars(select(ErasureFile).order_by(ErasureFile.filename).with_for_update(skip_locked=True))
            for entry in pending:
                try:
                    await service.delete_certificate(entry.filename)
                except OSError as exc:
                    logger.warning("Erasure file cleanup will retry: %s", type(exc).__name__)
                else:
                    if not service.entry_remains(entry.filename):
                        await session.delete(entry)
            cutoff = utcnow().replace(tzinfo=timezone.utc).timestamp() - get_settings().CERT_RETENTION_DAYS * 86400
            deleted = await asyncio.to_thread(service.purge_expired_files, cutoff)
            logger.info("Purged %s expired certificate file(s)", deleted)
    except Exception as e:
        logger.error("Error in purge_old_certificates: %s", type(e).__name__)
        raise RuntimeError("Scheduled job failed") from None


def setup_scheduled_jobs(scheduler, db: Database) -> None:
    """Configure all scheduled jobs."""

    # Expire requests at midnight
    scheduler.add_cron_job(
        expire_blood_requests,
        job_id="expire_blood_requests",
        hour=0,
        minute=0,
        db=db,
    )

    # Make donors available again after their cooldown, at midnight
    scheduler.add_cron_job(
        activate_donor_status,
        job_id="activate_donor_status",
        hour=0,
        minute=0,
        db=db,
    )

    # Drop expired OTPs and refresh sessions
    scheduler.add_cron_job(
        purge_expired_auth_records,
        job_id="purge_expired_auth_records",
        hour=0,
        minute=2,
        db=db,
    )

    scheduler.add_cron_job(
        purge_old_certificates,
        job_id="purge_old_certificates",
        hour=0,
        minute=4,
        db=db,
    )

    logger.info("Scheduled jobs configured successfully")
