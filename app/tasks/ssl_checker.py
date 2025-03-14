from datetime import datetime
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from urllib.parse import urlparse
import validators
import logging
from celery import shared_task
from app.api.v1.models import SSLLog
from app.api.v1.schemas import SSLStatusResponse
from app.exceptions import InvalidURLException
from app.dependencies.db import SessionLocal

logger = logging.getLogger(__name__)

@shared_task
def check_ssl_status_task(url: str, website_id: str | None = None) -> SSLStatusResponse:
    """
    Celery task to check SSL certificate status for a given website or URL
    """
    try:
        # Validate and extract domain from URL
        if not validators.url(url):
            raise InvalidURLException("Invalid URL format")
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or parsed_url.path
        if not domain:
            raise InvalidURLException("Invalid URL: No domain found")

        # Create SSL context
        context = ssl.create_default_context()

        # Establish a TCP connection
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert_binary = ssock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(cert_binary, default_backend())

                expiry_date = cert.not_valid_after
                days_remaining = (expiry_date - datetime.now()).days
                issuer = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value

                result = {
                    'valid': True,
                    'expiry_date': expiry_date.isoformat(),
                    'days_remaining': days_remaining,
                    'issuer': issuer,
                    'needs_renewal': days_remaining <= 30,  # Example threshold
                    'error': None
                }

                # Log the result to the database (if website_id is provided)
                if website_id:
                    with SessionLocal() as db:
                        ssl_log = SSLLog(
                            website_id=website_id,
                            valid_until=expiry_date,
                            issuer=issuer,
                            is_valid=True,
                            error=None
                        )
                        db.add(ssl_log)
                        db.commit()

                return result

    except Exception as e:
        logger.error(f"Error checking SSL status for {url}: {e}")
        result = {
            'valid': False,
            'expiry_date': None,
            'days_remaining': None,
            'issuer': None,
            'needs_renewal': None,
            'error': str(e)
        }

        # Log the error to the database (if website_id is provided)
        if website_id:
            with SessionLocal() as db:
                ssl_log = SSLLog(
                    website_id=website_id,
                    valid_until=None,
                    issuer=None,
                    is_valid=False,
                    error=str(e)
                )
                db.add(ssl_log)
                db.commit()

        return result
