from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

from pydantic import BaseModel, Field
from src.logger import Logger
from src.config import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_GRACE_PERIOD_SECONDS,
    BROWSER_POOL_ENABLED,
    MCP_TRANSPORT,
    MCP_HTTP_HOST,
    MCP_HTTP_PORT,
)
from src.output_format_handler import OutputFormat

from src.scraper import extract_text_from_url


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
        default=DEFAULT_GRACE_PERIOD_SECONDS,
        description="Short grace period to allow JS to finish rendering (in seconds). Set to 0 to skip.",
        ge=0,
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
    click_selector: str | None = Field(
        default=None,
        description="If provided, click the element matching this selector after navigation and before extraction."
    )
    custom_elements_to_remove: list[str] | None = Field(
        default=None,
        description="Additional HTML elements (CSS selectors) to remove before extraction."
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


@asynccontextmanager
async def lifespan(app: FastMCP):
    """Manage browser pool lifecycle."""
    if BROWSER_POOL_ENABLED:
        from src.scraper.helpers.browser_pool import get_pool
        logger.info("Pre-warming browser pool...")
        await get_pool()
        logger.info("Browser pool ready")
    try:
        yield {}
    finally:
        if BROWSER_POOL_ENABLED:
            from src.scraper.helpers.browser_pool import shutdown_pool
            logger.info("Shutting down browser pool...")
            await shutdown_pool()


mcp = FastMCP(
    "mcp-web-scraper",
    host=MCP_HTTP_HOST,
    port=MCP_HTTP_PORT,
    lifespan=lifespan,
)


@mcp.tool(
    name="scrape_web",
    description="Scrapes a webpage and extracts its main content",
)
async def scrape_web(
    url: str,
    max_length: int | None = None,
    grace_period_seconds: float = DEFAULT_GRACE_PERIOD_SECONDS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str | None = None,
    wait_for_network_idle: bool = True,
    output_format: str = "markdown",
    click_selector: str | None = None,
    custom_elements_to_remove: list[str] | None = None,
) -> str:
    """Scrape a webpage and extract its main content."""
    try:
        fmt = OutputFormat(output_format)
    except ValueError:
        fmt = OutputFormat.MARKDOWN

    logger.info(f"Scraping URL: {url}")
    result = await extract_text_from_url(
        url,
        custom_timeout=timeout_seconds,
        custom_elements_to_remove=custom_elements_to_remove,
        grace_period_seconds=grace_period_seconds,
        max_length=max_length,
        user_agent=user_agent,
        wait_for_network_idle=wait_for_network_idle,
        output_format=fmt,
        click_selector=click_selector,
    )

    if result.get("error"):
        logger.error(f"Failed to scrape {url}: {result['error']}")
        raise McpError(ErrorData(
            code=INTERNAL_ERROR,
            message=f"Failed to scrape {url}: {result['error']}"
        ))

    content = result.get("content")
    logger.info(f"Successfully scraped {url}, returning {len(content) if content else 0} characters")
    return f"Scraped content from {result.get('final_url', url)}:\n\n{content}"


@mcp.prompt(
    name="scrape",
    description="Scrape a webpage and extract its main content",
)
async def scrape_prompt(url: str, output_format: str = "markdown") -> str:
    """Scrape a webpage for use as prompt context."""
    try:
        fmt = OutputFormat(output_format)
    except ValueError:
        logger.error(f"Invalid output_format: {output_format}, defaulting to MARKDOWN")
        fmt = OutputFormat.MARKDOWN

    logger.info(f"Scraping URL for prompt: {url}")
    result = await extract_text_from_url(url, output_format=fmt)

    if result.get("error"):
        logger.error(f"Failed to scrape {url} for prompt: {result['error']}")
        return f"Failed to scrape content from {url}: {result['error']}"

    content = result.get("content")
    logger.info(f"Successfully scraped {url} for prompt, returning {len(content) if content else 0} characters")
    return content


def serve():
    """Run the MCP server with the configured transport."""
    transport = MCP_TRANSPORT.lower()
    logger.info(f"Starting MCP web scraper server (transport={transport})")
    mcp.run(transport=transport)


if __name__ == "__main__":
    serve()
