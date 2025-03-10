from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select
from app.core.models import Website

def get_website_by_id(db: Session, website_id: str):
    """
    Retrieve a website by its ID
    """
    statement = select(Website).where(Website.id == website_id)
    website = db.exec(statement).first()
    
    return website