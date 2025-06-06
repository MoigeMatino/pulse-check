from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, or_, select

from app.api.v1.models import SSLLog, UptimeLog, User, Website
from app.api.v1.schemas import WebsiteCreate


def fetch_ssl_logs(
    db: Session,
    website_id: str,
    is_valid: bool | None = None,
    limit: int = 10,
    cursor: int | None = None,
) -> dict:
    """
    Retrieve SSL logs for a specific website with optional filters
    """
    query = select(SSLLog).where(SSLLog.website_id == website_id)
    if is_valid is not None:
        query = query.where(SSLLog.is_valid == is_valid)
    if cursor:
        query = query.where(SSLLog.id > cursor)

    # Order by id and limit results; fetch 1 extra to check for next page
    query = query.order_by(SSLLog.id.asc()).limit(limit + 1)

    ssl_logs = db.exec(query).all()

    # TODO: return empty list instead of raising exception
    if not ssl_logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSL logs not found for this website",
        )
    # Determine if there's a next page
    has_next = len(ssl_logs) > limit
    # TODO: improve this by trimming up to limit # of records
    if has_next:
        ssl_logs = ssl_logs[:-1]  # Trim to exclude the extra log

    next_cursor = ssl_logs[-1].id if has_next else None

    return {
        "data": ssl_logs,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }


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


def get_website_by_id(db: Session, website_id: UUID, user_id: UUID):
    """
    Retrieve a website by its ID
    """
    website = db.get(Website, website_id)
    if website and website.user_id == user_id:
        return website
    return None


def get_website_by_url(db: Session, url: str):
    """
    Retrieve a website by its ID
    """
    website_url = str(url)
    statement = select(Website).where(Website.url == website_url)
    website = db.exec(statement).first()
    return website


def get_all_websites(
    db: Session, user_id: UUID, cursor: Optional[UUID] = None, limit: Optional[int] = 10
) -> Dict:
    """
    Retrieve all websites from db with cursor-based pagination
    """
    query = select(Website).where(Website.user_id == user_id)
    if cursor:
        query = query.where(Website.id > cursor)
    query = query.order_by(Website.id.asc()).limit(limit + 1)
    websites = db.exec(query).all()

    if not websites:
        return {"data": [], "next_cursor": None, "has_next": False}

    # Check if there's a next page
    has_next = len(websites) > limit
    if has_next:
        websites = websites[:limit]  # Trim to requested limit
    next_cursor = websites[-1].id if has_next else None
    return {
        "data": websites,
        "next_cursor": str(
            next_cursor
        ),  # cast uuid website id to str for json serialization
        "has_next": has_next,
    }


def fetch_uptime_logs(
    db: Session,
    website_id: UUID,
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
    uptime_logs = db.exec(query).all()

    # TODO: return empty list instead of raising exception
    if not uptime_logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSL logs not found for this website",
        )

    # Split results
    has_next = len(uptime_logs) > limit
    uptime_logs = uptime_logs[:limit]  # Trim to requested limit

    next_cursor = uptime_logs[-1].timestamp if has_next else None
    return {
        "data": uptime_logs,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }


def update_website(
    db: Session, website_id: UUID, update_data: dict, user_id: UUID
) -> Optional[Website]:
    """Update website fields"""
    website = db.get(Website, website_id)
    if not website or website.user_id != user_id:
        return None
    for key, value in update_data.items():
        setattr(website, key, value)
    db.add(website)
    db.commit()
    db.refresh(website)
    return website


def delete_website(db: Session, website_id: UUID, user_id: UUID) -> bool:
    """Delete a website"""
    website = db.get(Website, website_id)
    if not website or website.user_id != user_id:
        return False
    db.delete(website)
    db.commit()
    return True


def search_websites(
    db: Session,
    query: str,
    user_id: UUID,
    cursor: Optional[UUID] = None,
    limit: int = 10,
) -> dict:
    """Search websites by url or name with cursor pagination"""
    sql_query = select(Website).where(Website.user_id == user_id)

    # Apply search filter
    if query:
        search_term = f"%{query}%"
        sql_query = sql_query.where(
            or_(
                Website.url.ilike(search_term),
                Website.name.ilike(search_term),
            )
        )

    if cursor:
        sql_query = sql_query.where(Website.id > cursor)

    sql_query = sql_query.order_by(Website.id.asc()).limit(limit + 1)
    websites = db.exec(sql_query).all()

    if not websites:
        return {"data": [], "next_cursor": None, "has_next": False}

    has_next = len(websites) > limit
    websites = websites[:limit]

    next_cursor = websites[-1].id if has_next else None
    return {
        "data": websites,
        "next_cursor": str(next_cursor),
        "has_next": has_next,
    }


def get_user_by_id(db: Session, user_id: UUID):
    """
    Retrieve a user by their ID
    """
    user = db.get(User, user_id)
    return user


def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by their email
    """
    user_query = select(User).where(User.email == email)
    user = db.exec(user_query).first()
    return user
