import pytest
from src.scraper.scraper_utils import extract_clean_html

def test_extract_clean_html_returns_expected(monkeypatch):
    # Mock the centralized extractor for isolation
    class DummyExtractor:
        def extract_clean_html(self, html_content, url, config):
            return "Title", "<body>Clean</body>", "Clean text", None, object()
    monkeypatch.setattr(
        "src.scraper.infrastructure.web_scraping.html_extractor.get_centralized_extractor",
        lambda: DummyExtractor()
    )
    html = "<html><body><h1>Header</h1><p>Text</p></body></html>"
    elements_to_remove = ["h1"]
    url = "http://example.com"
    title, clean_html, text_content, error, soup = extract_clean_html(html, elements_to_remove, url)
    assert title == "Title"
    assert "<body>Clean</body>" == clean_html
    assert text_content == "Clean text"
    assert error is None
    assert soup is not None
