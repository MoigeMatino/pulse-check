from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from fastapi import status
from sqlmodel import Session

from app.api.v1.models import SSLLog, Website
from app.api.v1.schemas import SSLLogResponse, SSLStatusResponse


# Test the /websites/{website_id}/ssl-checks endpoint
def test_check_website_ssl(client, test_db: Session, logged_in_user):
    user = logged_in_user["user"]
    headers = logged_in_user["headers"]

    # Add a website to the database
    website = Website(
        id=uuid4(), url="https://example.com", name="Example Website", user=user
    )
    test_db.add(website)
    test_db.commit()

    with patch("app.tasks.ssl_checker.check_ssl_status_task.delay") as mock_task:
        # Trigger the SSL check
        response = client.post(f"/websites/{website.id}/ssl-checks", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "message": "SSL check initiated. Results will be available in logs."
        }
        # Assert the Celery task was called
        mock_task.assert_called_once_with(website.url, website.id)


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
def test_get_ssl_logs(client, test_db: Session, logged_in_user):
    user = logged_in_user["user"]
    headers = logged_in_user["headers"]

    # Add a website and SSL logs to the database
    website = Website(
        id=uuid4(), url="https://example.com", name="Example Website", user=user
    )
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
    response = client.get(f"/websites/{website.id}/ssl-logs?limit=2", headers=headers)
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
def test_get_ssl_logs_not_found(client, logged_in_user):
    headers = logged_in_user["headers"]
    non_existent_id = uuid4()
    response = client.get(
        f"/websites/{non_existent_id}/ssl-logs?limit=2", headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": f"Website with id {non_existent_id} not found"}


# Pagination and filtering tests
def test_get_ssl_logs_basic_pagination(client, test_ssl_logs, logged_in_user):
    headers = logged_in_user["headers"]
    website_id = test_ssl_logs[0].website_id
    response = client.get(f"/websites/{website_id}/ssl-logs?limit=2", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1
    assert data["data"][1]["id"] == 2
    assert data["next_cursor"] == 2


def test_get_ssl_logs_with_cursor(client, test_ssl_logs, logged_in_user):
    headers = logged_in_user["headers"]
    website_id = test_ssl_logs[0].website_id
    response = client.get(
        f"/websites/{website_id}/ssl-logs?limit=2&cursor=2", headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1  # Only 1 log left (id=3)
    assert data["data"][0]["id"] == 3
    assert data["next_cursor"] is None


def test_get_valid_logs_only(client, test_ssl_logs, logged_in_user):
    headers = logged_in_user["headers"]
    website_id = test_ssl_logs[0].website_id
    response = client.get(
        f"/websites/{website_id}/ssl-logs?limit=2&is_valid=true", headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1
    assert data["data"][1]["id"] == 3
    assert data["next_cursor"] is None  # Only 2 valid logs
    assert all(log["is_valid"] for log in data["data"])


def test_get_invalid_logs_only(client, test_ssl_logs, logged_in_user):
    headers = logged_in_user["headers"]
    website_id = test_ssl_logs[0].website_id
    response = client.get(
        f"/websites/{website_id}/ssl-logs?limit=2&is_valid=false", headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1  # Only 1 invalid log
    assert data["data"][0]["id"] == 2
    assert data["next_cursor"] is None
    assert all(not log["is_valid"] for log in data["data"])
