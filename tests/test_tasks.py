from fastapi import status
from sqlmodel import Session

from app.api.v1.models import Website


def test_check_website_ssl(client, test_db: Session, logged_in_user, mocker):
    # Mock the Celery task
    mock_task = mocker.patch("app.tasks.ssl_checker.check_ssl_status_task.delay")

    user = logged_in_user["user"]
    headers = logged_in_user["headers"]

    # Add a website to the database
    website = Website(url="https://example.com", name="Example Website", user=user)
    test_db.add(website)
    test_db.commit()

    # Trigger the SSL check
    response = client.post(f"/websites/{website.id}/ssl-checks", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "SSL check initiated. Results will be available in logs."
    }

    # Verify the Celery task was called
    mock_task.assert_called_once_with(website.url, website.id)
