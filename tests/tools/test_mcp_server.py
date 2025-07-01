from unittest.mock import AsyncMock, patch

import pytest
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS

from src.mcp_server_refactored import (
    MCPParameterValidator,
    MCPRequestHandler,
    MCPResponseFormatter,
)
from src.scraper.application.services.web_scraping_service import WebScrapingService


class TestMCPServerComponents:
    """Test cases for individual components of the MCP server."""

    @pytest.mark.asyncio
    async def test_request_handler_unknown_tool(self):
        """Test request handler with an unknown tool."""
        handler = MCPRequestHandler(
            None, MCPParameterValidator(), MCPResponseFormatter()
        )
        with pytest.raises(McpError) as excinfo:
            await handler.handle_tool_request("unknown_tool", {})
        assert excinfo.value.error_data.code == INVALID_PARAMS
        assert "Unknown tool" in excinfo.value.error_data.message

    @pytest.mark.asyncio
    async def test_request_handler_scrape_tool(self):
        """Test request handler with scrape tool."""
        with patch(
            "src.scraper.application.services.web_scraping_service.WebScrapingService.scrape_url"
        ) as mock_scrape_url:
            # Mock successful scraping
            mock_scrape_url.return_value = {
                "title": "Test Page",
                "content": "Test content",
                "final_url": "https://example.com",
                "error": None,
            }

            # Mock the service that will be passed to the handler
            mock_scraping_service = AsyncMock(spec=WebScrapingService)
            mock_scraping_service.scrape_url = mock_scrape_url

            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(mock_scraping_service, validator, formatter)

            arguments = {"url": "https://example.com", "output_format": "markdown"}

            result = await handler.handle_tool_request("scrape_web", arguments)

            assert "title" in result
            assert "content" in result
            assert result["title"] == "Test Page"
            mock_scrape_url.assert_called_once()


class TestMCPParameterValidation:
    """Test cases for MCP parameter validation."""

    def test_validate_tool_parameters_valid_url(self):
        """Test validation with valid URL."""
        validator = MCPParameterValidator()

        params = {"url": "https://example.com", "output_format": "markdown"}

        # Should not raise exception
        validated = validator.validate_tool_parameters("scrape_web", params)
        assert str(validated.url) == "https://example.com/"

    def test_validate_tool_parameters_missing_url(self):
        """Test validation with missing URL."""
        validator = MCPParameterValidator()
        with pytest.raises(McpError) as excinfo:
            validator.validate_tool_parameters(
                "scrape_web", {"output_format": "markdown"}
            )
        assert excinfo.value.error_data.code == INVALID_PARAMS
        assert "URL is required" in excinfo.value.error_data.message

    def test_validate_tool_parameters_invalid_url(self):
        """Test validation with invalid URL."""
        validator = MCPParameterValidator()
        with pytest.raises(McpError):
            validator.validate_tool_parameters(
                "scrape_web", {"url": "not-a-url", "output_format": "markdown"}
            )

    def test_validate_tool_parameters_optional_fields(self):
        """Test validation with optional fields."""
        validator = MCPParameterValidator()

        params = {
            "url": "https://example.com",
            "output_format": "markdown",
            "max_length": 1000,
            "timeout_seconds": 29,
            "user_agent": "TestBot/1.0",
        }

        validated = validator.validate_tool_parameters("scrape_web", params)
        assert validated.max_length == 1000
        assert validated.timeout_seconds == 29
        assert validated.user_agent == "TestBot/1.0"


class TestMCPResponseFormatting:
    """Test cases for MCP response formatting."""

    def test_format_response_success(self):
        """Test formatting a successful response."""
        formatter = MCPResponseFormatter()
        scrape_result = {
            "title": "Success",
            "content": "Content here",
            "final_url": "https://final.com",
            "error": None,
        }
        formatted = formatter.format_response(scrape_result, "scrape_web")
        assert formatted["tool_name"] == "scrape_web"
        assert formatted["result"]["title"] == "Success"
        assert "error" not in formatted["result"]

    def test_format_response_error(self):
        """Test formatting an error response."""
        formatter = MCPResponseFormatter()
        scrape_result = {"error": "Scraping failed", "final_url": "https://site.com"}
        with pytest.raises(McpError) as excinfo:
            formatter.format_response(scrape_result, "scrape_web")
        assert excinfo.value.error_data.code == -32000
        assert "Scraping failed" in excinfo.value.error_data.message
        assert "final_url" in excinfo.value.error_data.data


class TestMCPIntegration:
    """Integration-style tests for the MCP server."""

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self):
        """Test complete MCP scraping workflow."""
        with patch(
            "src.scraper.application.services.web_scraping_service.WebScrapingService.scrape_url"
        ) as mock_scrape_url:
            mock_scrape_url.return_value = {
                "title": "Integration Test Page",
                "content": "This is integration test content",
                "final_url": "https://example.com/test",
                "error": None,
            }

            # We need to ensure the handler is created with a service that has the scrape_url method
            mock_service = AsyncMock(spec=WebScrapingService)
            mock_service.scrape_url = mock_scrape_url

            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(mock_service, validator, formatter)

            request = {
                "tool_name": "scrape_web",
                "arguments": {"url": "https://example.com", "output_format": "text"},
            }

            response = await handler.handle_tool_request(
                request["tool_name"], request["arguments"]
            )

            assert response["title"] == "Integration Test Page"
            assert "This is integration test content" in response["content"]
            # The scrape_url method expects keyword arguments from the dumped ScrapeArgs model
            validated_args = validator.validate_tool_parameters(
                request["tool_name"], request["arguments"]
            )
            mock_scrape_url.assert_called_with(
                **validated_args.model_dump(exclude_none=True)
            )
