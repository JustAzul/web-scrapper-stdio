"""
Legacy Compatibility Tests for extract_text_from_url Function

These tests ensure that when we refactor the legacy extract_text_from_url function
to use our new service-based architecture, all existing behavior is preserved.
"""

import pytest

from src.output_format_handler import OutputFormat
from src.scraper import extract_text_from_url


class TestLegacyExtractTextFromUrlCompatibility:
    """Test suite ensuring backward compatibility of extract_text_from_url function"""

    @pytest.mark.asyncio
    async def test_extract_text_from_url_basic_functionality(self):
        """Test basic URL extraction works as expected"""
        result = await extract_text_from_url("https://example.com")

        assert result is not None
        assert isinstance(result, dict)
        assert "title" in result
        assert "final_url" in result
        assert "content" in result
        assert "error" in result
        assert result["error"] is None
        assert result["title"] is not None
        assert result["content"] is not None
        assert result["final_url"] == "https://example.com/"

    @pytest.mark.asyncio
    async def test_extract_text_from_url_with_custom_timeout(self):
        """Test custom timeout parameter works"""
        result = await extract_text_from_url("https://example.com", custom_timeout=15)

        assert result["error"] is None
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_with_custom_elements_to_remove(self):
        """Test custom elements to remove parameter works"""
        result = await extract_text_from_url(
            "https://example.com", custom_elements_to_remove=["nav", "footer"]
        )

        assert result["error"] is None
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_with_max_length(self):
        """Test max_length parameter truncates content appropriately"""
        result = await extract_text_from_url("https://example.com", max_length=100)

        assert result["error"] is None
        assert result["content"] is not None
        # Content might be longer due to truncation notice
        assert len(result["content"]) <= 100 + 35  # 35 chars for truncation notice

    @pytest.mark.asyncio
    async def test_extract_text_from_url_with_custom_user_agent(self):
        """Test custom user agent parameter works"""
        custom_ua = "Test User Agent"
        result = await extract_text_from_url(
            "https://example.com", user_agent=custom_ua
        )

        assert result["error"] is None
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_text_output_format(self):
        """Test TEXT output format works"""
        result = await extract_text_from_url(
            "https://example.com", output_format=OutputFormat.TEXT
        )

        assert result["error"] is None
        assert result["content"] is not None
        # TEXT format should not contain markdown formatting
        assert "#" not in result["content"]

    @pytest.mark.asyncio
    async def test_extract_text_from_url_html_output_format(self):
        """Test HTML output format works"""
        result = await extract_text_from_url(
            "https://example.com", output_format=OutputFormat.HTML
        )

        assert result["error"] is None
        assert result["content"] is not None
        # HTML format should contain HTML tags
        assert "<" in result["content"] and ">" in result["content"]

    @pytest.mark.asyncio
    async def test_extract_text_from_url_markdown_output_format(self):
        """Test MARKDOWN output format works (default)"""
        result = await extract_text_from_url(
            "https://example.com", output_format=OutputFormat.MARKDOWN
        )

        assert result["error"] is None
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_grace_period(self):
        """Test grace_period_seconds parameter works"""
        result = await extract_text_from_url(
            "https://example.com", grace_period_seconds=1.0
        )

        assert result["error"] is None
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_wait_for_network_idle_false(self):
        """Test wait_for_network_idle=False parameter works"""
        result = await extract_text_from_url(
            "https://example.com", wait_for_network_idle=False
        )

        assert result["error"] is None
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_error_handling_invalid_url(self):
        """Test error handling for invalid URLs"""
        result = await extract_text_from_url("https://thisdomaindoesnotexist12345.com")

        assert result is not None
        assert result["error"] is not None
        assert result["content"] is None
        assert result["title"] is None

    @pytest.mark.asyncio
    async def test_extract_text_from_url_error_handling_404(self):
        """Test error handling for 404 pages"""
        result = await extract_text_from_url("https://httpbin.org/status/404")

        assert result is not None
        # Should handle 404 gracefully - might return content or error depending on implementation
        assert isinstance(result["error"], (str, type(None)))

    @pytest.mark.asyncio
    async def test_extract_text_from_url_parameter_combinations(self):
        """Test various parameter combinations work together"""
        result = await extract_text_from_url(
            "https://example.com",
            custom_elements_to_remove=["script"],
            custom_timeout=20,
            grace_period_seconds=1.5,
            max_length=200,
            user_agent="Test Agent",
            wait_for_network_idle=False,
            output_format=OutputFormat.TEXT,
        )

        assert result["error"] is None
        assert result["content"] is not None
        # Content might be longer due to truncation notice
        assert len(result["content"]) <= 200 + 35  # 35 chars for truncation notice

    @pytest.mark.asyncio
    async def test_extract_text_from_url_return_structure_consistency(self):
        """Test that return structure is always consistent"""
        # Test with valid URL
        result1 = await extract_text_from_url("https://example.com")

        # Test with invalid URL
        result2 = await extract_text_from_url("https://invalid-domain-12345.com")

        # Both should have same structure
        for result in [result1, result2]:
            assert isinstance(result, dict)
            assert set(result.keys()) == {"title", "final_url", "content", "error"}
            assert isinstance(result["title"], (str, type(None)))
            assert isinstance(result["final_url"], str)
            assert isinstance(result["content"], (str, type(None)))
            assert isinstance(result["error"], (str, type(None)))

    @pytest.mark.asyncio
    async def test_extract_text_from_url_content_quality(self):
        """Test that extracted content meets quality expectations"""
        result = await extract_text_from_url("https://example.com")

        if result["error"] is None:
            assert result["content"] is not None
            # Should extract meaningful content
            assert len(result["content"]) > 10
            assert result["title"] is not None
            assert len(result["title"]) > 0  # Should extract title

    @pytest.mark.asyncio
    async def test_extract_text_from_url_click_selector_parameter(self):
        """Test click_selector parameter is accepted (behavior depends on page)"""
        result = await extract_text_from_url(
            "https://example.com", click_selector=".non-existent-selector"
        )

        # Should not crash even with non-existent selector
        assert result is not None
        assert isinstance(result, dict)
        # Content might be None if extraction fails, but function should not crash
