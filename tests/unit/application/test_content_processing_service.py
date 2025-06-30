from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from src.output_format_handler import OutputFormat


class TestContentProcessingService:
    """Test suite for ContentProcessingService that handles content extraction and formatting"""

    @pytest.fixture
    def mock_chunked_processor(self):
        """Mock chunked HTML processor"""
        mock = Mock()
        mock.extract_clean_html_optimized = Mock()
        return mock

    def test_process_html_success(self, mock_chunked_processor):
        """Test successful HTML content processing"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        # Setup mock
        mock_chunked_processor.extract_clean_html_optimized.return_value = (
            "Test Title",
            "<div>Clean HTML</div>",
            "Clean text content",
            None,
            BeautifulSoup(
                "<html><body><div>Clean HTML</div></body></html>", "html.parser"
            ),
        )

        service = ContentProcessingService(chunked_processor=mock_chunked_processor)

        result = service.process_html(
            html_content="<html><body><div>Test content</div></body></html>",
            elements_to_remove=["script", "style"],
            url="https://example.com",
        )

        title, clean_html, text_content, error = result

        assert title == "Test Title"
        assert clean_html == "<div>Clean HTML</div>"
        assert text_content == "Clean text content"
        assert error is None

        mock_chunked_processor.extract_clean_html_optimized.assert_called_once_with(
            "<html><body><div>Test content</div></body></html>",
            ["script", "style"],
            "https://example.com",
        )

    def test_process_html_error_handling(self, mock_chunked_processor):
        """Test error handling in HTML content processing"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        # Setup error scenario
        mock_chunked_processor.extract_clean_html_optimized.return_value = (
            None,
            None,
            None,
            "Processing error",
            None,
        )

        service = ContentProcessingService(chunked_processor=mock_chunked_processor)

        result = service.process_html(
            html_content="<html><body>Test</body></html>",
            elements_to_remove=[],
            url="https://example.com",
        )

        title, clean_html, text_content, error = result

        assert title is None
        assert clean_html is None
        assert text_content is None
        assert error == "Processing error"

    def test_process_html_fallback_mechanism(self, mock_chunked_processor):
        """Test fallback mechanism when chunked processing fails"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        # Setup chunked processor to raise exception
        mock_chunked_processor.extract_clean_html_optimized.side_effect = Exception(
            "Chunked processing failed"
        )

        service = ContentProcessingService(chunked_processor=mock_chunked_processor)

        with patch(
            "src.scraper.application.services.content_processing_service._extract_and_clean_html"
        ) as mock_fallback:
            mock_soup = BeautifulSoup(
                "<html><head><title>Test Title</title></head><body>Test content</body></html>",
                "html.parser",
            )
            mock_fallback.return_value = (mock_soup, mock_soup.body)

            result = service.process_html(
                html_content="<html><head><title>Test Title</title></head><body>Test content</body></html>",
                elements_to_remove=[],
                url="https://example.com",
            )

            title, clean_html, text_content, error = result

            assert title == "Test Title"
            assert error is None
            mock_fallback.assert_called_once()

    def test_validate_content_length_sufficient(self):
        """Test content length validation when content is sufficient"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        # Content is long enough
        result = service.validate_content_length(
            text_content="This is a sufficiently long piece of content for validation",
            min_length=20,
            url="https://example.com",
        )

        assert result is True

    def test_validate_content_length_insufficient(self):
        """Test content length validation when content is too short"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        # Content is too short
        result = service.validate_content_length(
            text_content="Short", min_length=20, url="https://example.com"
        )

        assert result is False

    def test_validate_content_length_empty_content(self):
        """Test content length validation with empty content"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        result = service.validate_content_length(
            text_content="", min_length=10, url="https://example.com"
        )

        assert result is False

    def test_format_content_markdown(self):
        """Test content formatting to Markdown"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        with patch(
            "src.scraper.application.services.content_processing_service.to_markdown"
        ) as mock_to_markdown:
            mock_to_markdown.return_value = "# Test Title\n\nMarkdown content"

            result = service.format_content(
                title="Test Title",
                html_content="<div>HTML content</div>",
                text_content="Text content",
                output_format=OutputFormat.MARKDOWN,
            )

            assert result == "# Test Title\n\nMarkdown content"
            mock_to_markdown.assert_called_once_with("<div>HTML content</div>")

    def test_format_content_text(self):
        """Test content formatting to plain text"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        mock_soup = BeautifulSoup("<div>HTML content</div>", "html.parser")

        with patch(
            "src.scraper.application.services.content_processing_service.to_text"
        ) as mock_to_text:
            mock_to_text.return_value = "Plain text content"

            with patch(
                "src.scraper.application.services.content_processing_service.BeautifulSoup"
            ) as mock_bs:
                mock_bs.return_value = mock_soup

                result = service.format_content(
                    title="Test Title",
                    html_content="<div>HTML content</div>",
                    text_content="Text content",
                    output_format=OutputFormat.TEXT,
                )

                assert result == "Plain text content"
                mock_to_text.assert_called_once_with(soup=mock_soup)

    def test_format_content_html(self):
        """Test content formatting to HTML"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        mock_soup = BeautifulSoup(
            "<html><body><div>HTML content</div></body></html>", "html.parser"
        )

        with patch(
            "src.scraper.application.services.content_processing_service.BeautifulSoup"
        ) as mock_bs:
            mock_bs.return_value = mock_soup

            result = service.format_content(
                title="Test Title",
                html_content="<div>HTML content</div>",
                text_content="Text content",
                output_format=OutputFormat.HTML,
            )

            assert result == "<div>HTML content</div>"

    def test_format_content_html_fallback_when_no_body(self):
        """Test HTML formatting fallback when soup has no body"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        mock_soup = BeautifulSoup(
            "<div>HTML content</div>", "html.parser"
        )  # No body tag

        with patch(
            "src.scraper.application.services.content_processing_service.BeautifulSoup"
        ) as mock_bs:
            mock_bs.return_value = mock_soup

            result = service.format_content(
                title="Test Title",
                html_content="<div>HTML content</div>",
                text_content="Text content",
                output_format=OutputFormat.HTML,
            )

            # Should fallback to original clean_html
            assert result == "<div>HTML content</div>"

    def test_format_content_with_max_length(self):
        """Test content formatting with max length truncation"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        with patch(
            "src.scraper.application.services.content_processing_service.to_markdown"
        ) as mock_to_markdown:
            mock_to_markdown.return_value = (
                "Very long markdown content that should be truncated"
            )

            with patch(
                "src.scraper.application.services.content_processing_service.truncate_content"
            ) as mock_truncate:
                mock_truncate.return_value = "Very long"

                result = service.format_content(
                    title="Test Title",
                    html_content="<div>HTML content</div>",
                    text_content="Text content",
                    output_format=OutputFormat.MARKDOWN,
                    max_length=10,
                )

                assert result == "Very long"
                mock_truncate.assert_called_once_with(
                    "Very long markdown content that should be truncated", 10
                )

    def test_format_content_without_max_length(self):
        """Test content formatting without max length limit"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        with patch(
            "src.scraper.application.services.content_processing_service.to_markdown"
        ) as mock_to_markdown:
            mock_to_markdown.return_value = "Full markdown content"

            with patch(
                "src.scraper.application.services.content_processing_service.truncate_content"
            ) as mock_truncate:
                result = service.format_content(
                    title="Test Title",
                    html_content="<div>HTML content</div>",
                    text_content="Text content",
                    output_format=OutputFormat.MARKDOWN,
                    max_length=None,
                )

                assert result == "Full markdown content"
                mock_truncate.assert_not_called()

    def test_get_min_content_length_search_app_domain(self):
        """Test minimum content length calculation for search.app domains"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        with patch(
            "src.scraper.application.services.content_processing_service.get_domain_from_url"
        ) as mock_get_domain:
            mock_get_domain.return_value = "example.search.app"

            with patch(
                "src.scraper.application.services.content_processing_service.DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP",
                50,
            ):
                result = service.get_min_content_length(
                    "https://example.search.app/test"
                )

                assert result == 50

    def test_get_min_content_length_regular_domain(self):
        """Test minimum content length calculation for regular domains"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        with patch(
            "src.scraper.application.services.content_processing_service.get_domain_from_url"
        ) as mock_get_domain:
            mock_get_domain.return_value = "example.com"

            with patch(
                "src.scraper.application.services.content_processing_service.DEFAULT_MIN_CONTENT_LENGTH",
                100,
            ):
                result = service.get_min_content_length("https://example.com/test")

                assert result == 100

    def test_get_min_content_length_no_domain(self):
        """Test minimum content length when domain extraction fails"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        service = ContentProcessingService(chunked_processor=Mock())

        with patch(
            "src.scraper.application.services.content_processing_service.get_domain_from_url"
        ) as mock_get_domain:
            mock_get_domain.return_value = None

            with patch(
                "src.scraper.application.services.content_processing_service.DEFAULT_MIN_CONTENT_LENGTH",
                100,
            ):
                result = service.get_min_content_length("invalid-url")

                assert result == 100
