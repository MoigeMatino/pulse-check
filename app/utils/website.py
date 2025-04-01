from sqlmodel import Session, select

from app.api.v1.models import Website


def get_website_by_id(db: Session, website_id: str):
    """
    Retrieve a website by its ID
    """
    statement = select(Website).where(Website.id == website_id)
    website = db.exec(statement).first()

    return website


def get_all_websites(db: Session):
    """
    Retrieve all websites from the database
    """
    statement = select(Website)
    websites = db.exec(statement).all()

    return websites
