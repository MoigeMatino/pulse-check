from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.api.v1.models import SSLLog, UptimeLog, User, Website
from app.auth import get_password_hash
from app.tasks.ssl_checker import check_ssl_status_task
from app.tasks.uptime_monitor import check_website_uptime


def test_check_ssl_status_task_success(test_db: Session):
    # Mock validate_url to just return the domain
    with patch("app.tasks.ssl_checker.validate_url", return_value="example.com"), patch(
        "app.tasks.ssl_checker.socket.create_connection"
    ) as mock_conn, patch(
        "app.tasks.ssl_checker.ssl.create_default_context"
    ) as mock_ctx, patch(
        "app.tasks.ssl_checker.x509.load_der_x509_certificate"
    ) as mock_cert:
        # Mock the SSL certificate object
        mock_cert_obj = MagicMock()
        mock_cert_obj.not_valid_after = datetime.now() + timedelta(days=90)
        mock_cert_obj.issuer.get_attributes_for_oid.return_value = [
            MagicMock(value="TestIssuer")
        ]
        mock_cert.return_value = mock_cert_obj

        # Mock context and socket
        mock_sock = MagicMock()
        mock_ctx.return_value.wrap_socket.return_value.__enter__.return_value.getpeercert.return_value = (  # noqa: E501
            b"cert"
        )
        mock_conn.return_value.__enter__.return_value = mock_sock

        website_id = "test-website-id"
        result = check_ssl_status_task.run("https://example.com", website_id)

        assert result["valid"] is True
        assert result["error"] is None
        assert result["issuer"] == "TestIssuer"
        assert isinstance(result["days_remaining"], int)

        # Check that an SSLLog was created
        ssl_log = test_db.exec(select(SSLLog).filter_by(website_id=website_id)).first()
        assert ssl_log is not None
        assert ssl_log.is_valid is True
        assert ssl_log.error is None


def test_check_ssl_status_task_failure(test_db: Session):
    with patch(
        "app.tasks.ssl_checker.validate_url",
        side_effect=Exception("Invalid URL format"),
    ):
        website_id = "test-website-id"
        result = check_ssl_status_task.run("invalid-url", website_id)
        assert result["valid"] is False
        assert result["error"] == "Invalid URL format"

        # Check that an SSLLog was created with error
        ssl_log = test_db.query(SSLLog).filter_by(website_id=website_id).first()
        assert ssl_log is not None
        assert ssl_log.is_valid is False
        assert ssl_log.error == "Invalid URL"


def test_check_website_uptime(client: TestClient, test_db: Session):
    user = User(
        id=uuid4(),
        email=f"test{uuid4()}@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    website = Website(
        id=uuid4(),
        user_id=user.id,
        url="https://example.com",
        is_active=True,
    )
    test_db.add_all([user, website])
    test_db.commit()

    # Test HTTP check
    result = check_website_uptime.run(str(website.id), website.url, "http")
    assert result["website_id"] == str(website.id)
    assert result["is_up"] is True

    # Test ping check
    # result = check_website_uptime.run(str(website.id), website.url, "ping")
    # assert result["website_id"] == str(website.id)

    # Test invalid website_id
    result = check_website_uptime.run("invalid-uuid", website.url, "http")
    assert result["error"] == "Invalid website_id"

    # Test retry with jitter
    with patch("random.uniform", return_value=45.0):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException):
            try:
                check_website_uptime.run(str(website.id), website.url, "http")
            except check_website_uptime.MaxRetriesExceededError:
                pass  # Expected retry failure

    # Verify UptimeLog
    log = test_db.exec(
        select(UptimeLog).where(UptimeLog.website_id == website.id)
    ).first()
    assert log is not None
