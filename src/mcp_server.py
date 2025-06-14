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
from src.logger import Logger
from src.config import DEFAULT_TIMEOUT_SECONDS
from src.output_format_handler import OutputFormat

# Use absolute imports instead of relative imports
try:
    from src.scraper import extract_text_from_url
except ImportError:
    # Try alternative import paths
    import scraper
    extract_text_from_url = scraper.extract_text_from_url


logger = Logger(__name__)


class ScrapeArgs(BaseModel):
    """Parameters for web scraping."""
    url: str = Field(description="URL to scrape")
    max_length: int | None = Field(
        default=None,
        description="Maximum number of characters to return. If None, unlimited.",
        gt=0,
        lt=1000000,
    )
    grace_period_seconds: float = Field(
        default=2.0,
        description="Short grace period to allow JS to finish rendering (in seconds)",
        gt=0,
        lt=30,
    )
    timeout_seconds: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        description="Timeout in seconds for the page load.",
        gt=0,
        lt=120,
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


async def mcp_extract_text_map(url: str, *args, **kwargs) -> dict:
    """
    MCP-specific wrapper for extract_text_from_url that returns a dict with status, extracted_text, and final_url.
    """
    result = await extract_text_from_url(url, *args, **kwargs)
    if result.get("error"):
        return {
            "status": "error",
            "extracted_text": None,
            "final_url": result.get("final_url", url),
            "title": result.get("title"),
            "error_message": result["error"]
        }
    return {
        "status": "success",
        "extracted_text": result.get("content"),
        "final_url": result.get("final_url", url),
        "title": result.get("title"),
        "error_message": None
    }


async def serve(custom_user_agent: str | None = None):
    logger.info("Starting MCP web scrapper server (stdio mode)")
    server = Server("mcp-web-scrapper")

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

        try:
            args = ScrapeArgs(**arguments)
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
            custom_elements_to_remove=None,
            grace_period_seconds=args.grace_period_seconds,
            max_length=args.max_length,
            user_agent=args.user_agent,
            wait_for_network_idle=args.wait_for_network_idle,
            output_format=args.output_format,
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
                logger.error(f"Invalid output_format: {output_format}, defaulting to MARKDOWN")
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
