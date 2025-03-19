import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from app import app
from app.dependencies.db import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,  # Use a single, fixed connection
    connect_args={"check_same_thread": False},  # Required for SQLite
)

# Fixture for the database session
@pytest.fixture(name="session")
def session_fixture():
    """Creates a new database session for each test"""
    with Session(engine) as session:
        yield session

# Fixture for the test database
@pytest.fixture(scope="function")
def test_db():
    """Creates the test database schema"""
    SQLModel.metadata.create_all(engine)
    yield  # Yield control to the tests
    SQLModel.metadata.drop_all(engine)  # Clean up after the tests

# Fixture for the FastAPI TestClient
@pytest.fixture(scope="function")
def client(test_db):
    """Provides a test client with overridden database dependency"""
    # Override the get_db dependency to use the test database session
    def get_db_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = get_db_override

    # Create a TestClient for the FastAPI app
    with TestClient(app) as client:
        yield client

    # Clear the dependency overrides after the tests
    app.dependency_overrides.clear()