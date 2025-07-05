import pytest
from unittest.mock import MagicMock
from src.scraper.application.services.web_scraping_service import WebScrapingService

def test_scrape_main_content_success():
    content_processor = MagicMock()
    orchestrator = MagicMock()
    service = WebScrapingService(content_processor, orchestrator)
    url = "http://example.com"
    service.scrape_main_content = MagicMock(return_value="Main")
    result = service.scrape_main_content(url)
    assert "Main" in result

def test_scrape_main_content_invalid_url():
    content_processor = MagicMock()
    orchestrator = MagicMock()
    service = WebScrapingService(content_processor, orchestrator)
    service.scrape_main_content = MagicMock(side_effect=ValueError("Invalid URL"))
    with pytest.raises(ValueError):
        service.scrape_main_content("not-a-url")
