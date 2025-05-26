from uuid import uuid4

from sqlmodel import Session

from app.api.v1.models import User


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
