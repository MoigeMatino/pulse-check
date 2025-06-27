import logging
import random
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from celery.utils.log import get_task_logger
from sqlalchemy.exc import OperationalError
from sqlmodel import select

from app.api.v1.models import UptimeLog, Website
from app.core.worker import celery_app
from app.dependencies.db import SessionLocal
from app.utils.generic import validate_url

logging.basicConfig(level=logging.INFO)
logger = get_task_logger(__name__)

UPTIME_CHECK_INTERVAL_MINUTES = 5  # Interval for uptime checks in minutes
BASE_RETRY_DELAY = 30  # Base delay for retries in seconds


@celery_app.task(
    bind=True,
    max_retries=3,
)
def schedule_uptime_checks(self):
    """Periodically check websites that are due for an uptime check."""

    # Fetch websites that need to be checked
    # Check if the website is active and if the last check was more than
    # the UPTIME_CHECK_INTERVAL_MINUTES or if it has never been checked
    try:
        with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            statement = select(Website).where(
                Website.is_active.is_(True),
                Website.uptime_last_checked.is_(None)
                | (
                    Website.uptime_last_checked
                    <= now - timedelta(minutes=UPTIME_CHECK_INTERVAL_MINUTES)
                ),  # check if X minutes have passed since uptime_last_checked
            )
            websites = db.exec(statement).all()
            if not websites:
                logger.info("No websites due for uptime check.")
                return
            for website in websites:
                check_website_uptime.delay(website.url, str(website.id))
                website.uptime_last_checked = now
                db.add(website)
            db.commit()
            logger.info(f"Uptime checks ran for {len(websites)} websites.")
    except OperationalError as e:
        # if database error occurs, retry with jitter
        delay = random.uniform(0, BASE_RETRY_DELAY * (2**self.request.retries))
        logger.error(f"Database connection error: {e}, retrying in {delay:.2f}s")
        self.retry(countdown=delay)
    except Exception as e:
        logger.error(f"Error scheduling uptime checks: {e}", exc_info=True)
        db.rollback()
        raise


@celery_app.task(bind=True, max_retries=3)
def check_website_uptime(self, url: str, website_id: str):
    """
    Periodically checks the uptime of a website.
    """
    try:
        UUID(website_id)  # Validate UUID
    except ValueError:
        logger.error(f"Invalid website_id: {website_id}")
        return {"website_id": website_id, "error": "Invalid website_id"}

    try:
        # validate url
        domain = validate_url(url)
        with httpx.Client(timeout=10.0) as client:
            response = client.get(domain)
            is_up = response.status_code == 200
            status_code = response.status_code
            response_time = response.elapsed.total_seconds()

    except httpx.RequestError as exc:
        if isinstance(exc, httpx.TimeoutException):
            # if a timeout occurs, retry with jitter
            delay = random.uniform(0, BASE_RETRY_DELAY * (2**self.request.retries))
            logger.warning(
                f"HTTP check failed for {url}: {exc}, retrying in {delay:.2f}s"
            )
            self.retry(countdown=delay)
        logger.warning(f"Uptime check failed for {url}: {exc}")
        is_up = False
        status_code = None
        response_time = None
        error_message = str(exc)

    try:
        with SessionLocal() as db:
            # Save the result to the database
            uptime_log = UptimeLog(
                website_id=website_id,
                timestamp=datetime.now(timezone.utc),
                is_up=is_up,
                status_code=status_code,
                response_time=response_time,
                error_message=error_message if not is_up else None,
            )

            db.add(uptime_log)
            db.commit()
    except OperationalError as e:
        delay = random.uniform(0, BASE_RETRY_DELAY * (2**self.request.retries))
        logger.error(
            f"Database error saving uptime log for {url}: {e}, retrying in {delay:.2f}s"
        )
        self.retry(countdown=delay)
    # define uptime log response schema
    return {"website_id": website_id, "is_up": is_up, "response_time": response_time}
