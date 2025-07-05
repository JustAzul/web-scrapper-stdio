import pytest
from unittest.mock import MagicMock
from src.scraper.application.services.content_processor import RefactoredContentProcessingService

@pytest.fixture
def processor():
    html_parser = MagicMock()
    content_cleaner = MagicMock()
    content_formatter = MagicMock()
    # Setup minimal mock behavior
    html_parser.parse_html.return_value = "soup"
    html_parser.extract_title.return_value = "Title"
    html_parser.extract_text.return_value = "Text"
    content_cleaner.clean_html.return_value = "<body>Clean</body>"
    content_cleaner.validate_content_length.return_value = True
    content_formatter.format_to_text.return_value = "Text"
    content_formatter.format_to_html.return_value = "<body>Clean</body>"
    content_formatter.format_to_markdown.return_value = "# Title\nText"
    content_formatter.truncate_content.side_effect = lambda x, y: x[:y]
    return RefactoredContentProcessingService(html_parser, content_cleaner, content_formatter)

def test_process_html_content_success(processor):
    title, clean_html, text_content, error = processor.process_html_content(
        "<html><body>Test</body></html>", ["h1"], "http://example.com"
    )
    assert title == "Title"
    assert clean_html == "<body>Clean</body>"
    assert text_content == "Text"
    assert error is None

def test_format_content_text(processor):
    result = processor.format_content("Title", "<body>Clean</body>", "Text", output_format=1)
    assert "Text" in result
