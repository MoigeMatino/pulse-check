import re
from urllib.parse import urlparse

import validators

from app.exceptions.ssl import InvalidURLException

WHITELISTED_TLDS = {"local", "internal", "dev", "test"}


def validate_url(url: str) -> str:
    """
    Validate a URL and return its domain or full URL for HTTP requests.

    Args:
        url: The URL to validate (e.g., "https://example.com").

    Returns:
        str: The validated domain or URL (e.g., "example.com" or "https://example.com").

    Raises:
        InvalidURLException: If the URL is invalid or lacks a domain.
    """
    if not validators.url(url):
        raise InvalidURLException("Invalid URL format")

    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path

    if not domain:
        raise InvalidURLException("Invalid URL: No domain found")

    # Validate TLD
    tld_match = re.search(r"\.([a-zA-Z]{2,})$", domain)
    if not tld_match:
        raise InvalidURLException("Invalid domain: Missing TLD (e.g., .com, .org)")

    if parsed_url.scheme not in ("http", "https"):
        raise InvalidURLException("URL must use http or https scheme")

    return domain
