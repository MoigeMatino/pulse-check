from fastapi import Query
from sqlmodel import Session, select

from app.api.v1.models import SSLLog


def get_ssl_logs_by_website_id(db: Session, website_id: str):
    """
    Retrieve SSL logs for a specific website by its ID
    """
    statement = select(SSLLog).where(SSLLog.website_id == website_id)
    ssl_logs = db.exec(statement).all()

    return ssl_logs


def valid_logs_query(query: Query, is_valid: bool) -> Query:
    """Apply validity filter to  query if specified"""
    return query.where(SSLLog.is_valid == is_valid)


def all_logs_query(db: Session, website_id: str) -> Query:
    """Create a query to retrieve SSL logs for a specific website"""
    return select(SSLLog).where(SSLLog.website_id == website_id)
