from datetime import date, datetime, timedelta
import logging
import zlib

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import Database
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.models.donor import PersonalDetails, DonorDetail
from app.models.otp import OtpCode
from app.models.refresh_session import RefreshSession

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


async def expire_blood_requests(db: Database) -> None:
    """
    Mark overdue pending requests as expired.
    Runs daily at midnight.
    """
    try:
        async with db.session() as session:
            if not await try_job_lock(session, "expire_blood_requests"):
                logger.info("expire_blood_requests already running elsewhere; skipping")
                return
            repo = BloodRequestRepository(session)
            current_date = date.today()
            count = await repo.expire_overdue_requests(current_date)
            logger.info(f"Expired {count} blood request(s)")
    except Exception as e:
        logger.error(f"Error in expire_blood_requests: {e}")


async def activate_donor_status(db: Database) -> None:
    """
    Reactivate donors who haven't donated in DONOR_ELIGIBILITY_DAYS days.
    Runs daily at midnight.
    """
    try:
        async with db.session() as session:
            if not await try_job_lock(session, "activate_donor_status"):
                logger.info("activate_donor_status already running elsewhere; skipping")
                return
            repo = DonorRepository(session)
            cutoff_date = date.today() - timedelta(days=get_settings().DONOR_ELIGIBILITY_DAYS)
            count = await repo.reactivate_eligible_donors(cutoff_date)
            logger.info(f"Reactivated {count} donor(s)")
    except Exception as e:
        logger.error(f"Error in activate_donor_status: {e}")


async def increment_donor_ages(db: Database) -> None:
    """
    Increment age for donors on their birthday.
    Runs daily at midnight.
    """
    try:
        from sqlalchemy import select, extract

        async with db.session() as session:
            if not await try_job_lock(session, "increment_donor_ages"):
                logger.info("increment_donor_ages already running elsewhere; skipping")
                return
            current_date = date.today()

            # Find donors whose birthday is today using SQL extract() — correct approach
            query = (
                select(PersonalDetails)
                .join(DonorDetail, DonorDetail.personal_details_id == PersonalDetails.id)
                .where(
                    extract("month", PersonalDetails.date_of_birth) == current_date.month,
                    extract("day", PersonalDetails.date_of_birth) == current_date.day,
                )
            )

            result = await session.execute(query)
            birthday_donors = result.scalars().all()

            for personal in birthday_donors:
                personal.age += 1

            await session.commit()
            logger.info(f"Incremented age for {len(birthday_donors)} donor(s)")
    except Exception as e:
        logger.error(f"Error in increment_donor_ages: {e}")


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
            now = datetime.utcnow()
            otps = await session.execute(delete(OtpCode).where(OtpCode.expires_at < now))
            sessions = await session.execute(delete(RefreshSession).where(RefreshSession.expires_at < now))
            logger.info(f"Purged {otps.rowcount} expired OTP(s) and {sessions.rowcount} expired refresh session(s)")
    except Exception as e:
        logger.error(f"Error in purge_expired_auth_records: {e}")


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

    # Reactivate donors at midnight
    scheduler.add_cron_job(
        activate_donor_status,
        job_id="activate_donor_status",
        hour=0,
        minute=0,
        db=db,
    )

    # Increment ages at midnight
    scheduler.add_cron_job(
        increment_donor_ages,
        job_id="increment_donor_ages",
        hour=0,
        minute=1,  # Offset by 1 minute to avoid conflicts
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

    logger.info("Scheduled jobs configured successfully")
