from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.v1.schemas import UptimeLogResponse, WebsiteCreate, WebsiteRead
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


@router.get("/{website_id}/uptime-logs", response_model=List[UptimeLogResponse])
def get_uptime_logs_endpoint(
    website_id: str,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[UptimeLogResponse]:
    """
    Retrieve uptime logs for a specific website with pagination
    """
    website = get_website_by_id(db, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )
    logs = get_uptime_logs(db, website_id, limit, offset)
    return logs
