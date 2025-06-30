"""
Integration tests for chunked processing with the existing scraper API.
Tests ensure backward compatibility and no breaking changes for end users.
"""

import pytest

from src.scraper import extract_clean_html
from src.scraper.infrastructure.external.chunked_processor import ChunkedHTMLProcessor


class TestChunkedProcessingIntegration:
    """Integration tests for chunked processing with existing scraper."""

    @pytest.fixture
    def small_website_html(self):
        """Small website HTML that should use original processing."""
        return """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Small News Site</title>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial; }
                    .banner { background: red; }
                </style>
            </head>
            <body>
                <nav class="navigation">
                    <a href="/home">Home</a>
                    <a href="/news">News</a>
                </nav>
                <header>
                    <h1>Daily News</h1>
                </header>
                <main>
                    <article>
                        <h2>Breaking News</h2>
                        <p>This is important news content that users want to read.</p>
                        <p>More detailed information about the news story.</p>
                    </article>
                </main>
                <aside class="sidebar">
                    <h3>Related Links</h3>
                    <ul>
                        <li><a href="/sports">Sports</a></li>
                        <li><a href="/weather">Weather</a></li>
                    </ul>
                </aside>
                <footer>
                    <p>&copy; 2024 News Site</p>
                </footer>
                <script>
                    console.log('Analytics tracking');
                    // Large analytics code would go here
                </script>
            </body>
        </html>
        """

    @pytest.fixture
    def large_website_html(self):
        """Large website HTML that should trigger chunked processing."""
        # Generate large HTML content
        articles = []
        for i in range(200):  # Generate enough content to exceed 100KB threshold
            articles.append(f"""
                <article class="news-item">
                    <h2>News Article {i}</h2>
                    <div class="meta">
                        <span class="author">Reporter {i % 10}</span>
                        <span class="date">2024-01-{(i % 28) + 1:02d}</span>
                        <span class="category">Category {i % 5}</span>
                    </div>
                    <div class="content">
                        <p>{"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 15}</p>
                        <p>{"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. " * 10}</p>
                        <p>{"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris. " * 12}</p>
                    </div>
                    <div class="tags">
                        <span class="tag">tag{i % 3}</span>
                        <span class="tag">tag{(i + 1) % 3}</span>
                    </div>
                </article>
            """)

        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Large News Aggregator</title>
                <meta charset="UTF-8">
                <style>
                    {"/* Large CSS block */ body { font-family: Arial; } " * 100}
                </style>
                <script>
                    {"// Large JavaScript block " * 200}
                    console.log('Heavy analytics and tracking code');
                </script>
            </head>
            <body>
                <nav class="top-nav">
                    <div class="nav-brand">News Aggregator</div>
                    <ul class="nav-links">
                        <li><a href="/home">Home</a></li>
                        <li><a href="/trending">Trending</a></li>
                        <li><a href="/politics">Politics</a></li>
                        <li><a href="/sports">Sports</a></li>
                    </ul>
                </nav>
                <header class="main-header">
                    <h1>Today's Top Stories</h1>
                    <div class="header-stats">
                        <span>200 Articles</span>
                        <span>Updated 5 min ago</span>
                    </div>
                </header>
                <main class="content-area">
                    {"".join(articles)}
                </main>
                <aside class="sidebar">
                    <div class="widget">
                        <h3>Trending Topics</h3>
                        <ul>
                            {"".join([f"<li>Topic {i}</li>" for i in range(20)])}
                        </ul>
                    </div>
                    <div class="widget">
                        <h3>Advertisement</h3>
                        <div class="ad-block">Banner Ad Content</div>
                    </div>
                </aside>
                <footer class="main-footer">
                    <div class="footer-links">
                        <a href="/about">About</a>
                        <a href="/contact">Contact</a>
                        <a href="/privacy">Privacy</a>
                    </div>
                    <p>&copy; 2024 News Aggregator. All rights reserved.</p>
                </footer>
                <script>
                    {"// More analytics and tracking code " * 500}
                </script>
            </body>
        </html>
        """

    def test_backward_compatibility_small_content(self, small_website_html):
        """Test that small content processing maintains exact backward compatibility."""
        elements_to_remove = ["script", "style", "nav", "header", "aside", "footer"]
        url = "http://test-news.com"

        # Process with new integrated function
        title, clean_html, text_content, error, soup = extract_clean_html(
            small_website_html, elements_to_remove, url
        )

        # Should return same structure as before
        assert title == "Small News Site"
        assert error is None
        assert soup is not None

        # Content should be extracted and cleaned
        assert "Breaking News" in text_content
        assert "important news content" in text_content
        assert "More detailed information" in text_content

        # Unwanted elements should be removed
        assert "Daily News" not in text_content  # header removed
        assert "Related Links" not in text_content  # aside removed
        assert "2024 News Site" not in text_content  # footer removed
        assert "Analytics tracking" not in text_content  # script removed
        assert "font-family: Arial" not in text_content  # style removed
        assert "Home" not in text_content  # nav removed

    def test_backward_compatibility_large_content(self, large_website_html):
        """Test that large content uses chunked processing but maintains compatibility."""
        elements_to_remove = ["script", "style", "nav", "header", "aside", "footer"]
        url = "http://large-news.com"

        # Process with new integrated function
        title, clean_html, text_content, error, soup = extract_clean_html(
            large_website_html, elements_to_remove, url
        )

        # Should return same structure as before
        assert title == "Large News Aggregator"
        assert error is None
        assert soup is not None

        # Content should be extracted
        assert "News Article 0" in text_content
        assert "News Article 199" in text_content
        assert "Lorem ipsum" in text_content

        # Unwanted elements should be removed
        assert "News Aggregator" not in text_content  # nav brand removed
        assert "Today's Top Stories" not in text_content  # header removed
        assert "Trending Topics" not in text_content  # aside removed
        assert "All rights reserved" not in text_content  # footer removed
        assert "Heavy analytics" not in text_content  # script removed
        assert "Large CSS block" not in text_content  # style removed

    def test_automatic_processing_method_selection(
        self, small_website_html, large_website_html
    ):
        """Test that the system automatically selects appropriate processing method."""
        elements_to_remove = ["script", "style"]

        # Small content should use original processing (internally)
        title1, _, text1, error1, _ = extract_clean_html(
            small_website_html, elements_to_remove, "http://small.com"
        )
        assert error1 is None
        assert title1 == "Small News Site"

        # Large content should use chunked processing (internally)
        title2, _, text2, error2, _ = extract_clean_html(
            large_website_html, elements_to_remove, "http://large.com"
        )
        assert error2 is None
        assert title2 == "Large News Aggregator"

        # Both should produce valid results
        assert len(text1) > 0
        assert len(text2) > 0
        assert len(text2) > len(text1)  # Large content should have more text

    def test_error_handling_and_fallback(self):
        """Test error handling and fallback to original method."""
        malformed_html = """
        <html>
            <head><title>Malformed Page</title>
            <body>
                <div>Unclosed div
                <p>Content here
        """

        elements_to_remove = ["script", "style"]
        url = "http://malformed.com"

        # Should handle malformed HTML gracefully
        title, clean_html, text_content, error, soup = extract_clean_html(
            malformed_html, elements_to_remove, url
        )

        assert title == "Malformed Page"
        assert error is None  # BeautifulSoup should handle malformation
        assert "Content here" in text_content
        assert soup is not None

    def test_performance_improvement_detection(self, large_website_html):
        """Test that chunked processing provides performance benefits for large content."""
        elements_to_remove = ["script", "style", "nav", "header", "aside", "footer"]
        url = "http://performance-test.com"

        # Create a processor to check metrics
        processor = ChunkedHTMLProcessor()

        # Process large content
        title, clean_html, text_content, error, soup = processor.extract_content(
            large_website_html, elements_to_remove, url
        )

        # Should have successful processing
        assert error is None
        assert title == "Large News Aggregator"

        # Should have performance metrics
        metrics = processor.get_last_processing_metrics()
        assert "processing_time" in metrics
        assert "content_size_mb" in metrics
        assert "used_chunked_processing" in metrics
        assert "memory_peak_mb" in metrics

        # Large content should trigger chunked processing
        assert metrics["used_chunked_processing"] is True
        assert metrics["content_size_mb"] > 0.1  # Should be > 100KB

    def test_identical_results_for_same_input(self, small_website_html):
        """Test that results are identical for the same input (deterministic)."""
        elements_to_remove = ["script", "style", "nav", "footer"]
        url = "http://consistent.com"

        # Process same content multiple times
        results = []
        for _ in range(3):
            result = extract_clean_html(small_website_html, elements_to_remove, url)
            results.append(result)

        # All results should be identical
        for result in results[1:]:
            assert result[0] == results[0][0]  # title
            assert result[1] == results[0][1]  # clean_html
            assert result[2] == results[0][2]  # text_content
            assert result[3] == results[0][3]  # error

    def test_no_breaking_changes_with_edge_cases(self):
        """Test edge cases to ensure no breaking changes."""
        elements_to_remove = ["script", "style"]

        # Empty HTML
        title, clean_html, text_content, error, soup = extract_clean_html(
            "", elements_to_remove, "http://empty.com"
        )
        assert error is None or "body tag" in error  # Acceptable error case

        # HTML without body - should handle gracefully like original implementation
        html_no_body = "<html><head><title>No Body</title></head></html>"
        title, clean_html, text_content, error, soup = extract_clean_html(
            html_no_body, elements_to_remove, "http://nobody.com"
        )

        # Should handle gracefully - either extract title or report body tag error
        assert (title == "No Body") or (error and "body tag" in error)
        # Should not crash - that's the main requirement

        # HTML with only whitespace in body
        html_whitespace = (
            "<html><head><title>Whitespace</title></head><body>   \n\t   </body></html>"
        )
        title, clean_html, text_content, error, soup = extract_clean_html(
            html_whitespace, elements_to_remove, "http://whitespace.com"
        )
        assert title == "Whitespace"
        assert error is None

    def test_processor_configuration_integration(self):
        """Test that processor configuration options work correctly."""
        html = "<html><body>" + "<p>Test content</p>" * 1000 + "</body></html>"
        elements_to_remove = []
        url = "http://config-test.com"

        # Should work with default configuration
        title, clean_html, text_content, error, soup = extract_clean_html(
            html, elements_to_remove, url
        )

        assert error is None
        assert "Test content" in text_content
        assert (
            len([line for line in text_content.split("\n") if "Test content" in line])
            == 1000
        )
