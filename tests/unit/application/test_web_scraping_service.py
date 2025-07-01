from dataclasses import dataclass
from typing import Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.output_format_handler import OutputFormat


@dataclass
class MockScrapingResult:
    """Mock result object for testing"""

    title: Optional[str]
    final_url: str
    content: Optional[str]
    error: Optional[str]


class TestWebScrapingService:
    """Test suite for WebScrapingService that orchestrates the web scraping process"""

    @pytest.fixture
    def mock_content_processor(self):
        """Mock content processing service"""
        mock = Mock()
        mock.process_html = Mock()
        mock.format_content = Mock()
        mock.validate_content_length = Mock()
        mock.get_min_content_length = Mock(return_value=10)
        return mock

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock ScrapingOrchestrator"""
        mock = AsyncMock()
        # Configure a mock scrape_url to return a successful result
        mock.scrape_url.return_value = Mock(
            success=True,
            content="<html><body>Test content</body></html>",
            error=None,
            final_url="https://example.com",
        )
        return mock

    @patch("src.scraper.application.services.web_scraping_service.apply_rate_limiting")
    @pytest.mark.asyncio
    async def test_successful_scraping_workflow(
        self,
        mock_rate_limiting,
        mock_content_processor,
        mock_orchestrator,
    ):
        """Test successful end-to-end scraping workflow"""
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        mock_rate_limiting.return_value = None
        mock_content_processor.process_html.return_value = (
            "Test Title",
            "Clean HTML",
            "Test content",
            None,
        )
        mock_content_processor.format_content.return_value = (
            "# Test Title\n\nTest content"
        )

        service = WebScrapingService(
            content_processor=mock_content_processor,
            orchestrator=mock_orchestrator,
        )

        result = await service.scrape_url(
            url="https://example.com",
            output_format=OutputFormat.MARKDOWN,
            custom_timeout=30,
        )

        assert result["title"] == "Test Title"
        assert result["final_url"] == "https://example.com"
        assert result["content"] == "# Test Title\n\nTest content"
        assert result["error"] is None
        mock_orchestrator.scrape_url.assert_called_once()
        mock_content_processor.process_html.assert_called_once()
        mock_content_processor.format_content.assert_called_once()

    @patch("src.scraper.application.services.web_scraping_service.apply_rate_limiting")
    @pytest.mark.asyncio
    async def test_navigation_error_handling(
        self,
        mock_rate_limiting,
        mock_content_processor,
        mock_orchestrator,
    ):
        """Test handling of navigation errors"""
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        mock_rate_limiting.return_value = None
        mock_orchestrator.scrape_url.return_value = Mock(
            success=False,
            content=None,
            error="Navigation failed",
            final_url="https://invalid.com",
        )

        service = WebScrapingService(
            content_processor=mock_content_processor,
            orchestrator=mock_orchestrator,
        )

        result = await service.scrape_url(url="https://invalid.com")

        assert result["error"] == "Navigation failed"
        assert result["content"] is None
        assert result["title"] is None
        mock_content_processor.process_html.assert_not_called()

    @patch("src.scraper.application.services.web_scraping_service.apply_rate_limiting")
    @pytest.mark.asyncio
    async def test_content_processing_error_handling(
        self,
        mock_rate_limiting,
        mock_content_processor,
        mock_orchestrator,
    ):
        """Test handling of content processing errors"""
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        mock_rate_limiting.return_value = None
        mock_orchestrator.scrape_url.return_value = Mock(
            success=True,
            content="<html><body>Test</body></html>",
            error=None,
            final_url="https://example.com",
        )
        mock_content_processor.process_html.return_value = (
            None,
            None,
            None,
            "Content processing failed",
        )

        service = WebScrapingService(
            content_processor=mock_content_processor,
            orchestrator=mock_orchestrator,
        )

        result = await service.scrape_url(url="https://example.com")

        assert result["error"] == "Content processing failed"
        assert result["content"] is None

    @patch("src.scraper.application.services.web_scraping_service.apply_rate_limiting")
    @pytest.mark.asyncio
    async def test_content_too_short_validation(
        self,
        mock_rate_limiting,
        mock_content_processor,
        mock_orchestrator,
    ):
        """Test validation when content is too short"""
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        mock_rate_limiting.return_value = None
        mock_orchestrator.scrape_url.return_value = Mock(
            success=True,
            content="<html><body>Hi</body></html>",
            error=None,
            final_url="https://example.com",
        )
        mock_content_processor.process_html.return_value = (
            None,
            None,
            None,
            "Content is too short",
        )

        service = WebScrapingService(
            content_processor=mock_content_processor,
            orchestrator=mock_orchestrator,
        )

        result = await service.scrape_url(url="https://example.com")

        assert "too short" in result["error"]
        assert result["content"] is None

    @patch("src.scraper.application.services.web_scraping_service.apply_rate_limiting")
    @pytest.mark.asyncio
    async def test_final_url_normalization_from_browser_response(
        self,
        mock_rate_limiting,
        mock_content_processor,
        mock_orchestrator,
    ):
        """Test that the final_url from the browser response is used."""
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        mock_rate_limiting.return_value = None
        mock_orchestrator.scrape_url.return_value = Mock(
            success=True,
            final_url="https://final-url.com",
            content="Content",
            error=None,
        )
        mock_content_processor.process_html.return_value = (
            "Title",
            "Content",
            "Content",
            None,
        )
        service = WebScrapingService(
            content_processor=mock_content_processor,
            orchestrator=mock_orchestrator,
        )
        result = await service.scrape_url(url="https://example.com/", custom_timeout=10)
        assert result["final_url"] == "https://final-url.com"
        assert result["title"] == "Title"
        assert result["error"] is None
        mock_content_processor.process_html.assert_called_once_with(
            "Content", [], "https://final-url.com"
        )
