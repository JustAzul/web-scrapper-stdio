import pytest
from pydantic import ValidationError
from src.models import ScrapeArgs, OutputFormat

def test_scrape_args_valid_url():
    args = ScrapeArgs(
        url="http://example.com",
        grace_period_seconds=2,
        timeout_seconds=10,
        output_format=OutputFormat.TEXT,
    )
    assert str(args.url) == "http://example.com/"

def test_scrape_args_invalid_url_malicious():
    with pytest.raises(ValidationError):
        ScrapeArgs(
            url="http://evil.com/<script>",
            grace_period_seconds=2,
            timeout_seconds=10,
            output_format=OutputFormat.TEXT,
        )

def test_scrape_args_invalid_url_traversal():
    with pytest.raises(ValidationError):
        ScrapeArgs(
            url="http://evil.com/../secret",
            grace_period_seconds=2,
            timeout_seconds=10,
            output_format=OutputFormat.TEXT,
        )

def test_scrape_args_invalid_url_local(monkeypatch):
    # Patch settings to disallow localhost
    from src import models
    monkeypatch.setattr(models, "get_settings", lambda: type("S", (), {"allow_localhost": False})())
    with pytest.raises(ValidationError):
        ScrapeArgs(
            url="http://localhost",
            grace_period_seconds=2,
            timeout_seconds=10,
            output_format=OutputFormat.TEXT,
        )

def test_scrape_args_valid_with_all_fields():
    args = ScrapeArgs(
        url="http://example.com",
        grace_period_seconds=2,
        timeout_seconds=10,
        output_format=OutputFormat.MARKDOWN,
        max_length=1000,
        user_agent="TestAgent",
        include_links=True,
        custom_headers={"X-Test": "1"},
        selector="body",
        custom_elements_to_remove=[".ads"],
    )
    assert args.max_length == 1000
    assert args.user_agent == "TestAgent"
    assert args.include_links is True
    assert args.selector == "body"
    assert args.custom_elements_to_remove == [".ads"]
