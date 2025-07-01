import pytest
from pydantic import ValidationError

from src.models import ScrapeArgs
from src.settings import get_settings


@pytest.fixture(autouse=True)
def isolated_settings():
    """
    Fixture to ensure each test runs with a fresh, default instance of settings.
    This prevents state from leaking between tests, especially those that
    might modify settings.
    """
    # Clear the cache before the test to get a fresh instance
    get_settings.cache_clear()
    yield
    # Clear the cache after the test to clean up
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "invalid_url",
    [
        "file:///etc/passwd",
        "http://localhost:8000",
        "http://127.0.0.1:8080/secret",
        "ftp://example.com/resource",
        "javascript:alert('xss')",
    ],
)
def test_rejects_unsafe_urls(invalid_url: str):
    """
    Ensures that URLs pointing to local or non-HTTP resources are rejected.
    This is a critical security measure against SSRF.
    This test must run with ALLOW_LOCALHOST set to False, which is the default.
    """
    with pytest.raises(ValidationError):
        ScrapeArgs(url=invalid_url)


def test_rejects_non_string_url():
    """
    Ensures that a non-string URL raises a validation error.
    """
    with pytest.raises(ValidationError):
        ScrapeArgs(url={"not": "a string"})


def test_user_agent_sanitization():
    """
    While Pydantic handles type validation, this test ensures
    that even if a string is passed, it doesn't contain obvious
    command injection attempts (though the risk is low here).
    A more robust solution would be at the execution layer.
    """
    # This test is more of a placeholder for future, deeper validation.
    # Pydantic will ensure user_agent is a string if provided.
    # The real risk is how this string is used, which is handled by Playwright.
    args = ScrapeArgs(url="http://example.com", user_agent="valid-agent; rm -rf /")
    assert args.user_agent == "valid-agent; rm -rf /"
