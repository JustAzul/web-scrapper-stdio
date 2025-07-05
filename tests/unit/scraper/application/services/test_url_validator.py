import pytest
from src.scraper.application.services.url_validator import URLValidator

def test_valid_url():
    validator = URLValidator()
    assert validator.validate("http://example.com")
    assert validator.validate("https://example.com")

def test_invalid_url():
    validator = URLValidator()
    assert not validator.validate("ftp://example.com")
    assert not validator.validate("not-a-url")
    assert not validator.validate("")
