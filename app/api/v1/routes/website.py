from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.v1.schemas import (
    PaginatedUptimeLogResponse,
    UptimeLogResponse,
    WebsiteCreate,
    WebsiteRead,
)
from app.dependencies.db import get_db
from app.utils.website import (
    create_website,
    get_uptime_logs,
    get_website_by_id,
    get_website_by_url,
)

router = APIRouter(prefix="/websites", tags=["websites"])


@router.post("/", response_model=WebsiteRead, status_code=status.HTTP_201_CREATED)
def create_website_endpoint(
    website: WebsiteCreate, db: Session = Depends(get_db)
) -> WebsiteRead:
    """
    Register a new website for uptime monitoring
    """
    # Check if the website already exists
    existing_website = get_website_by_url(db, website.url)
    if existing_website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Website with URL {website.url} already exists",
        )
    new_website = create_website(db, website)
    return new_website


@router.get("/{website_id}/uptime-logs", response_model=PaginatedUptimeLogResponse)
def get_uptime_logs_endpoint(
    website_id: str,
    after: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    is_up: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
) -> UptimeLogResponse:
    website = get_website_by_id(db, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    result = get_uptime_logs(db, website_id, after=after, limit=limit, is_up=is_up)
    return PaginatedUptimeLogResponse(**result)
