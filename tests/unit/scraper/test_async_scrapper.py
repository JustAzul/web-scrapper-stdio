from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import ScrapeArgs
from src.output_format_handler import OutputFormat
from src.scraper.async_scrapper import (
    AsyncScraper,
)


class TestAsyncScraper:
    @pytest.fixture
    def args(self):
        return ScrapeArgs(
            url="http://example.com",
            timeout_seconds=5,
            grace_period_seconds=1,
            output_format=OutputFormat.TEXT,
            max_length=None,
            user_agent=None,
            custom_elements_to_remove=None,
            custom_headers=None
        )

    @pytest.mark.asyncio
    @patch("src.scraper.async_scrapper.async_playwright")
    async def test_scrape_success(self, mock_playwright, args):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.goto.return_value.status = 200
        mock_page.content.return_value = "<html><body><div>Hello</div></body></html>"
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example"

        scraper = AsyncScraper()
        result = await scraper.scrape(args)
        assert result["error"] is None
        assert "Hello" in result["content"]

    @pytest.mark.asyncio
    @patch("src.scraper.async_scrapper.async_playwright")
    async def test_scrape_timeout_fallback(self, mock_playwright, args):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.goto.side_effect = Exception("Timeout error")

        scraper = AsyncScraper()
        # Fallback: requests scrape will be triggered, so we patch requests.get
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html><body><div>Fallback</div></body></html>"
            mock_resp.url = "http://example.com"
            mock_get.return_value = mock_resp
            result = await scraper.scrape(args)
            assert "Fallback mode (requests)" in result["error"]
            assert "Fallback" in result["content"]

    @pytest.mark.asyncio
    @patch("src.scraper.async_scrapper.async_playwright")
    async def test_scrape_http_error_no_fallback(self, mock_playwright, args):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.goto.return_value.status = 404
        mock_page.goto.return_value.status_text = "Not Found"

        scraper = AsyncScraper()
        # Fallback não deve ocorrer para HTTP error
        with patch("requests.get"):
            result = await scraper.scrape(args)
            assert isinstance(result["error"], str)
            assert "HTTP 404" in result["error"]

    @pytest.mark.asyncio
    @patch("src.scraper.async_scrapper.async_playwright")
    async def test_scrape_content_error_fallback(self, mock_playwright, args):
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.goto.return_value.status = 200
        mock_page.content.side_effect = Exception("Content extraction failed")

        scraper = AsyncScraper()
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html><body><div>Fallback2</div></body></html>"
            mock_resp.url = "http://example.com"
            mock_get.return_value = mock_resp
            result = await scraper.scrape(args)
            assert "Fallback mode (requests)" in result["error"]
            assert "Fallback2" in result["content"]

    def test_validate_args(self):
        scraper = AsyncScraper()
        # URL ausente
        args = MagicMock()
        args.url = None
        args.timeout_seconds = 5
        args.grace_period_seconds = 1
        assert scraper._validate_args(args) == "URL is required."
        # URL inválida
        args.url = "ftp://example.com"
        assert scraper._validate_args(args) == "URL must be a valid HTTP/HTTPS address."
        # Timeout inválido
        args.url = "http://example.com"
        args.timeout_seconds = 0
        assert scraper._validate_args(args) == "Timeout must be greater than zero."
        # Grace period negativo
        args.timeout_seconds = 5
        args.grace_period_seconds = -1
        assert scraper._validate_args(args) == "Grace period must be zero or positive."
        # Tudo válido
        args.grace_period_seconds = 1
        assert scraper._validate_args(args) is None
