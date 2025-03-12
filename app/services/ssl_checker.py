from datetime import datetime
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from typing import Dict, Optional
from urllib.parse import urlparse
from core.models import SSLLog
from sqlmodel import Session
from app.core.schemas import SSLStatusResponse
from app.exceptions import InvalidURLException
import validators
import logging

logger = logging.getLogger(__name__)

class SSLCheckerService:
    def __init__(self, warning_threshold_days: int = 30):
        """
        Initialize the SSL checker service.

        Args:
            warning_threshold_days (int): Number of days before expiry to trigger warnings.
        """
        self.warning_threshold_days = warning_threshold_days

    def check_ssl_status(
        self,
        url: str,
        website_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> SSLStatusResponse:
        """
        Check SSL certificate status for a given website or URL.

        Args:
            url (str): The URL to check.
            website_id (Optional[str]): The website ID (for database-driven checks).
            db (Optional[Session]): Database session (required for database-driven checks).

        Returns:
            SSLStatusResponse: SSL status information.
        """
        # Validate and extract domain from URL
        if not validators.url(url):
            raise InvalidURLException("Invalid URL format")
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or parsed_url.path
        if not domain:
            raise InvalidURLException("Invalid URL: No domain found")
        logger.info(f"Performing SSL check for {domain}")

        try:
            # Create SSL context
            context = ssl.create_default_context()

            # Establish a TCP connection
            with socket.create_connection((domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_binary = ssock.getpeercert(binary_form=True)
                    cert = x509.load_der_x509_certificate(
                        cert_binary, default_backend()
                    )

                    expiry_date = cert.not_valid_after
                    days_remaining = (expiry_date - datetime.now()).days
                    issuer = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value

                    # Log the SSL check result 
                    if website_id and db:
                        ssl_log = SSLLog(
                            website_id=website_id,
                            valid_until=expiry_date,
                            issuer=issuer,
                            is_valid=True,
                            error=None
                        )
                        db.add(ssl_log)
                        db.commit()

                    return {
                        'valid': True,
                        'expiry_date': expiry_date,
                        'days_remaining': days_remaining,
                        'issuer': issuer,
                        'needs_renewal': days_remaining <= self.warning_threshold_days,
                        'error': None
                    }

        except ssl.SSLError as e:
            logger.error(f"SSL error for {domain}: {e}")
            error_message = f"SSL error: {e}"
        except socket.timeout as e:
            logger.error(f"Connection timeout for {domain}: {e}")
            error_message = f"Connection timeout: {e}"
        except Exception as e:
            logger.error(f"Error checking SSL status for {domain}: {e}")
            error_message = str(e)

        # Log the failed SSL check
        if website_id and db:
            ssl_log = SSLLog(
                website_id=website_id,
                valid_until=None,
                issuer=None,
                is_valid=False,
                error=error_message
            )
            db.add(ssl_log)
            db.commit()

        return {
            'valid': False,
            'expiry_date': None,
            'days_remaining': None,
            'issuer': None,
            'needs_renewal': None,
            'error': error_message
        }

    def _handle_renewal_notification(self, website: Dict, ssl_status: Dict) -> None:
        """
        Handle SSL renewal notifications.

        Args:
            website (Dict): Website details.
            ssl_status (Dict): SSL status details.
        """
        message = (
            f"SSL Certificate for {website['url']} needs attention!\n"
            f"Days remaining: {ssl_status['days_remaining']}\n"
            f"Expiry date: {ssl_status['expiry_date']}\n"
            f"Issuer: {ssl_status['issuer']}"
        )
        logger.info(f"Sending notification for {website['url']}: {message}")
        # TODO: Integrate with NotificationService here
        # Example: NotificationService.send_notification(website['user_id'], message)