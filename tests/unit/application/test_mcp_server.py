"""
Tests for refactored MCP server components following Single Responsibility Principle.

This test file defines the expected behavior after separating concerns in the MCP server
into distinct services that each have a single responsibility.
"""

from unittest.mock import AsyncMock

import pytest

from src.mcp_server import (
    MCPParameterValidator,
    MCPRequestHandler,
    MCPResponseFormatter,
)
from src.output_format_handler import OutputFormat


class TestMCPRequestHandler:
    """Test the MCP request handling service that validates and processes requests."""

    @pytest.mark.asyncio
    async def test_handle_tool_request_success(self):
        """Test successful tool request handling with proper separation of concerns."""
        # This test defines expected behavior after refactoring
        # The MCPRequestHandler should only handle request validation and delegation

        # Mock dependencies
        mock_scraper_service = AsyncMock()
        mock_scraper_service.scrape_url.return_value = {
            "content": "Test content",
            "final_url": "https://example.com",
            "title": "Test Page",
        }

        handler = MCPRequestHandler(
            scraper_service=mock_scraper_service,
            validator=MCPParameterValidator(),
            formatter=MCPResponseFormatter(),
        )

        # Test request handling
        arguments = {"url": "https://example.com", "output_format": "markdown"}

        result = await handler.handle_tool_request("scrape_web", arguments)

        # Verify the handler properly delegates to the scraper service
        mock_scraper_service.scrape_url.assert_called_once()
        assert result is not None
        assert "content" in str(result)

    @pytest.mark.asyncio
    async def test_handle_tool_request_validation_error(self):
        """Test that request handler properly validates input parameters."""
        mock_scraper_service = AsyncMock()
        handler = MCPRequestHandler(
            scraper_service=mock_scraper_service,
            validator=MCPParameterValidator(),
            formatter=MCPResponseFormatter(),
        )

        # Test with invalid tool name
        with pytest.raises(Exception) as exc_info:
            await handler.handle_tool_request("invalid_tool", {})

        assert "Unknown tool" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_prompt_request_success(self):
        """Test successful prompt request handling."""
        mock_scraper_service = AsyncMock()
        mock_scraper_service.scrape_url.return_value = {
            "content": "Test content",
            "final_url": "https://example.com",
            "title": "Test Page",
        }

        handler = MCPRequestHandler(
            scraper_service=mock_scraper_service,
            validator=MCPParameterValidator(),
            formatter=MCPResponseFormatter(),
        )

        arguments = {"url": "https://example.com"}
        result = await handler.handle_prompt_request("scrape", arguments)

        mock_scraper_service.scrape_url.assert_called_once()
        assert result is not None


class TestMCPResponseFormatter:
    """Test the MCP response formatting service."""

    def test_format_tool_response_success(self):
        """Test formatting successful tool responses."""
        formatter = MCPResponseFormatter()

        scraper_result = {
            "content": "Test content",
            "final_url": "https://example.com",
            "title": "Test Page",
        }

        response = formatter.format_tool_response(scraper_result)

        # The response is now a dictionary with the scraper result data
        assert isinstance(response, dict)
        assert response["content"] == "Test content"
        assert response["final_url"] == "https://example.com"
        assert response["title"] == "Test Page"

    def test_format_prompt_response_success(self):
        """Test formatting successful prompt responses."""
        formatter = MCPResponseFormatter()

        scraper_result = {
            "content": "Test content",
            "final_url": "https://example.com",
            "title": "Test Page",
        }

        response = formatter.format_prompt_response(scraper_result)

        assert response.description is not None
        assert len(response.messages) == 1
        assert response.messages[0].content.text == "Test content"


class TestMCPParameterValidator:
    """Test the MCP parameter validation service."""

    def test_validate_tool_parameters_success(self):
        """Test successful parameter validation for tools."""
        validator = MCPParameterValidator()

        arguments = {
            "url": "https://example.com",
            "max_length": 1000,
            "output_format": "markdown",
        }

        validated_args = validator.validate_tool_parameters("scrape_web", arguments)

        assert str(validated_args.url) == "https://example.com/"
        assert validated_args.max_length == 1000
        assert validated_args.output_format == OutputFormat.MARKDOWN

    def test_validate_tool_parameters_invalid_tool(self):
        """Test parameter validation with invalid tool name."""
        validator = MCPParameterValidator()

        with pytest.raises(Exception) as exc_info:
            validator.validate_tool_parameters("invalid_tool", {})

        assert "Unknown tool" in str(exc_info.value)

    def test_validate_prompt_parameters_success(self):
        """Test successful parameter validation for prompts."""
        validator = MCPParameterValidator()

        arguments = {"url": "https://example.com", "output_format": "text"}

        validated_args = validator.validate_prompt_parameters("scrape", arguments)

        assert str(validated_args.url) == "https://example.com/"
        assert validated_args.output_format == OutputFormat.TEXT
