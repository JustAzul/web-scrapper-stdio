"""
Refactored MCP server components following Single Responsibility Principle.

This module separates the concerns of the original MCP server into distinct services,
each with a single responsibility:
- MCPParameterValidator: Validates and converts request parameters
- MCPRequestHandler: Handles request routing and coordination
- MCPResponseFormatter: Formats responses for MCP protocol
"""

from typing import Any, Dict, List, Optional

from mcp.shared.exceptions import McpError
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    ErrorData,
    GetPromptResult,
    PromptMessage,
    TextContent,
)
from pydantic import BaseModel, Field, ValidationError, field_validator

from src.config import DEFAULT_TIMEOUT_SECONDS
from src.core.constants import (
    MAX_CONTENT_LENGTH,
    MAX_GRACE_PERIOD_VALIDATION,
    MAX_TIMEOUT_VALIDATION,
)
from src.logger import Logger
from src.output_format_handler import OutputFormat
from src.scraper.application.services.web_scraping_service import WebScrapingService
from src.utils import filter_none_values

logger = Logger(__name__)


class ScrapeArgs(BaseModel):
    """Parameters for web scraping."""

    url: str = Field(description="URL to scrape")
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum number of characters to return. If None, unlimited.",
        gt=0,
        lt=MAX_CONTENT_LENGTH,
    )
    grace_period_seconds: float = Field(
        default=2.0,
        description="Short grace period to allow JS to finish rendering (in seconds)",
        gt=0,
        lt=MAX_GRACE_PERIOD_VALIDATION,
    )
    timeout_seconds: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        description="Timeout in seconds for the page load.",
        gt=0,
        lt=MAX_TIMEOUT_VALIDATION,
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="Custom User-Agent string to use. If not provided, a random one will be used.",
    )
    wait_for_network_idle: bool = Field(
        default=True,
        description="Whether to wait for network activity to settle before extracting content.",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Desired output format: markdown, text, or html.",
    )
    click_selector: Optional[str] = Field(
        default=None,
        description="If provided, click the element matching this selector after navigation and before extraction.",
    )
    custom_elements_to_remove: Optional[List[str]] = Field(
        default=None,
        description="Additional HTML elements (CSS selectors) to remove before extraction.",
    )

    @field_validator("url", "click_selector")
    def prevent_malicious_input(cls, v):
        """Prevent injection of malicious characters."""
        if v is None:
            return v
        malicious_chars = ["<", ">", "'", '"', ";", "&", "|", "{", "}"]
        if any(char in v for char in malicious_chars):
            raise ValueError("Malicious characters detected in input")
        return v


class MCPParameterValidator:
    """
    Service responsible for validating and converting MCP request parameters.

    Single Responsibility: Parameter validation and type conversion
    """

    def validate_tool_parameters(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> ScrapeArgs:
        """
        Validate and convert tool parameters to strongly-typed objects.

        Args:
            tool_name: Name of the tool being called
            arguments: Raw arguments from MCP request

        Returns:
            Validated ScrapeArgs object

        Raises:
            McpError: If validation fails or tool is unknown
        """
        if tool_name != "scrape_web":
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message=f"Unknown tool: {tool_name}",
                )
            )

        # Create a filtered copy of arguments without mutating the original
        filtered_arguments = filter_none_values(arguments)

        try:
            return ScrapeArgs(**filtered_arguments)
        except ValidationError as e:
            logger.error(f"Invalid parameters: {e}")
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

    def validate_prompt_parameters(
        self, prompt_name: str, arguments: Optional[Dict[str, Any]]
    ) -> ScrapeArgs:
        """
        Validate and convert prompt parameters.

        Args:
            prompt_name: Name of the prompt being called
            arguments: Raw arguments from MCP request

        Returns:
            Validated ScrapeArgs object

        Raises:
            McpError: If validation fails or prompt is unknown
        """
        if prompt_name != "scrape":
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message=f"Unknown prompt: {prompt_name}",
                )
            )

        if not arguments or "url" not in arguments:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

        # Create a copy of arguments for processing
        validated_args = arguments.copy()

        # Handle output_format conversion
        output_format = validated_args.get("output_format", OutputFormat.MARKDOWN)
        if isinstance(output_format, str):
            try:
                output_format = OutputFormat(output_format)
            except ValueError:
                logger.error(
                    f"Invalid output_format: {output_format}, defaulting to MARKDOWN"
                )
                output_format = OutputFormat.MARKDOWN

        validated_args["output_format"] = output_format

        # Create and return ScrapeArgs object
        try:
            return ScrapeArgs(**validated_args)
        except Exception as e:
            logger.error(f"Parameter validation failed: {e}")
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))


class MCPResponseFormatter:
    """
    Service responsible for formatting responses according to MCP protocol.

    Single Responsibility: Response formatting and serialization
    """

    def format_tool_response(self, scraper_result: Dict[str, Any]) -> List[TextContent]:
        """
        Format scraper result as MCP tool response.

        Args:
            scraper_result: Result from scraper service

        Returns:
            List of TextContent objects for MCP response
        """
        content = scraper_result.get("content", "")
        final_url = scraper_result.get("final_url", "")

        logger.info(
            f"Formatting tool response: {len(content) if content else 0} characters"
        )

        return [
            TextContent(
                type="text", text=f"Scraped content from {final_url}:\n\n{content}"
            )
        ]

    def format_prompt_response(self, scraper_result: Dict[str, Any]) -> GetPromptResult:
        """
        Format scraper result as MCP prompt response.

        Args:
            scraper_result: Result from scraper service

        Returns:
            GetPromptResult object for MCP response
        """
        content = scraper_result.get("content", "")
        final_url = scraper_result.get("final_url", "")

        logger.info(
            f"Formatting prompt response: {len(content) if content else 0} characters"
        )

        return GetPromptResult(
            description=f"Scraped content from {final_url}",
            messages=[
                PromptMessage(
                    role="user", content=TextContent(type="text", text=content)
                )
            ],
        )

    def format_error_response(self, url: str, error_message: str) -> GetPromptResult:
        """
        Format error as MCP prompt response.

        Args:
            url: URL that failed to scrape
            error_message: Error description

        Returns:
            GetPromptResult with error information
        """
        logger.error(f"Formatting error response for {url}: {error_message}")

        return GetPromptResult(
            description=f"Failed to scrape {url}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Failed to scrape content from {url}: {error_message}",
                    ),
                )
            ],
        )


class MCPRequestHandler:
    """
    Service responsible for handling MCP requests and coordinating between services.

    Single Responsibility: Request handling and service coordination
    """

    def __init__(
        self,
        scraper_service: WebScrapingService,
        validator: MCPParameterValidator,
        formatter: MCPResponseFormatter,
    ):
        """
        Initialize the request handler with dependencies.

        Args:
            scraper_service: Service for performing web scraping
            validator: Parameter validation service
            formatter: Response formatting service
        """
        self.scraper_service = scraper_service
        self.validator = validator
        self.formatter = formatter

    async def handle_tool_request(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """
        Handle MCP tool request.

        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments

        Returns:
            Formatted tool response

        Raises:
            McpError: If request processing fails
        """
        logger.info(f"Handling tool request: {tool_name} with arguments: {arguments}")

        # Validate parameters
        validated_args = self.validator.validate_tool_parameters(tool_name, arguments)

        # Ensure URL is provided
        if not validated_args.url:
            logger.error("URL is required")
            raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

        # Execute scraping
        logger.info(f"Scraping URL: {validated_args.url}")
        try:
            # This call might fail if scraping fails
            scraper_result = await self._execute_scraping(validated_args)
        except Exception as e:
            logger.error(f"Scraping execution failed: {e}", exc_info=True)
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"An unexpected error occurred: {e}",
                )
            )

        # Format and return response
        return self.formatter.format_tool_response(scraper_result)

    async def handle_prompt_request(
        self, prompt_name: str, arguments: Optional[Dict[str, Any]]
    ) -> GetPromptResult:
        """
        Handle MCP prompt request.

        Args:
            prompt_name: Name of the prompt being called
            arguments: Prompt arguments

        Returns:
            Formatted prompt response
        """
        logger.info(
            f"Handling prompt request: {prompt_name} with arguments: {arguments}"
        )

        # Validate parameters
        try:
            validated_args = self.validator.validate_prompt_parameters(
                prompt_name, arguments
            )
            scraper_result = await self._execute_scraping(validated_args)
        except McpError as e:
            # Propagate MCP-specific errors (like validation) directly
            raise e
        except Exception as e:
            logger.error(f"Scraping execution failed: {e}", exc_info=True)
            # For prompts, we can format the error nicely instead of raising
            return self.formatter.format_error_response(
                url=arguments.get("url", "unknown"), error_message=str(e)
            )

        return self.formatter.format_prompt_response(scraper_result)

    async def _execute_scraping(self, args: ScrapeArgs) -> Dict[str, Any]:
        """
        Helper method to execute scraping and handle potential errors.
        """
        # The WebScrapingService now handles the entire workflow
        result = await self.scraper_service.scrape_url(
            **args.model_dump(exclude_none=True)
        )
        return result
