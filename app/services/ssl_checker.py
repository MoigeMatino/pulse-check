from datetime import datetime
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from typing import Dict
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

    async def check_ssl_status(self, url: str) -> Dict:
        """
        Check SSL certificate status for a single url.

        Args:
            url (str): The url to check.

        Returns:
            Dict: Contains SSL certificate details or error information.
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()
            with socket.create_connection((url, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=url) as ssock:
                    cert_binary = ssock.getpeercert(binary_form=True)
                    cert = x509.load_der_x509_certificate(
                        cert_binary, default_backend()
                    )

                    expiry_date = cert.not_valid_after
                    days_remaining = (expiry_date - datetime.now()).days
                    issuer = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value

                    return {
                        'valid': True,
                        'expiry_date': expiry_date,
                        'days_remaining': days_remaining,
                        'issuer': issuer,
                        'needs_renewal': days_remaining <= self.warning_threshold_days,
                        'error': None
                    }

        except Exception as e:
            logger.error(f"Error checking SSL status for {url}: {e}")
            return {
                #TODO: consider appropriate values for rhe return dict
                'valid': False,
                'expiry_date': None,
                'days_remaining': None,
                'issuer': None,
                'needs_renewal': None,
                'error': str(e)
            }

    # TODO: reconsider website type from Dict to a pydantic schema
    async def _handle_renewal_notification(self, website: Dict, ssl_status: Dict) -> None:
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
        # something like await NotificationService.send_notification(website['user_id'], message)