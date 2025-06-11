from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData, GetPromptResult, Prompt, PromptArgument,
    PromptMessage, TextContent, Tool,
    INVALID_PARAMS, INTERNAL_ERROR
)
from mcp.shared.exceptions import McpError

import json
import sys
import asyncio
from pydantic import BaseModel, Field
from src.logger import Logger
from src.config import DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_CONTENT_LENGTH
import traceback

# Use absolute imports instead of relative imports
try:
    from src.scraper import extract_text_from_url
except ImportError:
    # Try alternative import paths
    import scraper
    extract_text_from_url = scraper.extract_text_from_url

import markdownify

logger = Logger(__name__)


class ScrapeArgs(BaseModel):
    """Parameters for web scraping."""
    url: str = Field(description="URL to scrape")
    max_length: int = Field(
        default=DEFAULT_MAX_CONTENT_LENGTH,
        description="Maximum number of characters to return.",
        gt=0,
        lt=1000000,
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


async def serve(custom_user_agent: str | None = None):
    logger.info("Starting MCP web scraper server (stdio mode)")
    server = Server("mcp-web-scraper")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        logger.info("Listing available tools")
        return [
            Tool(
                name="scrape_web",
                description="""Scrapes a webpage and extracts its main textual content as markdown.\nThis tool uses a headless browser to render the page with full JavaScript support,\nmaking it suitable for modern web applications.""",
                inputSchema=ScrapeArgs.model_json_schema(),
            )
        ]

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        logger.info("Listing available prompts")
        return [
            Prompt(
                name="scrape",
                description="Scrape a webpage and extract its main content as markdown",
                arguments=[
                    PromptArgument(
                        name="url",
                        description="URL to scrape",
                        required=True
                    )
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
        result = await extract_text_from_url(url)

        if result["status"] != "success":
            logger.error(
                f"Failed to scrape {url}: {result['error_message'] or result['status']}")
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"Failed to scrape {url}: {result['error_message'] or result['status']}"
            ))

        # Convert to Markdown if not already done
        content = result["extracted_text"]
        if content and result["status"] == "success":
            content = markdownify.markdownify(
                content, heading_style=markdownify.ATX)

        # Truncate if necessary
        if len(content) > args.max_length:
            logger.info(
                f"Truncating content from {len(content)} to {args.max_length} characters")
            content = content[:args.max_length] + \
                "\n\n[Content truncated due to length]"

        logger.info(
            f"Successfully scraped {url}, returning {len(content)} characters")
        return [TextContent(
            type="text",
            text=f"Scraped content from {result['final_url']}:\n\n{content}"
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
        result = await extract_text_from_url(url)

        if result["status"] != "success":
            logger.error(
                f"Failed to scrape {url} for prompt: {result['error_message'] or result['status']}")
            return GetPromptResult(
                description=f"Failed to scrape {url}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"Failed to scrape content from {url}: {result['error_message'] or result['status']}"
                        ),
                    )
                ],
            )

        # Convert to Markdown if needed
        content = result["extracted_text"]
        if content:
            content = markdownify.markdownify(
                content, heading_style=markdownify.ATX)

        logger.info(
            f"Successfully scraped {url} for prompt, returning {len(content)} characters")
        return GetPromptResult(
            description=f"Scraped content from {result['final_url']}",
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


def send_response(response):
    try:
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
        logger.debug(f"Sent response: {response}")
    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        logger.error(traceback.format_exc())


def main():
    logger.info("MCP server started, waiting for requests...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                logger.info("No more input, exiting MCP server.")
                break
            logger.debug(f"Received line: {line.strip()}")
            try:
                request = json.loads(line)
            except Exception as e:
                logger.error(f"Failed to parse JSON: {e}")
                send_response({"jsonrpc": "2.0", "error": {
                              "code": -32700, "message": "Parse error"}})
                continue

            # Handle initialize
            if request.get("method") == "initialize":
                logger.info("Received initialize request.")
                send_response({"jsonrpc": "2.0", "id": request.get(
                    "id"), "result": {"status": "ok"}})
                continue

            # Handle tool call
            if request.get("method") == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})
                logger.debug(f"Tool call: {name} with arguments: {arguments}")
                if name == "scrape_web":
                    url = arguments.get("url")
                    max_length = arguments.get("max_length")
                    if not url:
                        logger.error("Missing 'url' argument.")
                        send_response({
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {"code": -32602, "message": "URL parameter is required"}
                        })
                        continue
                    try:
                        # Call the scraper
                        result = asyncio.run(extract_text_from_url(url))
                        # If result is a string, wrap it in a dict
                        if isinstance(result, str):
                            if '[ERROR]' in result:
                                result = {
                                    "status": "error", "extracted_text": result, "final_url": url}
                            else:
                                result = {
                                    "status": "success", "extracted_text": result, "final_url": url}
                        # Truncate if max_length is set
                        if result["status"] == "success" and max_length:
                            result["extracted_text"] = result["extracted_text"][:max_length]
                        send_response({
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Exception in scrape_web: {e}")
                        logger.error(traceback.format_exc())
                        send_response({
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {"code": -32000, "message": str(e)}
                        })
                    continue
                else:
                    logger.error(f"Unknown tool name: {name}")
                    send_response({
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": "Unknown tool name"}
                    })
                    continue
            # Unknown method
            logger.error(f"Unknown method: {request.get('method')}")
            send_response({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32601, "message": "Unknown method"}
            })
        except Exception as e:
            logger.error(f"Fatal error in MCP server loop: {e}")
            logger.error(traceback.format_exc())
            send_response({
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Fatal error: {str(e)}"}
            })


if __name__ == "__main__":
    main()
