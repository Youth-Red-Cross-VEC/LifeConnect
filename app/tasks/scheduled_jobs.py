from datetime import date, timedelta
import logging

from app.core.database import Database
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.models.donor import PersonalDetails, DonorDetail

logger = logging.getLogger(__name__)


async def expire_blood_requests(db: Database) -> None:
    """
    Mark overdue pending requests as expired.
    Runs daily at midnight.
    """
    try:
        async with db.session() as session:
            repo = BloodRequestRepository(session)
            current_date = date.today()
            count = await repo.expire_overdue_requests(current_date)
            logger.info(f"Expired {count} blood request(s)")
    except Exception as e:
        logger.error(f"Error in expire_blood_requests: {e}")


async def activate_donor_status(db: Database) -> None:
    """
    Reactivate donors who haven't donated in 60+ days.
    Runs daily at midnight.
    """
    try:
        async with db.session() as session:
            repo = DonorRepository(session)
            cutoff_date = date.today() - timedelta(days=60)
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

    logger.info("Scheduled jobs configured successfully")
