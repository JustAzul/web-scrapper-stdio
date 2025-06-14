import pytest
import random
from src.mcp_server import mcp_extract_text_map
from src.scraper.helpers.browser import USER_AGENTS
from src.output_format_handler import OutputFormat


@pytest.mark.asyncio
async def test_call_tool_with_string_result():
    arguments = {
        "url": "http://example.com",
        "max_length": None,
        "timeout_seconds": 30,
        "wait_for_network_idle": True,
        "user_agent": random.choice(USER_AGENTS),
        "output_format": OutputFormat.TEXT,
    }
    result = await mcp_extract_text_map(
        arguments["url"],
        max_length=arguments["max_length"],
        user_agent=arguments["user_agent"],
        wait_for_network_idle=arguments["wait_for_network_idle"],
        output_format=arguments["output_format"],
    )
    assert isinstance(result, dict)
    assert "status" in result
    assert "extracted_text" in result
    assert "final_url" in result


@pytest.mark.asyncio
async def test_call_tool_with_string_output_format_text():
    arguments = {
        "url": "http://example.com",
        "max_length": None,
        "timeout_seconds": 30,
        "wait_for_network_idle": True,
        "user_agent": random.choice(USER_AGENTS),
        "output_format": "text",  # Pass as string, as MCP protocol would
    }
    result = await mcp_extract_text_map(
        arguments["url"],
        max_length=arguments["max_length"],
        user_agent=arguments["user_agent"],
        wait_for_network_idle=arguments["wait_for_network_idle"],
        output_format=arguments["output_format"],
    )
    assert isinstance(result, dict)
    assert result["status"] == "success"
    content = result["extracted_text"]
    print("\n[DEBUG] Output for string output_format='text':\n", content)
    # Should be plain text, not markdown or HTML
    assert not content.strip().startswith("#"), "Output is markdown, not plain text!"
    assert "Example Domain" in content
