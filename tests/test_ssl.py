from datetime import datetime

from fastapi import status
from sqlmodel import Session

from app.api.v1.models import SSLLog, Website
from app.api.v1.schemas import SSLLogResponse, SSLStatusResponse


# Test the /websites/{website_id}/ssl-checks endpoint
def test_check_website_ssl(client, test_db: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference
    # Add a website to the database
    website = Website(url="https://example.com", name="Example Website", user=user)
    test_db.add(website)
    test_db.commit()

    # Trigger the SSL check
    response = client.post(f"/websites/{website.id}/ssl-checks")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "SSL check initiated. Results will be available in logs."
    }


# Test the /ssl-checks endpoint
def test_check_ssl(client):
    # Perform an ad-hoc SSL check
    response = client.get("/ssl-checks", params={"url": "https://example.com"})
    assert response.status_code == status.HTTP_200_OK

    # Validate the response schema
    ssl_status = SSLStatusResponse(**response.json())
    assert isinstance(ssl_status, SSLStatusResponse)
    assert ssl_status.valid


# Test the /websites/{website_id}/ssl-logs endpoint
def test_get_ssl_logs(client, test_db: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference

    # Add a website and SSL logs to the database
    website = Website(url="https://example.com", name="Example Website", user=user)
    test_db.add(website)
    test_db.commit()

    ssl_log = SSLLog(
        id=4,
        website_id=website.id,
        valid_until=datetime(2025, 1, 1, 0, 0, 0),
        issuer="Example Issuer",
        is_valid=True,
        error=None,
    )
    test_db.add(ssl_log)
    test_db.commit()

    # Retrieve SSL logs
    response = client.get(f"/websites/{website.id}/ssl-logs?limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "next_cursor" in data
    assert len(data["data"]) == 1, f"Expected 1 log, got {data['data']}"
    log = SSLLogResponse(**data["data"][0])
    assert log.id == 4
    assert log.website_id == website.id
    assert data["next_cursor"] is None


# Test the /websites/{website_id}/ssl-logs endpoint for a non-existent website
def test_get_ssl_logs_not_found(client):
    response = client.get("/websites/999/ssl-logs?limit=2")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Website with id 999 not found"}


# Pagination and filtering tests
def test_get_ssl_logs_basic_pagination(client, test_logs):
    website_id = test_logs[0].website_id
    response = client.get(f"/websites/{website_id}/ssl-logs?limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1
    assert data["data"][1]["id"] == 2
    assert data["next_cursor"] == 2


def test_get_ssl_logs_with_cursor(client, test_logs):
    website_id = test_logs[0].website_id
    response = client.get(f"/websites/{website_id}/ssl-logs?limit=2&cursor=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1  # Only 1 log left (id=3)
    assert data["data"][0]["id"] == 3
    assert data["next_cursor"] is None


def test_get_valid_logs_only(client, test_logs):
    website_id = test_logs[0].website_id
    response = client.get(f"/websites/{website_id}/ssl-logs?limit=2&is_valid=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1
    assert data["data"][1]["id"] == 3
    assert data["next_cursor"] is None  # Only 2 valid logs
    assert all(log["is_valid"] for log in data["data"])


def test_get_invalid_logs_only(client, test_logs):
    website_id = test_logs[0].website_id
    response = client.get(f"/websites/{website_id}/ssl-logs?limit=2&is_valid=false")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1  # Only 1 invalid log
    assert data["data"][0]["id"] == 2
    assert data["next_cursor"] is None
    assert all(not log["is_valid"] for log in data["data"])
