import pytest
import os
import sys
import time
import asyncio
from mcp import ClientSession, StdioServerParameters # Import StdioServerParameters
from mcp.client.stdio import stdio_client # Correct import for the stdio client function
from urllib.parse import urlparse

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import the helper function for finding articles from test_api.py
from .test_api import find_article_link_on_page

# Define MCP Server details (use service name from docker-compose)
# MCP_SERVER_ADDRESS is not needed for stdio client
MCP_TOOL_NAME = "WEBPAGE_TEXT_EXTRACTOR"

# Helper function to make MCP tool calls
async def make_mcp_tool_call(tool_name: str, arguments: dict) -> dict:
    """
    Connects to the MCP server and calls the specified tool using stdio.

    Args:
        tool_name: Name of the MCP tool to call
        arguments: Dictionary of arguments to pass to the tool

    Returns:
        Dictionary containing the tool's response
    """
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp_server.py"] # Pass the script as an argument to python
    )
    print(f"\nCreating MCP stdio session with command: {server_params.command} {server_params.args}")
    try:
        # Use stdio_client context manager to get read/write streams
        async with stdio_client(server_params) as (read, write):
            # Pass streams to ClientSession
            async with ClientSession(read, write) as session:
                print(f"MCP stdio session initialized. Calling tool '{tool_name}'...")
                # Initialize the session (important step)
                await asyncio.wait_for(session.initialize(), timeout=30)
                print("MCP session initialized.")

                # Add timeout to the tool call
                result_obj = await asyncio.wait_for(
                    session.call_tool(name=tool_name, arguments=arguments),
                    timeout=60
                )
                print(f"MCP Tool '{tool_name}' returned: {result_obj}")
                
                # Extract the actual result data from the content field
                if result_obj.content and len(result_obj.content) > 0:
                    # The content field contains TextContent objects. Get the text from the first one.
                    result_text = result_obj.content[0].text
                    # Parse the JSON string in the text field
                    import json
                    result = json.loads(result_text)
                    return result
                else:
                    raise ValueError("Empty content in MCP tool result")
                
    except asyncio.TimeoutError:
        pytest.fail(f"MCP call timed out after 60 seconds. The operation may be hanging.")
    except ConnectionRefusedError:
        # This error might not apply directly to stdio, but keep for safety
        pytest.fail(f"MCP Connection Refused: Could not start server process.")
    except Exception as e:
        pytest.fail(f"MCP tool call via stdio failed with unexpected error: {e}")
    return {}

# --- MCP Basic Test Cases ---

@pytest.mark.asyncio
async def test_mcp_extract_example_com():
    """Test basic extraction from example.com via MCP"""
    url = "https://example.com"
    result = await make_mcp_tool_call(MCP_TOOL_NAME, {"url": url})

    assert result["status"] == "success"
    assert "Example Domain" in result["extracted_text"]
    assert result["error_message"] is None
    assert result["final_url"] in [url, url + '/']
    time.sleep(1)  # Small delay to prevent overloading servers

@pytest.mark.asyncio
async def test_mcp_extract_redirect_success():
    """Test extraction after a successful redirect via MCP."""
    urls = ["https://search.app/1jGF2", "https://search.app/vXQf9"]
    for url in urls:
        result = await make_mcp_tool_call(MCP_TOOL_NAME, {"url": url})
        assert result["status"] == "success"
        assert result["extracted_text"]
        assert result["error_message"] is None
        assert result["final_url"] != url
        time.sleep(1)

@pytest.mark.asyncio
async def test_mcp_extract_invalid_url_404():
    """Test MCP handling of an invalid URL that should result in an error."""
    url = "https://httpbin.org/status/404"
    result = await make_mcp_tool_call(MCP_TOOL_NAME, {"url": url})

    assert result["status"] == "error_fetching"
    assert "404" in result["error_message"]
    assert result["extracted_text"] == ""
    assert result["final_url"] == url
    time.sleep(1)

@pytest.mark.asyncio
async def test_mcp_extract_invalid_redirect_404():
    """Test MCP handling of a redirect.
    Note: This URL previously returned a 404 after redirect, but now appears to be valid.
    We've updated the test to validate the redirect behavior instead."""
    url = "https://search.app/CmeVX"
    result = await make_mcp_tool_call(MCP_TOOL_NAME, {"url": url})

    # Check redirect happened successfully
    assert result["status"] == "success"
    assert result["extracted_text"]
    assert result["error_message"] is None
    assert result["final_url"] != url
    time.sleep(1)

@pytest.mark.asyncio
async def test_mcp_extract_nonexistent_domain():
    """Test MCP handling of a completely non-existent domain."""
    url = "https://nonexistent-domain-for-testing-12345.com/somepage"
    result = await make_mcp_tool_call(MCP_TOOL_NAME, {"url": url})

    assert result["status"] == "error_fetching"
    assert "resolve" in result["error_message"] or "connect" in result["error_message"]
    assert result["extracted_text"] == ""
    assert result["final_url"] == url
    time.sleep(1)

# --- Dynamic Extraction Tests via MCP ---
# Using a smaller subset for MCP to reduce test time

@pytest.mark.asyncio
@pytest.mark.parametrize("domain_info", [
    # Use a more limited subset for MCP to keep runtime manageable
    ("forbes.com", "/innovation/"),
    ("dev.to", "/"),
])
async def test_mcp_dynamic_article_extraction(domain_info):
    """Tests dynamic article extraction using the MCP tool with a subset of domains."""
    domain, start_path = domain_info
    start_url = f"https://{domain}{start_path or '/'}"
    print(f"\nTesting dynamic extraction via MCP for: {domain} (starting from {start_url})")

    article_url = find_article_link_on_page(start_url)
    if not article_url:
        pytest.skip(f"Could not dynamically find an article link on {start_url} for MCP test")
        return

    print(f"Found article link: {article_url}")
    print(f"Calling MCP tool to extract text...")

    try:
        result = await make_mcp_tool_call(MCP_TOOL_NAME, {"url": article_url})
        print(f"MCP Result Status: {result['status']}")
        if result["status"] != "success":
             print(f"MCP Error: {result['error_message']}")

        assert result["status"] == "success", f"Expected status 'success' but got '{result['status']}' for {article_url}"
        assert result["extracted_text"], f"Expected non-empty extracted_text for {article_url}"
        assert len(result["extracted_text"]) >= 100, f"Extracted text too short ({len(result['extracted_text'])} chars) for {article_url}"
        assert result["error_message"] is None, f"Expected null error_message for {article_url}"
        requested_parsed = urlparse(article_url)
        final_parsed = urlparse(result["final_url"])
        assert final_parsed.netloc.replace("www.", "") == requested_parsed.netloc.replace("www.", ""), \
               f"Expected final_url '{result['final_url']}' to be on the same domain as requested URL '{article_url}' (ignoring www.)"

    except Exception as e:
        pytest.fail(f"An unexpected error occurred during MCP call or assertion: {e}. URL: {article_url}")

    time.sleep(2) 