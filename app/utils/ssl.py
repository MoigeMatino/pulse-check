from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.api.v1.models import SSLLog


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

    if not ssl_logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSL logs not found for this website",
        )
    # Determine if there's a next page
    has_next = len(ssl_logs) > limit
    if has_next:
        ssl_logs = ssl_logs[:-1]  # Trim to exclude the extra log

    next_cursor = ssl_logs[-1].id if has_next else None

    return {
        "data": ssl_logs,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }
