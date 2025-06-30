from src.scraper import ChunkedHTMLProcessor


class TestChunkedProcessingEdgeCases:
    """Edge case tests for chunked processing."""

    def test_empty_html(self):
        """Test handling of empty HTML."""
        processor = ChunkedHTMLProcessor()

        title, clean_html, text_content, error, soup = processor.extract_content(
            "", [], "http://test.com"
        )

        assert title == ""
        assert text_content == ""
        assert error is None

    def test_html_without_body(self):
        """Test handling of HTML without body tag."""
        processor = ChunkedHTMLProcessor()
        html = "<html><head><title>No Body</title></head></html>"

        title, clean_html, text_content, error, soup = processor.extract_content(
            html, [], "http://test.com"
        )

        assert title == "No Body"
        assert error is None

    def test_html_with_multiple_main_elements(self):
        """Test handling of HTML with multiple main content areas."""
        processor = ChunkedHTMLProcessor()
        html = """
        <html>
            <body>
                <main>First main content</main>
                <article>Article content</article>
                <main>Second main content</main>
            </body>
        </html>
        """

        title, clean_html, text_content, error, soup = processor.extract_content(
            html, [], "http://test.com"
        )

        assert "First main content" in text_content
        assert "Article content" in text_content
        assert error is None

    def test_extremely_nested_html(self):
        """Test handling of extremely nested HTML structures."""
        processor = ChunkedHTMLProcessor()

        # Create deeply nested structure
        nested_html = "<html><body>"
        for i in range(100):
            nested_html += f"<div class='level-{i}'>"
        nested_html += "Deep content"
        for i in range(100):
            nested_html += "</div>"
        nested_html += "</body></html>"

        title, clean_html, text_content, error, soup = processor.extract_content(
            nested_html, [], "http://test.com"
        )

        assert "Deep content" in text_content
        assert error is None
