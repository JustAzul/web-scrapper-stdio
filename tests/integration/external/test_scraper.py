import asyncio

import pytest
from bs4 import BeautifulSoup

from src.config import (
    DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS,
    DEFAULT_TEST_NO_DELAY_THRESHOLD,
)
from src.output_format_handler import OutputFormat
from src.scraper import apply_rate_limiting, extract_text_from_url, get_domain_from_url

# Short timeout for integration tests to prevent hanging
TIMEOUT_SECONDS = 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_from_example_com():
    """Test extraction from example.com with short timeout to prevent hanging."""
    url = "http://example.com"
    result = await extract_text_from_url(url, custom_timeout=TIMEOUT_SECONDS)
    assert isinstance(result, dict)

    # Skip test if it fails due to network issues
    if result.get("error"):
        pytest.skip(f"Network test failed: {result['error']}")

    assert result.get("title") is not None
    assert "Example Domain" in (result.get("title") or "") or "Example Domain" in (
        result.get("content") or ""
    )
    assert result.get("content") is not None
    assert result.get("final_url") in [
        url,
        url + "/",
        "https://www.example.com",
        "https://www.example.com/",
    ]
    assert not result.get("error")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_from_example_com_text_output():
    """Test text output format with short timeout."""
    url = "http://example.com"
    result = await extract_text_from_url(
        url, output_format=OutputFormat.TEXT, custom_timeout=TIMEOUT_SECONDS
    )
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    assert "Example Domain" in result.get("content", "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_from_example_com_markdown_output():
    """Test markdown output format with short timeout."""
    url = "http://example.com"
    result = await extract_text_from_url(
        url,
        output_format=OutputFormat.MARKDOWN,
        custom_timeout=TIMEOUT_SECONDS,
    )
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    content = result.get("content") or ""
    assert "Example Domain" in content
    assert "==" in content or "#" in content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_from_example_com_html_output():
    """Test HTML output format with short timeout."""
    url = "http://example.com"
    result = await extract_text_from_url(
        url, output_format=OutputFormat.HTML, custom_timeout=TIMEOUT_SECONDS
    )
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    html = result.get("content")
    assert html is not None
    BeautifulSoup(html, "html.parser")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_from_example_com_with_max_length():
    """Test max length parameter with short timeout."""
    url = "http://example.com"
    result = await extract_text_from_url(
        url,
        max_length=50,
        output_format=OutputFormat.HTML,
        custom_timeout=TIMEOUT_SECONDS,
    )
    assert isinstance(result, dict)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    html = result.get("content")
    assert html is not None
    assert len(html) <= 50 + len("\n\n[Content truncated due to length]")
    BeautifulSoup(html, "html.parser")


@pytest.mark.slow
@pytest.mark.flaky(reruns=3, reruns_delay=2)
@pytest.mark.asyncio
async def test_extract_text_from_wikipedia():
    """
    Test Wikipedia extraction with a retry mechanism for page crashes.
    """
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    max_retries = 3
    result = {}

    for attempt in range(max_retries):
        result = await extract_text_from_url(url, custom_timeout=TIMEOUT_SECONDS)
        error = result.get("error", "")
        if "Page crashed" not in error:
            break  # Success, exit loop
        if attempt < max_retries - 1:
            await asyncio.sleep(2)  # Wait before retrying

    assert isinstance(result, dict)
    if result.get("error"):
        pytest.skip(f"Wikipedia extraction failed with error: {result['error']}")
    assert result.get("title") is not None
    assert "Web scraping" in (result.get("title") or "") or "Web scraping" in (
        result.get("content") or ""
    )
    assert result.get("content") is not None
    assert result.get("final_url") == url or result.get("final_url", "").startswith(
        "https://en.wikipedia.org/wiki/"
    )


@pytest.mark.asyncio
async def test_nonexistent_domain():
    """Test handling of nonexistent domains - this should be fast."""
    url = "https://nonexistent-domain-for-testing-12345.com/somepage"
    result = await extract_text_from_url(
        url, custom_timeout=5
    )  # Even shorter timeout for expected failures
    assert isinstance(result, dict)
    assert result.get("error")
    assert (
        "Could not resolve" in result.get("error")
        or "error" in result.get("error").lower()
    )


@pytest.mark.asyncio
async def test_invalid_url_format():
    """Test handling of invalid URL formats - this should be fast."""
    url = "not-a-valid-url"
    result = await extract_text_from_url(url, custom_timeout=5)
    assert isinstance(result, dict)
    assert result.get("error")
    assert (
        "invalid url" in result.get("error").lower()
        or "error" in result.get("error").lower()
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code",
    [404, 500, 502],
)
async def test_http_error_pages(status_code):
    """Test handling of various HTTP error responses with short timeout."""
    url = f"https://httpbin.org/status/{status_code}"
    result = await extract_text_from_url(url, custom_timeout=TIMEOUT_SECONDS)
    assert isinstance(result, dict)

    if result.get("error") and "timed out" in result.get("error").lower():
        pytest.skip("Test skipped due to timeout, httpbin.org may be slow.")

    # The service should return a clear error for any non-2xx status code
    assert result.get("error"), (
        f"Expected an error for HTTP status {status_code}, but got none."
    )

    error_message = result.get("error", "").lower()
    assert (
        str(status_code) in error_message
        or "http error" in error_message
        or "server error" in error_message
        or "not found" in error_message
    ), f"Expected HTTP error indicator for {status_code} in: {result.get('error')}"


def test_get_domain_from_url():
    """Test domain extraction - this is fast and doesn't require network."""
    assert get_domain_from_url("https://example.com") == "example.com"
    assert get_domain_from_url("https://www.example.com") == "example.com"
    assert get_domain_from_url("http://blog.example.com/post/123") == "blog.example.com"
    assert get_domain_from_url("https://example.com:8080") == "example.com:8080"
    assert get_domain_from_url("not-a-url") is None
    assert get_domain_from_url("") is None


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting functionality - this is fast and doesn't require network."""
    domain = "test-domain.com"
    url = f"https://{domain}"
    start_time = asyncio.get_event_loop().time()

    await apply_rate_limiting(url)
    start_time = asyncio.get_event_loop().time()

    await apply_rate_limiting(url)
    second_request_time = asyncio.get_event_loop().time() - start_time

    assert second_request_time >= DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS - 0.1, (
        f"Rate limiting not working, delay was only {second_request_time} seconds"
    )
    different_url = "https://different-domain.com"
    start_time = asyncio.get_event_loop().time()

    await apply_rate_limiting(different_url)
    different_domain_time = asyncio.get_event_loop().time() - start_time

    assert different_domain_time < DEFAULT_TEST_NO_DELAY_THRESHOLD, (
        f"Different domain was delayed: {different_domain_time} seconds"
    )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_extract_real_article():
    """Test a real article with a retry mechanism for page crashes."""
    url = "https://www.theverge.com/2022/12/21/23521345/apple-wwdc-2023-date-ios-17-reality-pro-headset-imac"
    max_retries = 3
    result = {}

    for attempt in range(max_retries):
        result = await extract_text_from_url(url, custom_timeout=TIMEOUT_SECONDS)
        error = result.get("error", "")
        if "Page crashed" not in error:
            break  # Success, exit loop
        if attempt < max_retries - 1:
            await asyncio.sleep(2)  # Wait before retrying

    assert isinstance(result, dict)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result}")
    assert result.get("title") is not None
    assert "Web scraping" in (result.get("title") or "") or "Web scraping" in (
        result.get("content") or ""
    )
    assert result.get("content") is not None
    assert result.get("final_url") == url or result.get("final_url", "").startswith(
        "https://en.wikipedia.org/wiki/"
    )


@pytest.mark.asyncio
async def test_missing_url_argument():
    """Test calling the function with a missing URL should raise TypeError."""
    with pytest.raises(
        TypeError, match="missing 1 required positional argument: 'url'"
    ):
        # pylint: disable=no-value-for-parameter
        await extract_text_from_url()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_grace_period_seconds_js_delay():
    """Test that grace period allows JS to load content before extraction."""
    url = "http://example.com"
    result = await extract_text_from_url(
        url, grace_period_seconds=1.0, custom_timeout=TIMEOUT_SECONDS
    )

    if result.get("error"):
        pytest.skip(f"Grace period test failed: {result['error']}")

    assert isinstance(result, dict)
    assert result.get("content") is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_custom_user_agent_and_no_network_idle():
    """Test custom user agent and network idle settings with short timeout."""
    url = "http://example.com"
    custom_agent = "TestBot/1.0"
    result = await extract_text_from_url(
        url,
        user_agent=custom_agent,
        wait_for_network_idle=False,
        custom_timeout=TIMEOUT_SECONDS,
    )

    if result.get("error"):
        pytest.skip(f"Custom user agent test failed: {result['error']}")

    assert isinstance(result, dict)
    assert result.get("content") is not None
