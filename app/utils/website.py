from typing import List

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
    db: Session, website_id: str, limit: int = 10, offset: int = 0
) -> List[UptimeLog]:
    """Fetch uptime logs for a website with pagination."""
    query = (
        select(UptimeLog)
        .where(UptimeLog.website_id == website_id)
        .order_by(UptimeLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.exec(query).all()
