from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.v1.schemas import (
    PaginatedUptimeLogResponse,
    UptimeLogResponse,
    WebsiteCreate,
    WebsiteRead,
    WebsiteUpdate,
)
from app.dependencies.db import get_db
from app.utils.crud import (
    create_website,
    delete_website,
    fetch_uptime_logs,
    get_website_by_id,
    get_website_by_url,
    update_website,
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
def get_uptime_logs(
    website_id: str,
    after: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    is_up: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
) -> UptimeLogResponse:
    website = get_website_by_id(db, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Website not found"
        )
    result = fetch_uptime_logs(db, website_id, after=after, limit=limit, is_up=is_up)
    return PaginatedUptimeLogResponse(**result)


@router.patch("/{website_id}", response_model=WebsiteRead)
def update_website_endpoint(
    website_id: str,
    website_update: WebsiteUpdate,
    db: Session = Depends(get_db),
) -> WebsiteRead:
    """
    Update website details (e.g., toggle is_active)
    """
    update_data = website_update.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])  # Convert HttpUrl to str
    updated_website = update_website(db, website_id, update_data)
    if not updated_website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )
    return updated_website


@router.delete("/{website_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_website_endpoint(
    website_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a website
    """
    success = delete_website(db, website_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )
    return None  # 204 returns no content
