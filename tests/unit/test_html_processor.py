"""Unit tests for the HTML processing logic."""

import pytest

from src.scraper.application.services.content_processing_service import (
    ContentProcessingService,
)


@pytest.fixture
def content_processing_service():
    """Return a fresh ContentProcessingService instance for each test."""
    return ContentProcessingService()


class TestHtmlProcessor:
    """Group tests for the ContentProcessingService.process_html method."""

    def test_unwanted_tags_removed(self, content_processing_service):
        """Test that default unwanted tags are stripped from the HTML."""
        html = (
            "<html><head><title>A Title</title><style>.cls{}</style><script>console.log()</script></head>"
            "<body><nav>Menu</nav><main><p>Content</p></main><footer>Foot</footer></body></html>"
        )
        elements_to_remove = ["nav", "footer", "script", "style"]
        title, clean_html, text_content, error = (
            content_processing_service.process_html(
                html, elements_to_remove, "http://example.com"
            )
        )

        assert error is None
        assert title == "A Title"
        assert "Menu" not in text_content
        assert "Foot" not in text_content
        assert "console.log" not in text_content
        assert "Content" in text_content
        assert "<nav>" not in clean_html

    def test_empty_html_returns_empty_string(self, content_processing_service):
        """Test that empty HTML input results in empty outputs."""
        title, clean_html, text_content, error = (
            content_processing_service.process_html("", [], "http://example.com")
        )
        assert error is not None
        assert "Could not find body tag" in error
        assert title is None
        assert clean_html is None
        assert text_content is None

    def test_no_body_tag(self, content_processing_service):
        """Test that HTML without a body tag is handled gracefully."""
        html = "<html><head><title>Title Only</title></head></html>"
        title, clean_html, text_content, error = (
            content_processing_service.process_html(html, [], "http://example.com")
        )
        assert error is not None
        assert "Could not find body tag" in error
        assert title is None
        assert clean_html is None
        assert text_content is None

    def test_only_unwanted_tags_results_empty(self, content_processing_service):
        """Test that HTML with only unwanted tags results in empty content."""
        html = "<nav>Nav</nav><footer>Foot</footer>"
        title, clean_html, text_content, error = (
            content_processing_service.process_html(
                html, ["nav", "footer"], "http://example.com"
            )
        )
        assert error is not None
        assert "Could not find body tag" in error
        assert title is None
        assert clean_html is None
        assert text_content is None

    def test_spacing_between_elements(self, content_processing_service):
        """Test that spacing is correctly handled between block elements."""
        html = "<body><h1>H</h1><p>A</p><p>B</p></body>"
        title, clean_html, text_content, error = (
            content_processing_service.process_html(html, [], "http://example.com")
        )
        assert error is None
        assert text_content == "H\nA\nB"

    def test_malformed_html_handled(self, content_processing_service):
        """Test that malformed HTML is parsed leniently."""
        html = "<html><body><h1>Missing closes<p>X"
        title, clean_html, text_content, error = (
            content_processing_service.process_html(html, [], "http://example.com")
        )
        assert error is None
        assert "Missing closes" in text_content
        assert "X" in text_content

    def test_unicode_preserved(self, content_processing_service):
        """Test that Unicode characters are preserved correctly."""
        html = "<body><p>Olá, mundo! 😊</p></body>"
        title, clean_html, text_content, error = (
            content_processing_service.process_html(html, [], "http://example.com")
        )
        assert error is None
        assert text_content == "Olá, mundo! 😊"
