import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)
from src.logger import Logger
from src.models import ScrapeArgs
from src.models import ScrapeArgs as ScrapperScrapeArgs
from src.scraper.scrapper import Scraper

logger = Logger(__name__)

# Create a single, reusable Scraper instance
scraper_instance = Scraper()


def filter_none_values(data: dict) -> dict:
    """Remove None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}


async def extract_text_from_url_wrapper(url: str, **kwargs) -> dict:
    """Wrapper to run the sync scraper in a thread."""
    try:
        scrape_args = ScrapperScrapeArgs(
            url=url,
            **kwargs
        )
        return await asyncio.to_thread(scraper_instance.scrape, scrape_args)
    except Exception as e:
        logger.error(f"Error in extraction wrapper: {e}")
        return {"error": str(e)}


# --- Server Definition ---
server = Server("mcp-web-scraper")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lists available tools."""
    tools = [
        Tool(
            name="scrape_web",
            description="Scrapes a webpage and extracts its main content",
            inputSchema=ScrapeArgs.model_json_schema(),
        )
    ]
    logger.info(f"list_tools called, returning {len(tools)} tools.")
    return tools

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """Lists available prompts."""
    return [
        Prompt(
            name="scrape",
            description="Scrape content from a webpage",
            arguments=[
                PromptArgument(
                    name="url",
                    description="URL to scrape",
                    required=True,
                )
            ],
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Handles prompt requests."""
    logger.info(f"Get prompt request: {name} with arguments: {arguments}")
    if name != "scrape":
        raise McpError(
            ErrorData(code=INVALID_PARAMS, message=f"Unknown prompt: {name}")
        )

    url = arguments.get("url")
    if not url:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

    result = await extract_text_from_url_wrapper(url)

    if result.get("error"):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=result["error"]))

    content = result.get("content", "")
    final_url = result.get("final_url", url)

    return GetPromptResult(
        description=f"Scraped content from {final_url}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Here's the content from {final_url}:\n\n{content}",
                ),
            )
        ],
    )

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handles tool calls."""
    logger.info(f"Call to tool '{name}' with arguments: {arguments}")
    if name != "scrape_web":
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown tool: {name}"))

    try:
        args = ScrapeArgs(**filter_none_values(arguments))
    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

    result = await extract_text_from_url_wrapper(**args.model_dump())

    if result.get("error"):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=result["error"]))

    content = result.get("content", "")
    final_url = result.get("final_url", args.url)
    logger.info(
        f"Successfully scraped {final_url}, returning {len(content)} characters."
    )
    return [
        TextContent(type="text", text=f"Scraped content from {final_url}:\n\n{content}")
    ]


async def main():
    """Main function to run the server."""
    logger.info("Starting MCP server with stdio communication")
    options = server.create_initialization_options()
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, options)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Server crashed unexpectedly: {e}", exc_info=True)
