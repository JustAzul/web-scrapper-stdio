import pytest


def test_url_validator_initialization():
    """
    Tests that the URLValidator can be initialized.
    """
    from src.scraper.application.services.url_validator import URLValidator

    validator = URLValidator()
    assert validator is not None


@pytest.mark.parametrize(
    "valid_url",
    [
        "http://example.com",
        "https://example.com",
        "https://www.example.com/path?query=value",
        "https://127.0.0.1:8080",
        "http://localhost",
    ],
)
def test_url_validator_validate_success(valid_url):
    """
    Tests that the validate method returns True for valid URLs.
    """
    from src.scraper.application.services.url_validator import URLValidator

    validator = URLValidator()
    assert validator.validate(valid_url) is True


@pytest.mark.parametrize(
    "invalid_url",
    [
        "file:///etc/passwd",
        "javascript:alert('xss')",
        "ftp://example.com",
        "not-a-url",
    ],
)
def test_url_validator_validate_failure(invalid_url):
    """
    Tests that the validate method returns False for invalid or unsafe URLs.
    """
    from src.scraper.application.services.url_validator import URLValidator

    validator = URLValidator()
    assert validator.validate(invalid_url) is False
