import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.scraper.async_scrapper import AsyncScraper
from src.models import ScrapeArgs, OutputFormat

@pytest.fixture
def args():
    return ScrapeArgs(
        url="http://example.com",
        timeout_seconds=5,
        grace_period_seconds=1,
        output_format=OutputFormat.TEXT,
    )

@pytest.mark.asyncio
@patch("src.scraper.async_scrapper.async_playwright")
async def test_scrape_success(mock_playwright, args):
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
async def test_scrape_timeout_fallback(mock_playwright, args):
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page
    mock_page.goto.side_effect = Exception("Timeout error")

    scraper = AsyncScraper()
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = (
            "<html><body><div>Fallback Improved</div></body></html>"
        )
        mock_resp.url = "http://example.com"
        mock_get.return_value = mock_resp
        result = await scraper.scrape(args)
        assert "Fallback mode (requests)" in result["error"]
        assert "Fallback Improved" in result["content"]

@pytest.mark.asyncio
@patch("src.scraper.async_scrapper.async_playwright")
async def test_scrape_http_error_no_fallback(mock_playwright, args):
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page
    mock_page.goto.return_value.status = 404
    mock_page.goto.return_value.status_text = "Not Found"

    scraper = AsyncScraper()
    with patch("requests.get"):
        result = await scraper.scrape(args)
        assert isinstance(result["error"], str)
        assert "HTTP 404" in result["error"]

@pytest.mark.asyncio
@patch("src.scraper.async_scrapper.async_playwright")
async def test_scrape_content_error_fallback(mock_playwright, args):
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
        mock_resp.text = (
            "<html><body><div>Fallback2</div></body></html>"
        )
        mock_resp.url = "http://example.com"
        mock_get.return_value = mock_resp
        result = await scraper.scrape(args)
        assert "Fallback mode (requests)" in result["error"]
        assert "Fallback2" in result["content"]

@pytest.mark.asyncio
@patch("src.scraper.async_scrapper.async_playwright")
async def test_scrape_http_error_with_edge_cases(mock_playwright, args):
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    mock_playwright().__aenter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page
    mock_page.goto.return_value.status = 500
    mock_page.goto.return_value.status_text = "Internal Server Error"

    scraper = AsyncScraper()
    with patch("requests.get"):
        result = await scraper.scrape(args)
        assert isinstance(result["error"], str)
        assert "HTTP 500" in result["error"]
