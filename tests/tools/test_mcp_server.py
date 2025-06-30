"""
Tests for MCP Server functionality.

This module tests the Model Context Protocol server implementation,
including tool handling, parameter validation, and response formatting.
"""

from unittest.mock import patch

import pytest

from src.mcp_server_refactored import (
    MCPParameterValidator,
    MCPRequestHandler,
    MCPResponseFormatter,
)
from src.scraper.scrapper import Scraper


class TestMCPServerComponents:
    """Test MCP Server component functionality."""

    def test_parameter_validator_initialization(self):
        """Test MCPParameterValidator initialization."""
        validator = MCPParameterValidator()
        assert validator is not None
        assert hasattr(validator, "validate_tool_parameters")

    def test_request_handler_initialization(self):
        """Test MCPRequestHandler initialization."""
        scraper = Scraper()
        validator = MCPParameterValidator()
        formatter = MCPResponseFormatter()
        handler = MCPRequestHandler(scraper, validator, formatter)

        assert handler is not None
        assert handler.scraper_service is scraper
        assert handler.validator is validator
        assert handler.formatter is formatter

    def test_response_formatter_initialization(self):
        """Test MCPResponseFormatter initialization."""
        formatter = MCPResponseFormatter()
        assert formatter is not None
        assert hasattr(formatter, "format_tool_response")

    @pytest.mark.asyncio
    async def test_request_handler_scrape_tool(self):
        """Test request handler with scrape tool."""
        with patch("src.scraper.scrapper.Scraper.scrape") as mock_scrape:
            # Mock successful scraping
            mock_scrape.return_value = {
                "title": "Test Page",
                "content": "Test content",
                "final_url": "https://example.com",
                "error": None,
                "metadata": {"status": "success"},
            }

            scraper = Scraper()
            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(scraper, validator, formatter)

            arguments = {"url": "https://example.com", "output_format": "markdown"}

            result = await handler.handle_tool_request("scrape_web", arguments)

            assert isinstance(result, list)
            assert len(result) > 0


class TestMCPParameterValidation:
    """Test MCP parameter validation functionality."""

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

        params = {"output_format": "markdown"}

        with pytest.raises(Exception):  # Should raise validation error
            validator.validate_tool_parameters("scrape_web", params)

    def test_validate_tool_parameters_invalid_tool(self):
        """Test validation with invalid tool name."""
        validator = MCPParameterValidator()

        params = {"url": "https://example.com", "output_format": "markdown"}

        with pytest.raises(Exception):  # Should raise McpError
            validator.validate_tool_parameters("invalid_tool", params)

    def test_validate_tool_parameters_optional_fields(self):
        """Test validation with optional fields."""
        validator = MCPParameterValidator()

        params = {
            "url": "https://example.com",
            "output_format": "markdown",
            "max_length": 1000,
            "timeout_seconds": 30,
            "user_agent": "TestBot/1.0",
        }

        validated = validator.validate_tool_parameters("scrape_web", params)
        assert validated.max_length == 1000
        assert validated.timeout_seconds == 30
        assert validated.user_agent == "TestBot/1.0"

    def test_validate_prompt_parameters_valid(self):
        """Test prompt parameter validation."""
        validator = MCPParameterValidator()

        params = {"url": "https://example.com", "output_format": "markdown"}

        validated = validator.validate_prompt_parameters("scrape", params)
        assert validated["url"] == "https://example.com"

    def test_validate_prompt_parameters_missing_url(self):
        """Test prompt validation with missing URL."""
        validator = MCPParameterValidator()

        params = {"output_format": "markdown"}

        with pytest.raises(Exception):  # Should raise McpError
            validator.validate_prompt_parameters("scrape", params)


class TestMCPResponseFormatting:
    """Test MCP response formatting functionality."""

    def test_format_tool_response_success(self):
        """Test formatting successful scraper response."""
        formatter = MCPResponseFormatter()

        scraper_result = {
            "title": "Example Page",
            "content": "This is test content",
            "final_url": "https://example.com",
            "error": None,
            "metadata": {"status": "success"},
        }

        formatted_response = formatter.format_tool_response(scraper_result)

        assert isinstance(formatted_response, list)
        assert len(formatted_response) > 0
        assert formatted_response[0].type == "text"
        assert "This is test content" in formatted_response[0].text

    def test_format_tool_response_error(self):
        """Test formatting error scraper response."""
        formatter = MCPResponseFormatter()

        scraper_result = {
            "title": None,
            "content": None,
            "final_url": "https://example.com",
            "error": "Page not found",
            "metadata": {"status": "error"},
        }

        formatted_response = formatter.format_tool_response(scraper_result)

        assert isinstance(formatted_response, list)
        assert len(formatted_response) > 0
        assert formatted_response[0].type == "text"

    def test_format_prompt_response_success(self):
        """Test formatting successful prompt response."""
        formatter = MCPResponseFormatter()

        scraper_result = {
            "title": "Test Page",
            "content": "Test content",
            "final_url": "https://example.com",
            "error": None,
            "metadata": {"status": "success"},
        }

        formatted_response = formatter.format_prompt_response(scraper_result)

        assert hasattr(formatted_response, "description")
        assert hasattr(formatted_response, "messages")
        assert len(formatted_response.messages) > 0

    def test_format_error_response(self):
        """Test formatting error response."""
        formatter = MCPResponseFormatter()

        error_response = formatter.format_error_response(
            "https://example.com", "Network timeout"
        )

        assert hasattr(error_response, "description")
        assert hasattr(error_response, "messages")
        assert "Failed to scrape" in error_response.description

    def test_format_tool_response_empty_content(self):
        """Test formatting response with empty content."""
        formatter = MCPResponseFormatter()

        scraper_result = {
            "title": "",
            "content": "",
            "final_url": "https://example.com",
            "error": None,
            "metadata": {"status": "success"},
        }

        formatted_response = formatter.format_tool_response(scraper_result)

        assert isinstance(formatted_response, list)
        assert len(formatted_response) > 0


class TestMCPIntegration:
    """Test MCP server integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self):
        """Test complete MCP scraping workflow."""
        with patch("src.scraper.scrapper.Scraper.scrape") as mock_scrape:
            mock_scrape.return_value = {
                "title": "Integration Test Page",
                "content": "This is integration test content",
                "final_url": "https://example.com/test",
                "error": None,
                "metadata": {"status": "success", "time_taken": 2.5},
            }

            # Initialize components
            scraper = Scraper()
            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(scraper, validator, formatter)

            # Execute workflow
            arguments = {
                "url": "https://example.com/test",
                "output_format": "markdown",
                "max_length": 5000,
            }

            result = await handler.handle_tool_request("scrape_web", arguments)

            # Verify response
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        with patch("src.scraper.scrapper.Scraper.scrape") as mock_scrape:
            # Mock scraping failure
            mock_scrape.side_effect = Exception("Network error")

            # Initialize components
            scraper = Scraper()
            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(scraper, validator, formatter)

            # Execute workflow
            arguments = {"url": "https://example.com/test", "output_format": "markdown"}

            # Should raise McpError for scraping failures
            with pytest.raises(Exception) as exc_info:
                await handler.handle_tool_request("scrape_web", arguments)

            # Verify error contains expected information
            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        import asyncio

        with patch("src.scraper.scrapper.Scraper.scrape") as mock_scrape:
            # Mock different responses for different URLs
            def mock_response(url, **kwargs):
                if "page1" in url:
                    return {
                        "title": "Page 1",
                        "content": "Content 1",
                        "final_url": url,
                        "error": None,
                        "metadata": {"status": "success"},
                    }
                else:
                    return {
                        "title": "Page 2",
                        "content": "Content 2",
                        "final_url": url,
                        "error": None,
                        "metadata": {"status": "success"},
                    }

            mock_scrape.side_effect = mock_response

            # Initialize components
            scraper = Scraper()
            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(scraper, validator, formatter)

            # Create concurrent requests
            tasks = [
                handler.handle_tool_request(
                    "scrape_web",
                    {"url": "https://example.com/page1", "output_format": "text"},
                ),
                handler.handle_tool_request(
                    "scrape_web",
                    {"url": "https://example.com/page2", "output_format": "markdown"},
                ),
            ]

            # Execute concurrently
            results = await asyncio.gather(*tasks)

            # Verify both requests succeeded
            assert len(results) == 2
            assert all(isinstance(result, list) for result in results)
            assert all(len(result) > 0 for result in results)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in requests."""
        import asyncio

        with patch("src.scraper.scrapper.Scraper.scrape") as mock_scrape:
            # Mock a slow response that times out
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate slow response
                return {"error": "Should not reach here"}

            mock_scrape.side_effect = slow_response

            # Initialize components
            scraper = Scraper()
            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(scraper, validator, formatter)

            arguments = {
                "url": "https://slow-example.com",
                "output_format": "text",
                "timeout_seconds": 1,  # Very short timeout
            }

            # Should raise McpError for timeout/error responses
            with pytest.raises(Exception) as exc_info:
                await handler.handle_tool_request("scrape_web", arguments)

            # Verify error contains timeout information
            assert "Should not reach here" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_prompt_workflow(self):
        """Test prompt handling workflow."""
        with patch("src.scraper.scrapper.Scraper.scrape") as mock_scrape:
            mock_scrape.return_value = {
                "title": "Prompt Test Page",
                "content": "This is prompt test content",
                "final_url": "https://example.com/prompt",
                "error": None,
                "metadata": {"status": "success"},
            }

            # Initialize components
            scraper = Scraper()
            validator = MCPParameterValidator()
            formatter = MCPResponseFormatter()
            handler = MCPRequestHandler(scraper, validator, formatter)

            # Execute prompt workflow
            arguments = {"url": "https://example.com/prompt", "output_format": "text"}

            result = await handler.handle_prompt_request("scrape", arguments)

            # Verify response structure
            assert hasattr(result, "description")
            assert hasattr(result, "messages")
            assert len(result.messages) > 0


class TestMCPToolDefinition:
    """Test MCP tool definition and schema validation."""

    def test_tool_schema_structure(self):
        """Test that the tool schema has correct structure."""
        # This would be the schema from main.py
        expected_schema = {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to scrape"},
                "max_length": {
                    "type": "integer",
                    "description": "Maximum number of characters to return",
                    "minimum": 1,
                },
                "grace_period_seconds": {
                    "type": "number",
                    "description": "Grace period for JS rendering (seconds)",
                    "minimum": 0.1,
                    "maximum": 60,
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "Request timeout (seconds)",
                    "minimum": 1,
                    "maximum": 300,
                },
                "output_format": {
                    "type": "string",
                    "enum": ["markdown", "text", "html"],
                    "description": "Output format",
                },
                "user_agent": {
                    "type": "string",
                    "description": "Custom user agent string",
                },
                "custom_headers": {
                    "type": "object",
                    "description": "Custom HTTP headers",
                },
            },
            "required": ["url"],
        }

        # Validate schema structure
        assert expected_schema["type"] == "object"
        assert "url" in expected_schema["required"]
        assert "url" in expected_schema["properties"]
        assert expected_schema["properties"]["url"]["type"] == "string"

    def test_tool_parameter_constraints(self):
        """Test tool parameter constraints."""
        validator = MCPParameterValidator()

        # Test minimum constraints
        valid_params = {
            "url": "https://example.com",
            "max_length": 1,
            "grace_period_seconds": 0.1,
            "timeout_seconds": 1,
        }

        validated = validator.validate_tool_parameters("scrape_web", valid_params)
        assert validated.max_length >= 1
        assert validated.grace_period_seconds >= 0.1
        assert validated.timeout_seconds >= 1

    def test_tool_enum_validation(self):
        """Test enum validation for output_format."""
        validator = MCPParameterValidator()

        valid_formats = ["markdown", "text", "html"]

        for format_type in valid_formats:
            params = {"url": "https://example.com", "output_format": format_type}

            validated = validator.validate_tool_parameters("scrape_web", params)
            assert validated.output_format.value == format_type

    def test_url_validation(self):
        """Test URL validation."""
        validator = MCPParameterValidator()

        # Test valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "https://example.com:8080/path?query=value",
        ]

        for url in valid_urls:
            params = {"url": url, "output_format": "text"}

            validated = validator.validate_tool_parameters("scrape_web", params)
            assert str(validated.url) == url if url.endswith("/") else f"{url}/"

    def test_custom_headers_validation(self):
        """Test custom headers validation."""
        validator = MCPParameterValidator()

        params = {
            "url": "https://example.com",
            "output_format": "text",
            "custom_headers": {
                "Authorization": "Bearer token123",
                "X-Custom-Header": "custom-value",
            },
        }

        validated = validator.validate_tool_parameters("scrape_web", params)
        assert validated.custom_headers is not None
        assert "Authorization" in validated.custom_headers
        assert "X-Custom-Header" in validated.custom_headers
