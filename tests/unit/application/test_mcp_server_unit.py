"""Unit tests for the MCP server."""
# import pytest
# from unittest.mock import AsyncMock, MagicMock
#
# from src.mcp_server import (
#     ScrapeArgs,
#     extract_text_from_url,
#     MCPParameterValidator,
#     serve,
# )
#
# @pytest.fixture
# def mock_scraper():
#     """Fixture to mock the Scraper class."""
#     return MagicMock()
#
# @pytest.mark.asyncio
# async def test_extract_text_from_url_success(mock_scraper):
#     """Test successful extraction from URL."""
#     mock_scraper.run.return_value = "<html><body>Mocked Content</body></html>"
#     result = await extract_text_from_url("http://example.com", scraper=mock_scraper)
#     assert "Mocked Content" in result
#
# @pytest.mark.asyncio
# async def test_extract_text_from_url_with_all_params(mock_scraper):
#     """Test successful extraction with all parameters."""
#     mock_scraper.run.return_value = "<html><body>All Params Content</body></html>"
#     kwargs = {
#         "output_format": "text",
#         "timeout_seconds": 60,
#         "max_length": 500,
#         "user_agent": "TestAgent/1.0",
#     }
#     result = await extract_text_from_url(
#         "http://example.com", scraper=mock_scraper, **kwargs
#     )
#     assert "All Params Content" in result
#
# @pytest.mark.asyncio
# async def test_extract_text_from_url_failure(mock_scraper):
#     """Test extraction failure."""
#     mock_scraper.run.side_effect = Exception("Scraping failed")
#     result = await extract_text_from_url("http://example.com", scraper=mock_scraper)
#     assert "Error: Scraping failed" in result
#
# def test_mcp_parameter_validator():
#     """Test MCP parameter validation."""
#     validator = MCPParameterValidator(extract_text_from_url)
#     validated_func = validator.get_validated_method()
#
#     # Test with valid parameters
#     validated_func(url="http://example.com", timeout_seconds=45)
#
#     # Test with invalid timeout
#     with pytest.raises(ValueError):
#         validated_func(url="http://example.com", timeout_seconds=200)
#
#     # Test with invalid URL
#     with pytest.raises(ValueError):
#         validated_func(url="invalid-url")
#
# @pytest.mark.asyncio
# async def test_serve_initialization(mocker):
#     """Test server initialization and shutdown."""
#     # Mock the stdio_server to avoid actual server start
#     mock_stdio_server = AsyncMock()
#     mocker.patch("src.mcp_server.stdio_server", mock_stdio_server)
#
#     # Mock asyncio.Event to control the server loop
#     mock_event = AsyncMock()
#     mock_event.wait.side_effect = [
#         None,
#         KeyboardInterrupt,
#     ]  # Run once, then interrupt
#     mocker.patch("asyncio.Event", return_value=mock_event)
#
#     with pytest.raises(KeyboardInterrupt):
#         await serve()
#
#     mock_stdio_server.assert_called_once()
