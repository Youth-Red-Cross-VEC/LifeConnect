from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

# How late (after its scheduled time) a job may still start: covers a container restart or a deploy.
MISFIRE_GRACE_SECONDS = 6 * 60 * 60


class Scheduler:
    """
    Async scheduler for background jobs using APScheduler.
    
    Handles scheduled tasks like:
    - Blood request expiration (daily at midnight)
    - Donor status reactivation (daily at midnight)
    - Age increment on birthdays (daily at midnight)
    """

    def __init__(self, timezone: str = "Asia/Kolkata"):
        # CronTrigger does not inherit the scheduler timezone when it is built separately, so keep
        # it here and pass it explicitly; otherwise SCHEDULER_TIMEZONE would be silently ignored and
        # "midnight" would be the container's local (usually UTC) midnight.
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(
            timezone=timezone,
            job_defaults={
                # APScheduler's default grace is 1 second: a restart a moment after 00:00 would silently skip
                # the day. Every job is idempotent or date-cutoff based, so a late run is safe; coalesce
                # collapses several missed runs into one, and max_instances stops a slow run overlapping.
                "misfire_grace_time": MISFIRE_GRACE_SECONDS,
                "coalesce": True,
                "max_instances": 1,
            },
        )
        self._jobs: dict[str, Any] = {}

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        hour: int = 0,
        minute: int = 0,
        **kwargs,
    ) -> None:
        """
        Add a cron job that runs at a specific time daily.
        
        Args:
            func: Async function to execute
            job_id: Unique identifier for the job
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            **kwargs: Additional arguments to pass to the function
        """
        self.scheduler.add_job(
            func,
            CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )
        self._jobs[job_id] = {"type": "cron", "hour": hour, "minute": minute}
        logger.info(f"Added cron job '{job_id}' scheduled at {hour:02d}:{minute:02d}")

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        minutes: int = 30,
        **kwargs,
    ) -> None:
        """
        Add an interval job that runs periodically.
        
        Args:
            func: Async function to execute
            job_id: Unique identifier for the job
            minutes: Interval in minutes
            **kwargs: Additional arguments to pass to the function
        """
        self.scheduler.add_job(
            func,
            IntervalTrigger(minutes=minutes),
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )
        self._jobs[job_id] = {"type": "interval", "minutes": minutes}
        logger.info(f"Added interval job '{job_id}' running every {minutes} minutes")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self) -> None:
        """Gracefully shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")

    def get_jobs(self) -> dict[str, Any]:
        """Get all registered jobs."""
        return self._jobs


# Global scheduler instance
scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """Get the global scheduler instance."""
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    return scheduler


def init_scheduler(timezone: str = "Asia/Kolkata") -> Scheduler:
    """Initialize the global scheduler instance."""
    global scheduler
    scheduler = Scheduler(timezone=timezone)
    return scheduler


def start_scheduler_if_enabled(settings, database) -> Scheduler | None:
    """Start the job scheduler only when SCHEDULER_ENABLED and RUN_SCHEDULER are true here."""
    if not settings.SCHEDULER_ENABLED or not settings.RUN_SCHEDULER:
        logger.info(
            "Scheduler disabled for this process "
            f"(SCHEDULER_ENABLED={settings.SCHEDULER_ENABLED}, RUN_SCHEDULER={settings.RUN_SCHEDULER})"
        )
        return None

    from app.tasks import setup_scheduled_jobs

    instance = init_scheduler(timezone=settings.SCHEDULER_TIMEZONE)
    setup_scheduled_jobs(instance, database)
    instance.start()
    return instance
