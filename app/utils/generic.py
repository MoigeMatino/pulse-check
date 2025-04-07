from urllib.parse import urlparse

import validators
from exceptions.ssl import InvalidURLException


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

    if parsed_url.scheme not in ("http", "https"):
        raise InvalidURLException("URL must use http or https scheme")

    return domain
