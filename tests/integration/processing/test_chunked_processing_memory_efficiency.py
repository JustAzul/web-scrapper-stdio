import pytest

from src.scraper import ChunkedHTMLProcessor


@pytest.mark.integration
class TestChunkedProcessingMemoryEfficiency:
    """Memory efficiency tests for chunked processing that require real processing."""

    @pytest.fixture
    def large_html(self):
        """Generates a large HTML document for memory testing."""
        # Using a smaller multiplier to keep test execution reasonable
        content = "<div>" * 500 + "A" * 1000 + "</div>" * 500
        return f"<html><body>{content}</body></html>"

    def test_graceful_degradation_on_memory_pressure(self, large_html):
        """
        Ensure that chunked processing can handle large content without
        crashing, even under simulated memory pressure (by using a large file).
        """
        processor = ChunkedHTMLProcessor(enable_chunking=True)
        try:
            _, _, text_content, error, _ = processor.extract_content(
                large_html, [], "http://example.com/graceful"
            )
            assert error is None
            assert text_content is not None
            assert len(text_content) > 0
        except MemoryError:
            pytest.fail("Chunked processor failed with MemoryError on large content.")
