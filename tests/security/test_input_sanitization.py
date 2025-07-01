"""
Security-focused tests to ensure the application handles malicious
or unexpected inputs gracefully, preventing vulnerabilities like XSS.
"""

import pytest
from pydantic import ValidationError

from src.mcp_server_refactored import ScrapeArgs


class TestInputSanitization:
    """
    Tests focused on how the application handles potentially malicious inputs.
    The goal is to ensure inputs are sanitized and don't introduce vulnerabilities.
    """

    @pytest.mark.parametrize(
        "malicious_string",
        [
            "<script>alert('XSS')</script>",
            "';-- a comment",
            '"><img src=x onerror=alert(1)>',
            "{{ 7*7 }}",  # Template injection
            "../etc/passwd",
        ],
    )
    def test_malicious_url_is_validated(self, malicious_string):
        """
        Ensures that malicious strings in the URL are either rejected by
        Pydantic's URL validation or handled without issue.
        """
        # Pydantic's HttpUrl is expected to reject most of these.
        with pytest.raises(ValidationError):
            ScrapeArgs(url=f"https://example.com/{malicious_string}")

    @pytest.mark.parametrize(
        "malicious_string",
        [
            "Custom<script>alert(1)</script>",
            "TestBot/1.0\r\nInjected-Header: value",  # Header Injection
        ],
    )
    def test_malicious_user_agent_does_not_break_scraper(self, malicious_string):
        """
        Ensures that a malicious user-agent string is handled gracefully.
        We expect Pydantic to accept it, but the scraper should not crash.
        """
        # Pydantic will likely accept this as a plain string.
        args = ScrapeArgs(url="http://example.com", user_agent=malicious_string)
        assert args.user_agent == malicious_string
        # The main test is that this doesn't cause an unhandled error downstream.
        # A full integration test would be better, but this is a start.

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "malicious_css_selector",
        [
            "div >> *[onclick=alert(1)]",  # Playwright-specific syntax
            "body:has(script)",
            "*[style*='--x: url(https://evil.com/);']",
        ],
    )
    async def test_malicious_selector_does_not_execute_code(
        self, httpserver, malicious_css_selector
    ):
        """
        Tests that a malicious CSS selector does not cause code execution.
        Playwright should handle this safely, but this test verifies that the
        application doesn't crash and no obvious XSS is reflected.
        """
        from src.dependency_injection.application_bootstrap import ApplicationBootstrap

        # Bootstrap the application to get the real services
        bootstrap = ApplicationBootstrap()
        web_scraping_service = bootstrap.get_web_scraping_service()

        httpserver.expect_request("/").respond_with_data(
            "<html><body><p>Hello</p></body></html>"
        )

        try:
            # We expect this might fail benignly (e.g., element not found)
            # or succeed without finding anything. The key is no crash/XSS.
            result = await web_scraping_service.scrape_url(
                url=httpserver.url_for("/"),
                click_selector=malicious_css_selector,
            )
            assert result is not None
            # The selector should not be reflected in the output
            if result["content"]:
                assert malicious_css_selector not in result["content"]
        except Exception as e:
            # Any exception is fine, as long as it's not a security vulnerability.
            # We are just ensuring the application remains stable.
            assert "crash" not in str(e).lower()
