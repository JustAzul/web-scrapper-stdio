from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from src.scraper.infrastructure.external.chunked_processor import ChunkedHTMLProcessor
from src.scraper.infrastructure.external.html_utils import _extract_and_clean_html


class TestChunkedHTMLProcessor:
    """Test-Driven Development tests for chunked HTML processing."""

    @pytest.fixture
    def small_html(self):
        """Small HTML document that should use original processing."""
        return """
        <html>
            <head><title>Small Page</title></head>
            <body>
                <h1>Test Content</h1>
                <p>This is a small page that should not trigger chunked processing.</p>
                <script>alert('test');</script>
                <style>.test { color: red; }</style>
            </body>
        </html>
        """

    @pytest.fixture
    def large_html(self):
        """Large HTML document that should trigger chunked processing."""
        content_blocks = []
        for i in range(100):  # Reduced from 500 to 100 articles for faster tests
            content_blocks.append(f"""
                <article class="content-block">
                    <h2>Article {i}</h2>
                    <p>{"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20}</p>
                    <div class="metadata">
                        <span class="author">Author {i}</span>
                        <span class="date">2024-01-{i:02d}</span>
                    </div>
                    <div class="comments">
                        {'<div class="comment">User comment here...</div>' * 5}
                    </div>
                </article>
            """)

        return f"""
        <html>
            <head>
                <title>Large Page with Many Articles</title>
                <script>{"// Large script block " + "x" * 2000}</script>
                <style>{"/* Large CSS block */ " + "a" * 2000}</style>
            </head>
            <body>
                <nav>Navigation that should be removed</nav>
                <header>Header that should be removed</header>
                <main class="content">
                    {"".join(content_blocks)}
                </main>
                <aside>Sidebar that should be removed</aside>
                <footer>Footer that should be removed</footer>
                <script>alert('Should be removed');</script>
            </body>
        </html>
        """

    @pytest.fixture
    def malformed_html(self):
        """Malformed HTML to test error handling."""
        return """
        <html>
            <head><title>Malformed</title>
            <body>
                <div>Unclosed div
                <p>Missing closing tag
                <article>Content here
        """

    def test_processor_initialization(self):
        """Test that ChunkedHTMLProcessor initializes with correct defaults."""
        processor = ChunkedHTMLProcessor()

        assert processor.chunk_size_threshold == 100000  # 100KB default
        assert processor.memory_monitor.memory_limit_mb == 150  # Updated default
        assert processor.enable_chunking is True
        assert processor.fallback_enabled is True

    def test_processor_custom_configuration(self):
        """Test ChunkedHTMLProcessor with custom configuration."""
        processor = ChunkedHTMLProcessor(
            chunk_size_threshold=50000, memory_limit_mb=100, enable_chunking=False
        )

        assert processor.chunk_size_threshold == 50000
        assert processor.memory_monitor.memory_limit_mb == 100
        assert processor.enable_chunking is False

    def test_should_use_chunked_processing_small_content(self, small_html):
        """Test that small content does not trigger chunked processing."""
        processor = ChunkedHTMLProcessor()

        should_chunk = processor._should_use_chunked_processing(small_html)

        assert should_chunk is False

    def test_should_use_chunked_processing_large_content(self, large_html):
        """Test that large content triggers chunked processing."""
        processor = ChunkedHTMLProcessor()

        should_chunk = processor._should_use_chunked_processing(large_html)

        assert should_chunk is True

    def test_should_use_chunked_processing_disabled(self, large_html):
        """Test that chunked processing can be disabled."""
        processor = ChunkedHTMLProcessor(enable_chunking=False)

        should_chunk = processor._should_use_chunked_processing(large_html)

        assert should_chunk is False

    def test_extract_content_small_html_backward_compatibility(self, small_html):
        """Test that small HTML processing maintains backward compatibility."""
        processor = ChunkedHTMLProcessor()
        elements_to_remove = ["script", "style", "nav", "footer"]

        # Should return same format as original function
        title, clean_html, text_content, error, soup = processor.extract_content(
            small_html, elements_to_remove, "http://test.com"
        )

        assert title == "Small Page"
        assert error is None
        assert "Test Content" in text_content
        assert "This is a small page" in text_content
        assert "alert('test')" not in text_content  # Script removed
        assert ".test { color: red; }" not in text_content  # Style removed
        assert soup is not None

    def test_extract_content_large_html_chunked_processing(self, large_html):
        """Test that large HTML uses chunked processing and maintains same output format."""
        processor = ChunkedHTMLProcessor()
        elements_to_remove = ["script", "style", "nav", "header", "aside", "footer"]

        title, clean_html, text_content, error, soup = processor.extract_content(
            large_html, elements_to_remove, "http://test.com"
        )

        # Same return format as original
        assert title == "Large Page with Many Articles"
        assert error is None
        assert soup is not None

        # Content should be extracted
        assert "Article 0" in text_content
        assert "Article 99" in text_content
        assert "Lorem ipsum" in text_content

        # Unwanted elements should be removed
        assert "Navigation that should be removed" not in text_content
        assert "Header that should be removed" not in text_content
        assert "Sidebar that should be removed" not in text_content
        assert "Footer that should be removed" not in text_content
        assert "alert('Should be removed')" not in text_content

    def test_memory_efficiency_large_content(self, large_html):
        """Test that chunked processing is more memory efficient."""
        processor = ChunkedHTMLProcessor()
        elements_to_remove = ["script", "style", "nav", "header", "aside", "footer"]

        # Mock memory monitoring through the MemoryMonitor
        with patch.object(processor.memory_monitor, "get_memory_usage") as mock_memory:
            mock_memory.return_value = 50.0  # 50 MB

            title, clean_html, text_content, error, soup = processor.extract_content(
                large_html, elements_to_remove, "http://test.com"
            )

            # Verify content was extracted successfully
            assert title == "Large Page with Many Articles"
            assert error is None
            assert "Article 1" in text_content
            assert len(text_content) > 100  # Should have substantial content

            # Verify memory monitoring was called
            mock_memory.assert_called()

    def test_error_handling_malformed_html(self, malformed_html):
        """Test error handling with malformed HTML."""
        processor = ChunkedHTMLProcessor()
        elements_to_remove = ["script", "style"]

        title, clean_html, text_content, error, soup = processor.extract_content(
            malformed_html, elements_to_remove, "http://test.com"
        )

        # Should handle malformed HTML gracefully
        assert title == "Malformed"  # Should extract title despite malformation
        assert error is None  # BeautifulSoup handles malformed HTML
        assert "Content here" in text_content
        assert soup is not None

    def test_fallback_on_chunked_processing_failure(self, large_html):
        """Test that processor falls back to original method on chunked processing failure."""
        processor = ChunkedHTMLProcessor()
        elements_to_remove = ["script", "style"]

        # Mock chunked processing to fail
        with patch.object(
            processor,
            "_extract_content_chunked",
            side_effect=Exception("Chunked processing failed"),
        ):
            with patch.object(processor, "_extract_content_original") as mock_original:
                mock_original.return_value = (
                    "Title",
                    "<html>content</html>",
                    "Content",
                    None,
                    Mock(),
                )

                title, clean_html, text_content, error, soup = (
                    processor.extract_content(
                        large_html, elements_to_remove, "http://test.com"
                    )
                )

                # Should have fallen back to original method
                assert mock_original.called
                assert title == "Title"
                assert error is None

    def test_content_area_detection(self, large_html):
        """Test that processor correctly identifies main content areas."""
        processor = ChunkedHTMLProcessor()

        # Parse HTML to BeautifulSoup first
        soup = BeautifulSoup(large_html, "html.parser")
        content_areas = processor._identify_content_areas(soup)

        # Should find main content area
        assert len(content_areas) > 0
        # Should prioritize semantic elements
        main_area = str(content_areas[0])
        assert 'class="content"' in main_area or "main" in main_area.lower()

    def test_performance_monitoring(self, large_html):
        """Test that performance metrics are collected."""
        processor = ChunkedHTMLProcessor()
        elements_to_remove = ["script", "style"]

        title, clean_html, text_content, error, soup = processor.extract_content(
            large_html, elements_to_remove, "http://test.com"
        )

        # Should have performance metrics
        metrics = processor.get_last_processing_metrics()
        assert metrics is not None
        assert "processing_time" in metrics
        assert "content_size_mb" in metrics
        assert "used_chunked_processing" in metrics
        assert "memory_peak_mb" in metrics

    def test_backward_compatibility_with_original_function(self, small_html):
        """Test that results match original _extract_and_clean_html function."""
        processor = ChunkedHTMLProcessor(enable_chunking=False)  # Force original method
        elements_to_remove = ["script", "style"]

        # Get result from new processor (using original method)
        new_title, new_clean_html, new_text, new_error, new_soup = (
            processor.extract_content(small_html, elements_to_remove, "http://test.com")
        )

        # Get result from original function
        orig_soup, orig_target = _extract_and_clean_html(small_html, elements_to_remove)
        orig_title = (
            orig_soup.title.string.strip()
            if orig_soup.title and orig_soup.title.string
            else ""
        )
        orig_text = (
            orig_target.get_text(separator="\n", strip=True) if orig_target else ""
        )

        # Results should be identical
        assert new_title == orig_title
        assert new_text == orig_text
        assert new_error is None

    def test_integration_with_existing_scraper(self):
        """Test integration point with existing scraper code."""
        # This test ensures the integration point works correctly
        from src.scraper.infrastructure.external.chunked_processor import (
            extract_clean_html_optimized,
        )

        html = (
            "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        )
        elements_to_remove = ["script"]
        url = "http://test.com"

        # Should return same format as original extract_clean_html
        result = extract_clean_html_optimized(html, elements_to_remove, url)

        assert len(result) == 5  # title, clean_html, text_content, error, soup
        title, clean_html, text_content, error, soup = result
        assert title == "Test"
        assert "Content" in text_content
        assert error is None

    def test_output_consistency(self):
        """Test that chunked and non-chunked processing produce identical output"""
        # Create test content with 100 articles
        articles = []
        for i in range(100):
            articles.append(
                f'<article class="content"><h1>Article {i}</h1><p>Content {i}</p><span class="author">Author {i}</span></article>'
            )
        html_content = (
            "<html><head><title>Test Page</title></head><body>"
            + "".join(articles)
            + "</body></html>"
        )

        # Process with chunked processing enabled
        chunked_processor = ChunkedHTMLProcessor(enable_chunking=True)
        chunked_result = chunked_processor.extract_content(
            html_content, [], "http://test.com"
        )

        # Process with chunked processing disabled (original method)
        non_chunked_processor = ChunkedHTMLProcessor(enable_chunking=False)
        non_chunked_result = non_chunked_processor.extract_content(
            html_content, [], "http://test.com"
        )

        # Compare results - both should return tuples with same format
        assert len(chunked_result) == len(non_chunked_result), (
            "Results have different lengths"
        )

        # Unpack tuples
        title_chunk, clean_html_chunk, text_chunk, error_chunk, soup_chunk = (
            chunked_result
        )
        title_orig, clean_html_orig, text_orig, error_orig, soup_orig = (
            non_chunked_result
        )

        # Compare individual components
        assert title_chunk == title_orig, (
            f"Titles differ: '{title_chunk}' vs '{title_orig}'"
        )
        assert error_chunk == error_orig, (
            f"Errors differ: '{error_chunk}' vs '{error_orig}'"
        )

        # Normalize HTML and text for comparison
        def normalize_text(text):
            return " ".join(text.split()) if text else ""

        def normalize_html(html):
            if not html:
                return ""
            soup = BeautifulSoup(html, "html.parser")
            return str(soup)

        norm_text_chunk = normalize_text(text_chunk)
        norm_text_orig = normalize_text(text_orig)

        norm_html_chunk = normalize_html(clean_html_chunk)
        norm_html_orig = normalize_html(clean_html_orig)

        # Check that both contain all articles
        for i in range(100):
            article_title = f"Article {i}"
            assert article_title in text_orig, (
                f"Article {i} missing from original output"
            )
            assert article_title in text_chunk, (
                f"Article {i} missing from chunked output"
            )

            author = f"Author {i}"
            assert author in text_orig, f"Author {i} missing from original output"
            assert author in text_chunk, f"Author {i} missing from chunked output"

        # The text content should be identical
        assert norm_text_chunk == norm_text_orig, (
            f"Text content differs:\nChunked: {norm_text_chunk[:500]}...\nOriginal: {norm_text_orig[:500]}..."
        )

        # The HTML content should be identical after normalization
        assert norm_html_chunk == norm_html_orig, (
            f"HTML content differs:\nChunked: {norm_html_chunk[:500]}...\nOriginal: {norm_html_orig[:500]}..."
        )
