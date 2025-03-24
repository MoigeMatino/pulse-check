from fastapi import status
from sqlmodel import Session
from datetime import datetime

from app.api.v1.schemas import SSLStatusResponse, SSLLogResponse
from app.api.v1.models import Website, SSLLog

# Test the /websites/{website_id}/check-ssl endpoint
def test_check_website_ssl(client, session: Session, user_with_notification_preference):
    
    user, _ = user_with_notification_preference
    # Add a website to the database
    website = Website(url="https://example.com", name="Example Website", user=user)
    session.add(website)
    session.commit()

    # Trigger the SSL check
    response = client.post(f"/websites/{website.id}/check-ssl")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "SSL check initiated. Results will be available in logs."}
    
# Test the /check-ssl endpoint
def test_check_ssl(client):
    # Perform an ad-hoc SSL check
    response = client.get("/check-ssl", params={"url": "https://example.com"})
    assert response.status_code == status.HTTP_200_OK

    # Validate the response schema
    ssl_status = SSLStatusResponse(**response.json())
    assert isinstance(ssl_status, SSLStatusResponse)
    assert ssl_status.valid
    

# Test the /websites/{website_id}/ssl-logs endpoint
def test_get_ssl_logs(client, session: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference

    # Add a website and SSL logs to the database
    website = Website(url="https://example.com", name="Example Website", user=user)
    session.add(website)
    session.commit()

    ssl_log = SSLLog(
        website_id=website.id,
        valid_until=datetime(2025, 1, 1, 0, 0, 0),
        issuer="Example Issuer",
        is_valid=True,
        error=None,
    )
    session.add(ssl_log)
    session.commit()

    # Retrieve SSL logs
    response = client.get(f"/websites/{website.id}/ssl-logs")
    assert response.status_code == status.HTTP_200_OK

    # Validate the response schema
    logs = [SSLLogResponse(**log) for log in response.json()]
    assert isinstance(logs, list)
    assert len(logs) == 1
    assert logs[0].website_id == website.id
    

# Test the /websites/{website_id}/ssl-logs endpoint for a non-existent website
def test_get_ssl_logs_not_found(client):
    response = client.get("/websites/999/ssl-logs")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "SSL logs not found for this website"}    
    
def test_get_valid_logs_only(client, test_logs):
    # Test filtering only valid logs
    response = client.get("/websites/1/ssl-logs?is_valid=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_invalid_logs_only(client, test_logs):
    # Test filtering only valid logs
    response = client.get("/websites/1/ssl-logs?is_valid=false")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1