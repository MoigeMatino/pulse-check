from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import validators

from app.api.v1.models import UptimeLog
from app.core.worker import celery_app
from app.dependencies.db import SessionLocal
from app.exceptions.ssl import InvalidURLException


@celery_app.task
def check_website_uptime(url: str, website_id: str):
    """
    Periodically checks the uptime of a website.
    """
    # Ping website
    try:
        if not validators.url(url):
            raise InvalidURLException("Invalid URL format")
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or parsed_url.path
        if not domain:
            raise InvalidURLException("Invalid URL: No domain found")

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

    return {"website_id": website_id, "is_up": is_up, "response_time": response_time}
