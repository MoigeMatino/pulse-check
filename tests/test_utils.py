from app.exceptions.ssl import InvalidURLException
from app.utils.generic import validate_url


def test_validate_url_success():
    url = "https://example.com"
    expected_domain = "example.com"
    result = validate_url(url)
    assert result == expected_domain


def test_validate_url_invalid_format():
    url = "invalid_url"
    try:
        validate_url(url)
    except Exception as e:
        assert isinstance(e, InvalidURLException)
        assert str(e) == "Invalid URL format"


def test_validate_url_invalid_tld():
    url = "https://example.invalidtld"
    try:
        validate_url(url)
    except Exception as e:
        assert isinstance(e, InvalidURLException)
        assert str(e) == "Invalid domain: Missing TLD (e.g., .com, .org)"


def test_validate_url_invalid_scheme():
    url = "ftp://example.com"
    try:
        validate_url(url)
    except Exception as e:
        assert isinstance(e, InvalidURLException)
        assert str(e) == "URL must use http or https scheme"
