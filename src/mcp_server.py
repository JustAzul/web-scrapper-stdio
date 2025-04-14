import asyncio
from mcp.server import FastMCP  # Import the correct FastMCP class
import os
import sys

# Ensure the src directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the core scraper function - use local import
try:
    # When running as a module
    from src.scraper import extract_text_from_url
except ImportError:
    # When running as a script in the src directory
    from scraper import extract_text_from_url

# Define a server name (can be anything descriptive)
SERVER_NAME = "webscraper_tool_server"
print(f"Initializing MCP Server: {SERVER_NAME}")

# Initialize the MCP server instance
mcp_instance = FastMCP(SERVER_NAME)  # Use FastMCP instead of mcp_sdk

@mcp_instance.tool()
async def WEBPAGE_TEXT_EXTRACTOR(url: str) -> dict:
    """
    Fetches the primary text content from a given public web URL.
    Uses headless browsing to handle JavaScript-heavy pages.
    Ideal for extracting articles, blog posts, or documentation.

    Args:
        url: The fully qualified URL of the web page to scrape.

    Returns:
        A dictionary containing:
        - extracted_text (str): The main textual content. Empty if error.
        - status (str): Outcome ("success", "error_fetching", etc.).
        - error_message (str | None): Error details if status != "success".
        - final_url (str): URL after redirects.
    """
    print(f"MCP Tool WEBPAGE_TEXT_EXTRACTOR called with URL: {url}")
    try:
        # Call the existing async scraper function
        result = await extract_text_from_url(url)
        print(f"MCP Tool WEBPAGE_TEXT_EXTRACTOR result status: {result.get('status')}")
        return result
    except Exception as e:
        # Generic fallback error handling for the tool
        print(f"MCP Tool WEBPAGE_TEXT_EXTRACTOR unexpected error: {e}")
        return {
            "extracted_text": "",
            "status": "error_unknown",
            "error_message": f"An unexpected error occurred in the MCP tool wrapper: {str(e)}",
            "final_url": url # Best guess for final URL on error
        }

# Entry point to run the server
if __name__ == "__main__":
    print(f"Starting MCP Server {SERVER_NAME}...")
    mcp_instance.run()
    print(f"MCP Server {SERVER_NAME} stopped.") 