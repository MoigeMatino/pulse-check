from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.v1.models import User
from app.api.v1.schemas import PaginatedSSLLogResponse, SSLStatusResponse
from app.auth import get_current_user
from app.dependencies.db import get_db
from app.tasks.ssl_checker import check_ssl_status_task
from app.utils.crud import fetch_ssl_logs, get_website_by_id

router = APIRouter()


@router.post("/websites/{website_id}/ssl-checks", response_model=Dict[str, str])
def check_website_ssl(
    website_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Trigger an SSL check for a specific website. The result will be available in logs
    """
    website = get_website_by_id(db, website_id, current_user.id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )
    # Check if ssl_check_enabled is True and website is active
    if not website.ssl_check_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSL checks are disabled for website {website_id}",
        )
    if not website.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Website {website_id} is inactive",
        )
    # Trigger SSL check asynchronously
    check_ssl_status_task.delay(website.url, website.id)

    return {"message": "SSL check initiated. Results will be available in logs."}


# * Good candidate for api key authentication
@router.get("/ssl-checks", response_model=SSLStatusResponse)
def check_ssl(url: str) -> SSLStatusResponse:
    """
    Perform an ad-hoc SSL check for an arbitrary URL (not stored in the database)
    This runs synchronously and returns the result immediately
    """
    return check_ssl_status_task(url)


@router.get("/websites/{website_id}/ssl-logs", response_model=PaginatedSSLLogResponse)
def get_ssl_logs(
    website_id: UUID,
    is_valid: bool | None = Query(None, description="Filter logs by validity"),
    limit: int = Query(10, ge=1, le=100, description="Number of logs to return"),
    cursor: int
    | None = Query(None, ge=0, description="ID of the last log from the previous page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedSSLLogResponse:
    """
    Retrieve SSL check history for a specific website
    """
    website = get_website_by_id(db, website_id, current_user.id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )

    ssl_logs = fetch_ssl_logs(
        db, website_id, is_valid=is_valid, limit=limit, cursor=cursor
    )
    return PaginatedSSLLogResponse(**ssl_logs)
