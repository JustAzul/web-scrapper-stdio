import pytest
from pytest_httpserver import HTTPServer

from src.scraper.application.services.scraping_orchestrator import (
    ScrapingOrchestrator,
)

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


class TestLocalScraperIntegration:
    async def test_successful_scrape(self, httpserver: HTTPServer):
        """
        Tests a successful scrape against a local HTTP server.
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <nav><a>Home</a></nav>
            <main>
                <h1>Main Content</h1>
                <p>This is a paragraph.</p>
            </main>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        httpserver.expect_request("/test-page").respond_with_data(
            html_content, content_type="text/html"
        )

        scraper = ScrapingOrchestrator()
        result = await scraper.scrape_url(url=httpserver.url_for("/test-page"))

        assert result is not None
        assert "Main Content" in result["content"]
        assert "This is a paragraph." in result["content"]
        assert "Home" not in result["content"]  # Should be removed by processor
        assert "Footer content" not in result["content"]  # Should be removed
        assert result["error"] is None

    async def test_scrape_404_not_found(self, httpserver: HTTPServer):
        """
        Tests that the scraper correctly handles a 404 Not Found error.
        """
        httpserver.expect_request("/not-found").respond_with_data(
            "Page Not Found", status=404
        )

        scraper = ScrapingOrchestrator()
        result = await scraper.scrape_url(url=httpserver.url_for("/not-found"))

        assert result is not None
        assert result["content"] is None
        assert result["error"] is not None
        assert "HTTP 404" in result["error"]

    async def test_scrape_500_server_error(self, httpserver: HTTPServer):
        """
        Tests that the scraper correctly handles a 500 Internal Server Error.
        """
        httpserver.expect_request("/server-error").respond_with_data(
            "Internal Server Error", status=500
        )

        scraper = ScrapingOrchestrator()
        result = await scraper.scrape_url(url=httpserver.url_for("/server-error"))

        assert result is not None
        assert result["content"] is None
        assert result["error"] is not None
        assert "HTTP 500" in result["error"]

    async def test_scrape_timeout(self, httpserver: HTTPServer):
        """
        Tests that the scraper correctly handles a request timeout.
        """
        httpserver.expect_request("/slow-page").respond_with_handler(
            lambda request: (__import__("time").sleep(2), None)
        )

        # Use a very short timeout to trigger the error quickly
        scraper = ScrapingOrchestrator()
        result = await scraper.scrape_url(
            url=httpserver.url_for("/slow-page"), custom_timeout=1
        )

        assert result is not None
        assert result["content"] is None
        assert result["error"] is not None
        assert "Timeout" in result["error"] or "timeout" in result["error"]
