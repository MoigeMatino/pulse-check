from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.v1.models import SSLLog
from app.api.v1.schemas import PaginatedSSLLogResponse, SSLStatusResponse
from app.dependencies.db import get_db
from app.tasks.ssl_checker import check_ssl_status_task
from app.utils.ssl import all_logs_query, valid_logs_query
from app.utils.website import get_website_by_id

router = APIRouter()


@router.post("/websites/{website_id}/ssl-checks", response_model=Dict[str, str])
def check_website_ssl(website_id: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Trigger an SSL check for a specific website. The result will be available in logs
    """
    website = get_website_by_id(db, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )
    # TODO: check if ssl_check_enabled is True and website is active
    # Trigger SSL check asynchronously
    check_ssl_status_task.delay(website.url, website.id)

    return {"message": "SSL check initiated. Results will be available in logs."}


@router.get("/ssl-checks", response_model=SSLStatusResponse)
def check_ssl(url: str) -> SSLStatusResponse:
    """
    Perform an ad-hoc SSL check for an arbitrary URL (not stored in the database)
    This runs synchronously and returns the result immediately
    """
    return check_ssl_status_task(url)


@router.get("/websites/{website_id}/ssl-logs", response_model=PaginatedSSLLogResponse)
def get_ssl_logs(
    website_id: str,
    is_valid: bool | None = Query(None, description="Filter logs by validity"),
    limit: int = Query(10, ge=1, le=100, description="Number of logs to return"),
    cursor: int
    | None = Query(None, ge=0, description="ID of the last log from the previous page"),
    db: Session = Depends(get_db),
) -> PaginatedSSLLogResponse:
    """
    Retrieve SSL check history for a specific website
    """
    logs_query = all_logs_query(db, website_id)

    # if filter is_valid is specified
    if is_valid is not None:
        logs_query = valid_logs_query(logs_query, is_valid)

    # Apply cursor filter
    if cursor is not None:
        logs_query = logs_query.where(SSLLog.id > cursor)

    # Order by id and limit results; fetch 1 extra to check for next page
    logs_query = logs_query.order_by(SSLLog.id.asc()).limit(limit + 1)

    logs = db.exec(logs_query).all()

    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSL logs not found for this website",
        )
    # Determine if there's a next page
    has_next = len(logs) > limit
    if has_next:
        logs = logs[:-1]  # Exclude the extra log
    next_cursor = logs[-1].id if logs and has_next else None

    return PaginatedSSLLogResponse(data=logs, next_cursor=next_cursor)
