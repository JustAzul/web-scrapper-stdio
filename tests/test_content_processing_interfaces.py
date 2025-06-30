"""
TDD Tests for T012 - Content Processing Service Interface Implementation
Tests for implementing abstract interfaces to follow Dependency Inversion Principle (DIP)
"""

from unittest.mock import Mock

import pytest

from src.output_format_handler import OutputFormat


class TestIHTMLParser:
    """TDD Tests for IHTMLParser interface"""

    def test_html_parser_interface_creation(self):
        """Test creating IHTMLParser interface"""
        # This test will fail initially (RED phase)
        from src.scraper.application.contracts.html_parser import IHTMLParser

        # Interface should be abstract
        with pytest.raises(TypeError):
            IHTMLParser()

    def test_html_parser_interface_methods(self):
        """Test IHTMLParser interface has required methods"""
        from src.scraper.application.contracts.html_parser import IHTMLParser

        # Check interface has required abstract methods
        assert hasattr(IHTMLParser, "parse_html")
        assert hasattr(IHTMLParser, "extract_title")
        assert hasattr(IHTMLParser, "extract_text")
        assert hasattr(IHTMLParser, "remove_elements")

    def test_beautiful_soup_adapter_implementation(self):
        """Test BeautifulSoupAdapter implements IHTMLParser"""
        from src.scraper.application.contracts.html_parser import IHTMLParser
        from src.scraper.infrastructure.external.beautiful_soup_adapter import (
            BeautifulSoupAdapter,
        )

        adapter = BeautifulSoupAdapter()
        assert isinstance(adapter, IHTMLParser)

    def test_beautiful_soup_adapter_parse_html(self):
        """Test BeautifulSoupAdapter can parse HTML"""
        from src.scraper.infrastructure.external.beautiful_soup_adapter import (
            BeautifulSoupAdapter,
        )

        adapter = BeautifulSoupAdapter()
        html = (
            "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        )

        soup = adapter.parse_html(html)
        assert soup is not None
        assert soup.title.string == "Test"

    def test_beautiful_soup_adapter_extract_title(self):
        """Test BeautifulSoupAdapter can extract title"""
        from src.scraper.infrastructure.external.beautiful_soup_adapter import (
            BeautifulSoupAdapter,
        )

        adapter = BeautifulSoupAdapter()
        html = "<html><head><title>Test Page</title></head><body></body></html>"
        soup = adapter.parse_html(html)

        title = adapter.extract_title(soup)
        assert title == "Test Page"

    def test_beautiful_soup_adapter_extract_text(self):
        """Test BeautifulSoupAdapter can extract text content"""
        from src.scraper.infrastructure.external.beautiful_soup_adapter import (
            BeautifulSoupAdapter,
        )

        adapter = BeautifulSoupAdapter()
        html = "<html><body><p>Hello</p><p>World</p></body></html>"
        soup = adapter.parse_html(html)

        text = adapter.extract_text(soup.body)
        assert "Hello" in text
        assert "World" in text

    def test_beautiful_soup_adapter_remove_elements(self):
        """Test BeautifulSoupAdapter can remove elements"""
        from src.scraper.infrastructure.external.beautiful_soup_adapter import (
            BeautifulSoupAdapter,
        )

        adapter = BeautifulSoupAdapter()
        html = "<html><body><nav>Nav</nav><p>Content</p><script>alert()</script></body></html>"
        soup = adapter.parse_html(html)

        cleaned_soup = adapter.remove_elements(soup, ["nav", "script"])
        assert "Nav" not in str(cleaned_soup)
        assert "alert()" not in str(cleaned_soup)
        assert "Content" in str(cleaned_soup)


class TestIContentCleaner:
    """TDD Tests for IContentCleaner interface"""

    def test_content_cleaner_interface_creation(self):
        """Test creating IContentCleaner interface"""
        # This test will fail initially (RED phase)
        from src.scraper.application.contracts.content_cleaner import IContentCleaner

        # Interface should be abstract
        with pytest.raises(TypeError):
            IContentCleaner()

    def test_content_cleaner_interface_methods(self):
        """Test IContentCleaner interface has required methods"""
        from src.scraper.application.contracts.content_cleaner import IContentCleaner

        # Check interface has required abstract methods
        assert hasattr(IContentCleaner, "clean_html")
        assert hasattr(IContentCleaner, "extract_main_content")
        assert hasattr(IContentCleaner, "validate_content_length")

    def test_default_content_cleaner_implementation(self):
        """Test DefaultContentCleaner implements IContentCleaner"""
        from src.scraper.application.contracts.content_cleaner import IContentCleaner
        from src.scraper.infrastructure.external.default_content_cleaner import (
            DefaultContentCleaner,
        )

        cleaner = DefaultContentCleaner()
        assert isinstance(cleaner, IContentCleaner)

    def test_default_content_cleaner_clean_html(self):
        """Test DefaultContentCleaner can clean HTML"""
        from src.scraper.infrastructure.external.default_content_cleaner import (
            DefaultContentCleaner,
        )

        cleaner = DefaultContentCleaner()
        html = "<html><body><nav>Nav</nav><main>Content</main></body></html>"
        elements_to_remove = ["nav"]

        cleaned = cleaner.clean_html(html, elements_to_remove)
        assert "Nav" not in cleaned
        assert "Content" in cleaned

    def test_default_content_cleaner_extract_main_content(self):
        """Test DefaultContentCleaner can extract main content"""
        from src.scraper.infrastructure.external.default_content_cleaner import (
            DefaultContentCleaner,
        )

        cleaner = DefaultContentCleaner()
        html = "<html><body><header>Header</header><main>Main Content</main><footer>Footer</footer></body></html>"

        main_content = cleaner.extract_main_content(html)
        assert "Main Content" in main_content
        # Should prefer main content over other elements

    def test_default_content_cleaner_validate_content_length(self):
        """Test DefaultContentCleaner can validate content length"""
        from src.scraper.infrastructure.external.default_content_cleaner import (
            DefaultContentCleaner,
        )

        cleaner = DefaultContentCleaner()

        # Valid content
        assert cleaner.validate_content_length(
            "This is long enough content", 10, "https://example.com"
        )

        # Invalid content
        assert not cleaner.validate_content_length("Short", 10, "https://example.com")


class TestIContentFormatter:
    """TDD Tests for IContentFormatter interface"""

    def test_content_formatter_interface_creation(self):
        """Test creating IContentFormatter interface"""
        # This test will fail initially (RED phase)
        from src.scraper.application.contracts.content_formatter import (
            IContentFormatter,
        )

        # Interface should be abstract
        with pytest.raises(TypeError):
            IContentFormatter()

    def test_content_formatter_interface_methods(self):
        """Test IContentFormatter interface has required methods"""
        from src.scraper.application.contracts.content_formatter import (
            IContentFormatter,
        )

        # Check interface has required abstract methods
        assert hasattr(IContentFormatter, "format_to_markdown")
        assert hasattr(IContentFormatter, "format_to_text")
        assert hasattr(IContentFormatter, "format_to_html")
        assert hasattr(IContentFormatter, "truncate_content")

    def test_default_content_formatter_implementation(self):
        """Test DefaultContentFormatter implements IContentFormatter"""
        from src.scraper.application.contracts.content_formatter import (
            IContentFormatter,
        )
        from src.scraper.infrastructure.external.default_content_formatter import (
            DefaultContentFormatter,
        )

        formatter = DefaultContentFormatter()
        assert isinstance(formatter, IContentFormatter)

    def test_default_content_formatter_format_to_markdown(self):
        """Test DefaultContentFormatter can format to markdown"""
        from src.scraper.infrastructure.external.default_content_formatter import (
            DefaultContentFormatter,
        )

        formatter = DefaultContentFormatter()
        html = "<h1>Title</h1><p>Paragraph</p>"

        markdown = formatter.format_to_markdown(html)
        assert "Title" in markdown
        assert "Paragraph" in markdown

    def test_default_content_formatter_format_to_text(self):
        """Test DefaultContentFormatter can format to text"""
        from src.scraper.infrastructure.external.default_content_formatter import (
            DefaultContentFormatter,
        )

        formatter = DefaultContentFormatter()
        html = "<h1>Title</h1><p>Paragraph</p>"

        text = formatter.format_to_text(html)
        assert "Title" in text
        assert "Paragraph" in text
        assert "<h1>" not in text  # No HTML tags

    def test_default_content_formatter_format_to_html(self):
        """Test DefaultContentFormatter can format to clean HTML"""
        from src.scraper.infrastructure.external.default_content_formatter import (
            DefaultContentFormatter,
        )

        formatter = DefaultContentFormatter()
        html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>"

        clean_html = formatter.format_to_html(html)
        assert "<h1>Title</h1>" in clean_html
        assert "<p>Paragraph</p>" in clean_html

    def test_default_content_formatter_truncate_content(self):
        """Test DefaultContentFormatter can truncate content"""
        from src.scraper.infrastructure.external.default_content_formatter import (
            DefaultContentFormatter,
        )

        formatter = DefaultContentFormatter()
        content = "This is a very long content that should be truncated"

        truncated = formatter.truncate_content(content, 20)
        assert (
            "truncated" in truncated.lower() or len(truncated) <= 20
        )  # Should be truncated


class TestRefactoredContentProcessingService:
    """TDD Tests for refactored ContentProcessingService using DIP"""

    def test_refactored_service_creation_with_dependencies(self):
        """Test creating refactored service with injected dependencies"""
        from src.scraper.application.contracts.content_cleaner import IContentCleaner
        from src.scraper.application.contracts.content_formatter import (
            IContentFormatter,
        )
        from src.scraper.application.contracts.html_parser import IHTMLParser
        from src.scraper.application.services.refactored_content_processing_service import (
            RefactoredContentProcessingService,
        )

        # Mock dependencies
        html_parser = Mock(spec=IHTMLParser)
        content_cleaner = Mock(spec=IContentCleaner)
        content_formatter = Mock(spec=IContentFormatter)

        service = RefactoredContentProcessingService(
            html_parser=html_parser,
            content_cleaner=content_cleaner,
            content_formatter=content_formatter,
        )

        assert service.html_parser == html_parser
        assert service.content_cleaner == content_cleaner
        assert service.content_formatter == content_formatter

    def test_refactored_service_process_html_content(self):
        """Test refactored service can process HTML content using injected dependencies"""
        from src.scraper.application.contracts.content_cleaner import IContentCleaner
        from src.scraper.application.contracts.content_formatter import (
            IContentFormatter,
        )
        from src.scraper.application.contracts.html_parser import IHTMLParser
        from src.scraper.application.services.refactored_content_processing_service import (
            RefactoredContentProcessingService,
        )

        # Mock dependencies
        html_parser = Mock(spec=IHTMLParser)
        content_cleaner = Mock(spec=IContentCleaner)
        content_formatter = Mock(spec=IContentFormatter)

        # Configure mocks
        mock_soup = Mock()
        mock_soup.title.string = "Test Title"
        html_parser.parse_html.return_value = mock_soup
        html_parser.extract_title.return_value = "Test Title"
        content_cleaner.clean_html.return_value = "<p>Clean content</p>"
        html_parser.extract_text.return_value = "Clean content"

        service = RefactoredContentProcessingService(
            html_parser=html_parser,
            content_cleaner=content_cleaner,
            content_formatter=content_formatter,
        )

        result = service.process_html_content(
            "<html><body><p>Test</p></body></html>", ["nav"], "https://example.com"
        )

        # Verify dependencies were called
        assert (
            html_parser.parse_html.call_count == 2
        )  # Called for original and cleaned HTML
        content_cleaner.clean_html.assert_called_once()
        html_parser.extract_title.assert_called_once()
        html_parser.extract_text.assert_called_once()

        # Verify result structure
        title, clean_html, text_content, error = result
        assert title == "Test Title"
        assert error is None

    def test_refactored_service_format_content(self):
        """Test refactored service can format content using injected formatter"""
        from src.scraper.application.contracts.content_cleaner import IContentCleaner
        from src.scraper.application.contracts.content_formatter import (
            IContentFormatter,
        )
        from src.scraper.application.contracts.html_parser import IHTMLParser
        from src.scraper.application.services.refactored_content_processing_service import (
            RefactoredContentProcessingService,
        )

        # Mock dependencies
        html_parser = Mock(spec=IHTMLParser)
        content_cleaner = Mock(spec=IContentCleaner)
        content_formatter = Mock(spec=IContentFormatter)

        # Configure formatter mock
        content_formatter.format_to_markdown.return_value = "# Test\nContent"

        service = RefactoredContentProcessingService(
            html_parser=html_parser,
            content_cleaner=content_cleaner,
            content_formatter=content_formatter,
        )

        result = service.format_content(
            title="Test",
            html_content="<h1>Test</h1><p>Content</p>",
            text_content="Test\nContent",
            output_format=OutputFormat.MARKDOWN,
            max_length=None,
        )

        # Verify formatter was called
        content_formatter.format_to_markdown.assert_called_once()
        assert result == "# Test\nContent"


class TestBackwardCompatibility:
    """TDD Tests for maintaining backward compatibility"""

    def test_original_service_interface_maintained(self):
        """Test that original ContentProcessingService interface is maintained"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        # Original service should still work
        service = ContentProcessingService()

        # Check all original methods exist
        assert hasattr(service, "process_html_content")
        assert hasattr(service, "validate_content_length")
        assert hasattr(service, "get_min_content_length")
        assert hasattr(service, "format_content")

    def test_dependency_injection_integration(self):
        """Test that refactored service can be used as drop-in replacement"""
        from src.scraper.application.services.refactored_content_processing_service import (
            RefactoredContentProcessingService,
        )
        from src.scraper.infrastructure.external.beautiful_soup_adapter import (
            BeautifulSoupAdapter,
        )
        from src.scraper.infrastructure.external.default_content_cleaner import (
            DefaultContentCleaner,
        )
        from src.scraper.infrastructure.external.default_content_formatter import (
            DefaultContentFormatter,
        )

        # Create service with default implementations
        service = RefactoredContentProcessingService(
            html_parser=BeautifulSoupAdapter(),
            content_cleaner=DefaultContentCleaner(),
            content_formatter=DefaultContentFormatter(),
        )

        # Should have same interface as original
        assert hasattr(service, "process_html_content")
        assert hasattr(service, "validate_content_length")
        assert hasattr(service, "get_min_content_length")
        assert hasattr(service, "format_content")
