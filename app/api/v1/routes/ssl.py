from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.tasks.ssl_checker import SSLCheckerService
from app.api.v1.schemas import SSLStatusResponse, SSLLogResponse
from app.dependencies.db import get_db
from app.utils.website import get_website_by_id
from app.utils.ssl import get_ssl_logs_by_website_id

router = APIRouter()

@router.post("/websites/{website_id}/check-ssl", response_model=SSLStatusResponse)
def check_website_ssl(
    website_id: str,
    db: Session = Depends(get_db),
    ssl_checker: SSLCheckerService = Depends(SSLCheckerService)
) -> SSLStatusResponse:
    """
    Manually trigger an SSL check for a specific website
    """
    website = get_website_by_id(db, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )
    
    # Perform the SSL check synchronously
    ssl_status = ssl_checker.check_ssl_status(website.url, website.id, db)
    return ssl_status

@router.get("/check-ssl", response_model=SSLStatusResponse)
def check_ssl(
    url: str,
    ssl_checker: SSLCheckerService = Depends(SSLCheckerService)
) -> SSLStatusResponse:
    """
    Perform an ad-hoc SSL check for a given arbitrary URL (not stored in the database)
    """
    # Perform the SSL check synchronously
    ssl_status = ssl_checker.check_ssl_status(url=url)
    return ssl_status

@router.get("/websites/{website_id}/ssl-logs", response_model=List[SSLLogResponse])
def get_ssl_logs(
    website_id: str,
    db: Session = Depends(get_db)
) -> List[SSLLogResponse]:
    """
    Retrieve SSL check history for a specific website
    """
    logs = get_ssl_logs_by_website_id(db, website_id)
    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSL logs not found for this website"
        )
    return logs