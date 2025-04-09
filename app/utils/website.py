from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.api.v1.models import UptimeLog, Website
from app.api.v1.schemas import WebsiteCreate


def create_website(db: Session, website: WebsiteCreate) -> Website:
    """Create a new website in the database"""
    # Convert HttpUrl to str explicitly
    website_data = website.model_dump()
    website_data["url"] = str(website.url)  # HttpUrl -> str
    website_in = Website(**website_data)
    db.add(website_in)
    db.commit()
    db.refresh(website_in)
    return website_in


def get_website_by_id(db: Session, website_id: str):
    """
    Retrieve a website by its ID
    """
    website = db.get(Website, website_id)
    return website


def get_website_by_url(db: Session, url: str):
    """
    Retrieve a website by its ID
    """
    website_url = str(url)
    statement = select(Website).where(Website.url == website_url)
    website = db.exec(statement).first()
    return website


def get_all_websites(db: Session):
    """
    Retrieve all websites from the database
    """
    statement = select(Website)
    websites = db.exec(statement).all()

    return websites


def get_uptime_logs(
    db: Session,
    website_id: str,
    after: Optional[datetime] = None,
    limit: int = 10,
    is_up: Optional[bool] = None,
) -> dict:
    query = select(UptimeLog).where(UptimeLog.website_id == website_id)
    if is_up is not None:
        query = query.where(UptimeLog.is_up == is_up)
    if after:
        query = query.where(UptimeLog.timestamp > after)

    # Fetch one extra to check if more exist
    query = query.order_by(UptimeLog.timestamp.asc()).limit(limit + 1)
    logs = db.exec(query).all()

    # Split results
    has_next = len(logs) > limit
    logs = logs[:limit]  # Trim to requested limit

    next_cursor = logs[-1].timestamp if logs and has_next else None
    return {
        "data": logs,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }


def update_website(
    db: Session, website_id: str, update_data: dict
) -> Optional[Website]:
    """Update website fields"""
    website = db.get(Website, website_id)
    if not website:
        return None
    for key, value in update_data.items():
        setattr(website, key, value)
    db.add(website)
    db.commit()
    db.refresh(website)
    return website
