from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app import app
from app.api.v1.models import UptimeLog  # noqa: F401
from app.api.v1.models import NotificationPreference, SSLLog, User, Website
from app.dependencies.db import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,  # Use a single, fixed connection
    connect_args={"check_same_thread": False},  # Required for SQLite
)


@pytest.fixture(scope="function")
def test_db():
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
        session.commit()
    finally:
        session.close()
        SQLModel.metadata.drop_all(engine)


# Mock query functions for testing
def mock_all_logs_query(db: Session, website_id: str):
    return select(SSLLog).where(SSLLog.website_id == website_id)


def mock_valid_logs_query(query, is_valid: bool):
    return query.where(SSLLog.is_valid == is_valid)


# Fixture for the FastAPI TestClient
@pytest.fixture(scope="function")
def client(test_db, monkeypatch):
    """Provides a test client with overridden database dependency"""

    app.dependency_overrides[get_db] = lambda: test_db
    monkeypatch.setattr("app.utils.ssl.all_logs_query", mock_all_logs_query)
    monkeypatch.setattr("app.utils.ssl.valid_logs_query", mock_valid_logs_query)

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def user_with_notification_preference(test_db: Session):
    """
    Fixture that creates a User with a NotificationPreference
    """
    user = User(name="Test User", email="testuser@email.com")
    test_db.add(user)
    test_db.commit()

    # Create a notification preference for the user
    notification_preference = NotificationPreference(
        user_id=user.id, notification_type="email"
    )
    test_db.add(notification_preference)
    test_db.commit()

    # Return the user and notification preference
    return user, notification_preference


@pytest.fixture(name="test_website")
def create_test_website(test_db: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference

    website = Website(
        id="1", name="Example Website", url="https://example.com", user=user
    )
    test_db.add(website)
    test_db.commit()
    return website


# Fixture for test SSL logs
@pytest.fixture(name="test_logs")
def create_test_logs(test_db: Session, test_website: Website):
    now = datetime.now(timezone.utc)
    logs = [
        SSLLog(
            id=1,  # Explicit IDs for pagination
            website_id=test_website.id,
            valid_until=now + timedelta(days=30),
            is_valid=True,
            issuer="Issuer1",
        ),
        SSLLog(
            id=2,
            website_id=test_website.id,
            valid_until=now + timedelta(days=-1),  # Expired
            is_valid=False,
            error="Certificate expired",
            issuer="Issuer2",
        ),
        SSLLog(
            id=3,
            website_id=test_website.id,
            valid_until=now + timedelta(days=60),
            is_valid=True,
            issuer="Issuer3",
        ),
    ]
    test_db.add_all(logs)
    test_db.commit()

    return logs
