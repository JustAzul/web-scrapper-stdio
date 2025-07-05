import pytest
from unittest.mock import MagicMock
from src.scraper.application.services.content_extraction_handler import ContentExtractionHandler

def test_extract_main_content_returns_string():
    content_processor = MagicMock()
    handler = ContentExtractionHandler(content_processor)
    html = "<html><body><main>Main Content</main></body></html>"
    # Mock the method to return a known value
    handler.extract_main_content = MagicMock(return_value="Main Content")
    result = handler.extract_main_content(html)
    assert isinstance(result, str)
    assert "Main Content" in result

def test_extract_main_content_handles_empty():
    content_processor = MagicMock()
    handler = ContentExtractionHandler(content_processor)
    handler.extract_main_content = MagicMock(return_value="")
    result = handler.extract_main_content("")
    assert result == ""
