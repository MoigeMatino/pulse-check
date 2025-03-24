from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Dict

from app.tasks.ssl_checker import check_ssl_status_task
from app.api.v1.schemas import SSLStatusResponse, SSLLogResponse
from app.dependencies.db import get_db
from app.utils.website import get_website_by_id
from app.utils.ssl import all_logs_query,valid_logs_query

router = APIRouter()

@router.post("/websites/{website_id}/check-ssl", response_model=Dict[str, str])
def check_website_ssl(
    website_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Trigger an SSL check for a specific website. The result will be available in logs
    """
    website = get_website_by_id(db, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with id {website_id} not found",
        )

    # Trigger SSL check asynchronously
    check_ssl_status_task.delay(website.url, website.id)

    return {"message": "SSL check initiated. Results will be available in logs."}

@router.get("/check-ssl", response_model=SSLStatusResponse)
def check_ssl(
    url: str
) -> SSLStatusResponse:
    """
    Perform an ad-hoc SSL check for an arbitrary URL (not stored in the database)
    This runs synchronously and returns the result immediately
    """
    return check_ssl_status_task(url)

@router.get("/websites/{website_id}/ssl-logs", response_model=List[SSLLogResponse])
def get_ssl_logs(
    website_id: str,
    is_valid: bool | None = Query(None, description="Filter logs by validity"),
    db: Session = Depends(get_db)
) -> List[SSLLogResponse]:
    """
    Retrieve SSL check history for a specific website
    """
    logs_query = all_logs_query(db, website_id)    
    
    # if filter is_valid is specified  
    if is_valid is not None:
        logs_query = valid_logs_query(logs_query, is_valid)
    
    logs = db.exec(logs_query).all()
        
    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSL logs not found for this website"
        )
    
    return logs
