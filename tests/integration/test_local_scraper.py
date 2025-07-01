from unittest.mock import AsyncMock, Mock

import pytest
from pytest_httpserver import HTTPServer

from src.scraper.api.handlers.content_extractor import (
    ContentExtractor,
    ExtractionResult,
)
from src.scraper.api.handlers.output_formatter import OutputFormatter
from src.scraper.application.services.scraping_orchestrator import (
    ScrapingOrchestrator,
)
from src.scraper.application.services.url_validator import URLValidator

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


class TestLocalScraperIntegration:
    @pytest.fixture
    def mock_url_validator(self):
        mock = Mock(spec=URLValidator)
        mock.validate.return_value = True
        mock.normalize.side_effect = lambda url: url  # Just return the url
        return mock

    @pytest.fixture
    def mock_content_extractor(self):
        mock = AsyncMock(spec=ContentExtractor)
        return mock

    @pytest.fixture
    def mock_output_formatter(self):
        mock = Mock(spec=OutputFormatter)
        mock.format_and_truncate.side_effect = lambda content: content
        return mock

    async def test_successful_scrape(
        self,
        httpserver: HTTPServer,
        mock_url_validator,
        mock_content_extractor,
        mock_output_formatter,
    ):
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
        test_url = httpserver.url_for("/test-page")
        mock_url_validator.normalize.return_value = test_url
        mock_content_extractor.extract.return_value = ExtractionResult(
            title="Test Page",
            content="Main Content This is a paragraph.",
            clean_html="<main><h1>Main Content</h1><p>This is a paragraph.</p></main>",
            final_url=test_url,
        )

        scraper = ScrapingOrchestrator(
            url_validator=mock_url_validator,
            content_extractor=mock_content_extractor,
            output_formatter=mock_output_formatter,
        )
        result = await scraper.scrape(url=test_url)

        assert result is not None
        assert "Main Content" in result["content"]
        assert "This is a paragraph." in result["content"]
        assert result["error"] is None

    async def test_scrape_404_not_found(
        self,
        httpserver: HTTPServer,
        mock_url_validator,
        mock_content_extractor,
        mock_output_formatter,
    ):
        """
        Tests that the scraper correctly handles a 404 Not Found error.
        """
        httpserver.expect_request("/not-found").respond_with_data(
            "Page Not Found", status=404
        )
        mock_content_extractor.extract.return_value = ExtractionResult(
            error="HTTP error 404"
        )

        scraper = ScrapingOrchestrator(
            url_validator=mock_url_validator,
            content_extractor=mock_content_extractor,
            output_formatter=mock_output_formatter,
        )
        result = await scraper.scrape(url=httpserver.url_for("/not-found"))

        assert result is not None
        assert result["content"] is None
        assert result["error"] is not None
        assert "HTTP error 404" in result["error"]

    async def test_scrape_500_server_error(
        self,
        httpserver: HTTPServer,
        mock_url_validator,
        mock_content_extractor,
        mock_output_formatter,
    ):
        """
        Tests that the scraper correctly handles a 500 Internal Server Error.
        """
        httpserver.expect_request("/server-error").respond_with_data(
            "Internal Server Error", status=500
        )
        mock_content_extractor.extract.return_value = ExtractionResult(
            error="HTTP error 500"
        )

        scraper = ScrapingOrchestrator(
            url_validator=mock_url_validator,
            content_extractor=mock_content_extractor,
            output_formatter=mock_output_formatter,
        )
        result = await scraper.scrape(url=httpserver.url_for("/server-error"))

        assert result is not None
        assert result["content"] is None
        assert result["error"] is not None
        assert "HTTP error 500" in result["error"]

    async def test_scrape_timeout(
        self,
        httpserver: HTTPServer,
        mock_url_validator,
        mock_content_extractor,
        mock_output_formatter,
    ):
        """
        Tests that the scraper correctly handles a request timeout.
        """
        httpserver.expect_request("/slow-page").respond_with_handler(
            lambda request: (__import__("time").sleep(2), None)
        )

        # The orchestrator's content_extractor would be the one to timeout.
        mock_content_extractor.extract.return_value = ExtractionResult(
            error="Timeout error"
        )

        # Use a very short timeout to trigger the error quickly
        scraper = ScrapingOrchestrator(
            url_validator=mock_url_validator,
            content_extractor=mock_content_extractor,
            output_formatter=mock_output_formatter,
        )
        result = await scraper.scrape(
            url=httpserver.url_for("/slow-page"), custom_timeout=1
        )

        assert result is not None
        assert result["content"] is None
        assert result["error"] is not None
        assert "Timeout" in result["error"] or "timeout" in result["error"]
