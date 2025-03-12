from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select
from app.api.v1.models import SSLLog

def get_ssl_logs_by_website_id(db: Session, website_id: str):
    """
    Retrieve SSL logs for a specific website by its ID
    """
    statement = select(SSLLog).where(SSLLog.website_id == website_id)
    ssl_logs = db.exec(statement).all()

    return ssl_logs