from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.exc import OperationalError
from sqlmodel import select

from app.api.v1.models import UptimeLog, Website
from app.core.worker import celery_app
from app.dependencies.db import SessionLocal
from app.utils.generic import validate_url

UPTIME_CHECK_INTERVAL_MINUTES = 5  # Interval for uptime checks in minutes


@celery_app.task
def schedule_uptime_checks():
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

            for website in websites:
                check_website_uptime.delay(website.id, website.url)
                website.uptime_last_checked = now
                db.add(website)

            db.commit()
    except OperationalError as e:
        print(f"Database connection error: {e}")
    except Exception as e:
        print(f"Error fetching websites: {e}")
        db.rollback()


@celery_app.task
def check_website_uptime(url: str, website_id: str):
    """
    Periodically checks the uptime of a website.
    """
    # validate url
    domain = validate_url(url)

    # Ping website
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(domain)
            is_up = response.status_code == 200
            status_code = response.status_code
            response_time = response.elapsed.total_seconds()

    except httpx.RequestError as exc:
        is_up = False
        status_code = None
        response_time = None
        error_message = str(exc)

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
    # define uptime log response schema
    return {"website_id": website_id, "is_up": is_up, "response_time": response_time}
