import pytest
from src.mcp_server import mcp_extract_text_map


@pytest.mark.asyncio
async def test_call_tool_with_string_result():
    arguments = {
        "url": "http://example.com",
        "max_length": None,
        "timeout_seconds": 30,
        "wait_for_network_idle": True
    }
    result = await mcp_extract_text_map(arguments["url"], max_length=arguments["max_length"])
    assert isinstance(result, dict)
    assert "status" in result
    assert "extracted_text" in result
    assert "final_url" in result
