from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData, GetPromptResult, Prompt, PromptArgument,
    PromptMessage, TextContent, Tool,
    INVALID_PARAMS, INTERNAL_ERROR
)
from mcp.shared.exceptions import McpError

import asyncio
from pydantic import BaseModel, Field
from src.core.constants import (
    DEFAULT_GRACE_PERIOD_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_GRACE_PERIOD_VALIDATION,
    MAX_TIMEOUT_VALIDATION,
)
from src.logger import Logger
from src.scraper.scrapper import Scraper
from src.scraper.api.handlers.output_formatter import OutputFormat
from src.models import ScrapeArgs as ScrapperScrapeArgs


logger = Logger(__name__)


class ScrapeArgs(BaseModel):
    """Parameters for web scraping."""
    url: str = Field(description="URL to scrape")
    max_length: int | float | None = Field(
        default=None,
        description="Maximum number of characters to return. If None, unlimited.",
        gt=0,
        lt=1000000,
    )
    grace_period_seconds: float = Field(
        default=DEFAULT_GRACE_PERIOD_SECONDS,
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
    user_agent: str | None = Field(
        default=None,
        description="Custom User-Agent string to use. If not provided, a random one will be used."
    )
    wait_for_network_idle: bool = Field(
        default=True,
        description="Whether to wait for network activity to settle before extracting content."
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Desired output format: markdown, text, or html."
    )
    click_selector: str | None = Field(
        default=None,
        description="If provided, click the element matching this selector after navigation and before extraction."
    )
    custom_elements_to_remove: list[str] | None = Field(
        default=None,
        description="Additional HTML elements (CSS selectors) to remove before extraction."
    )


def filter_none_values(data: dict) -> dict:
    """Remove None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}


async def extract_text_from_url(url: str, **kwargs) -> dict:
    """
    Wrapper function to maintain compatibility with production MCP server.
    Converts the current Scraper class to the expected interface.
    """
    try:
        # Convert kwargs to ScrapeArgs
        max_len = kwargs.get('max_length')
        if max_len is not None:
            max_len = int(max_len)

        scrape_args = ScrapperScrapeArgs(
            url=url,
            max_length=max_len,
            grace_period_seconds=kwargs.get('grace_period_seconds', DEFAULT_GRACE_PERIOD_SECONDS),
            timeout_seconds=kwargs.get('custom_timeout', DEFAULT_TIMEOUT_SECONDS),
            user_agent=kwargs.get('user_agent'),
            wait_for_network_idle=kwargs.get('wait_for_network_idle', True),
            output_format=kwargs.get('output_format', OutputFormat.MARKDOWN),
            click_selector=kwargs.get('click_selector'),
            custom_elements_to_remove=kwargs.get('custom_elements_to_remove')
        )
        
        # Use the Scraper class
        scraper = Scraper()
        result = await scraper.scrape(scrape_args)
        
        return result
        
    except Exception as e:
        return {
            "title": None,
            "final_url": url,
            "content": None,
            "error": str(e)
        }


async def serve(custom_user_agent: str | None = None):
    logger.info("Starting MCP web scraper server (stdio mode)")
    server = Server("mcp-web-scraper")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        logger.info("Listing available tools")
        return [
            Tool(
                name="scrape_web",
                description="Scrapes a webpage and extracts its main content",
                inputSchema=ScrapeArgs.model_json_schema(),
            )
        ]

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        logger.info("Listing available prompts")
        return [
            Prompt(
                name="scrape",
                description="Scrape a webpage and extract its main content",
                arguments=[
                    PromptArgument(
                        name="url",
                        description="URL to scrape",
                        required=True,
                    ),
                    PromptArgument(
                        name="output_format",
                        description="Desired output format: markdown, text, or html",
                        required=False,
                    ),
                ],
            )
        ]

    @server.call_tool()
    async def call_tool(name, arguments: dict) -> list[TextContent]:
        logger.info(f"Call to tool '{name}' with arguments: {arguments}")
        if name != "scrape_web":
            raise McpError(ErrorData(code=INVALID_PARAMS,
                           message=f"Unknown tool: {name}"))

        # Create a filtered copy of arguments without mutating the original
        filtered_arguments = filter_none_values(arguments)

        try:
            args = ScrapeArgs(**filtered_arguments)
        except ValueError as e:
            logger.error(f"Invalid parameters: {e}")
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        url = args.url
        if not url:
            logger.error("URL is required")
            raise McpError(ErrorData(code=INVALID_PARAMS,
                           message="URL is required"))

        # Call our existing scraper function
        logger.info(f"Scraping URL: {url}")
        result = await extract_text_from_url(
            url,
            custom_timeout=args.timeout_seconds,
            custom_elements_to_remove=args.custom_elements_to_remove,
            grace_period_seconds=args.grace_period_seconds,
            max_length=args.max_length,
            user_agent=args.user_agent,
            wait_for_network_idle=args.wait_for_network_idle,
            output_format=args.output_format,
            click_selector=args.click_selector,
        )

        if result.get("error"):
            logger.error(
                f"Failed to scrape {url}: {result['error']}")
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"Failed to scrape {url}: {result['error']}"
            ))

        content = result.get("content")

        logger.info(
            f"Successfully scraped {url}, returning {len(content) if content else 0} characters")
        return [TextContent(
            type="text",
            text=f"Scraped content from {result.get('final_url', url)}:\n\n{content}"
        )]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
        logger.info(f"Get prompt '{name}' with arguments: {arguments}")
        if name != "scrape":
            raise McpError(ErrorData(code=INVALID_PARAMS,
                           message=f"Unknown prompt: {name}"))

        if not arguments or "url" not in arguments:
            logger.error("URL is required for scrape prompt")
            raise McpError(ErrorData(code=INVALID_PARAMS,
                           message="URL is required"))

        url = arguments["url"]
        logger.info(f"Scraping URL for prompt: {url}")
        output_format = arguments.get("output_format", OutputFormat.MARKDOWN)
        if isinstance(output_format, str):
            try:
                output_format = OutputFormat(output_format)
            except ValueError:
                logger.error(
                    f"Invalid output_format: {output_format}, defaulting to MARKDOWN")
                output_format = OutputFormat.MARKDOWN
        result = await extract_text_from_url(url, output_format=output_format)

        if result.get("error"):
            logger.error(
                f"Failed to scrape {url} for prompt: {result['error']}")
            return GetPromptResult(
                description=f"Failed to scrape {url}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"Failed to scrape content from {url}: {result['error']}"
                        ),
                    )
                ],
            )

        content = result.get("content")

        logger.info(
            f"Successfully scraped {url} for prompt, returning {len(content) if content else 0} characters")
        return GetPromptResult(
            description=f"Scraped content from {result.get('final_url', url)}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=content
                    )
                )
            ],
        )

    options = server.create_initialization_options()
    logger.info('About to enter stdio_server context')
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Starting MCP server with stdio communication")
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
        logger.info("server.run() completed")

if __name__ == "__main__":
    asyncio.run(serve()) 