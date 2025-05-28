from uuid import uuid4

from sqlmodel import Session

from app.api.v1.models import User
from app.auth import get_password_hash


def test_register_user(client):
    new_user = {
        "email": "newuser@example.com",
        "password": "newuserpassword",
        "slack_webhook": "https://hooks.slack.com/services/T00000000/B00000000/",
        "phone_number": "+1234567890",
    }
    response = client.post("/auth/register", json=new_user)
    assert response.status_code == 201


def test_login_user(client, test_db: Session):
    user = User(
        id=uuid4(),
        name="Test User",
        email="testuser@email.com",
        password_hash="$2a$12$4V0eTBxLKC7TPnnDXq/iAuRmxcTR6MhNJT18ihePzq23RbFc1XB6W",
    )
    test_db.add(user)
    test_db.commit()

    response = client.post(
        "/auth/login", data={"username": "testuser@email.com", "password": "mypassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_unregistered_user(client):
    response = client.post(
        "/auth/login",
        data={"username": "unregistereduser@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_refresh_token_with_cookie(client, test_db: Session):
    user_data = {
        "email": f"test{uuid4()}@email.com",
        "password": "mysecretpassword",
        "slack_webhook": "https://hooks.slack.com/abc",
        "phone_number": "+1234567890",
    }
    hash_password = get_password_hash(user_data["password"])
    user = User(
        id=uuid4(),
        name="New User",
        email=user_data["email"],
        password_hash=hash_password,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Login to get access token and set refresh token cookie
    response = client.post(
        "/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.cookies
    access_token = response.json()["access_token"]
    refresh_token = response.cookies["refresh_token"]

    # Use refresh token via cookie
    response = client.post(
        "/auth/refresh",
        cookies={"refresh_token": refresh_token},  # Explicitly pass cookie
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    new_access_token = response.json()["access_token"]
    assert new_access_token != access_token

    # Test missing refresh token
    client.cookies.clear()
    response = client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token missing"
