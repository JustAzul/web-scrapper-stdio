import pytest
import asyncio
import re
import requests
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.config import (
    DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS,
    DEFAULT_TEST_REQUEST_TIMEOUT,
    DEFAULT_TEST_NO_DELAY_THRESHOLD,
    DEFAULT_MIN_CONTENT_LENGTH,
)

from src.scraper import extract_text_from_url, get_domain_from_url, apply_rate_limiting
from src.output_format_handler import OutputFormat
from src.scraper.helpers.browser import USER_AGENTS


@pytest.mark.asyncio
async def test_extract_text_from_example_com():
    url = "http://example.com"
    result = await extract_text_from_url(url)
    assert isinstance(result, dict)
    assert result.get("title") is not None
    assert "Example Domain" in (result.get("title") or "") or "Example Domain" in (
        result.get("content") or "")
    assert result.get("content") is not None
    assert result.get("final_url") in [
        url, url + "/", "https://www.example.com", "https://www.example.com/"]
    assert not result.get("error")


@pytest.mark.asyncio
async def test_extract_text_from_example_com_text_output():
    url = "http://example.com"
    result = await extract_text_from_url(url, output_format=OutputFormat.TEXT)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    assert "Example Domain" in result.get("content", "")


@pytest.mark.asyncio
async def test_extract_text_from_example_com_markdown_output():
    url = "http://example.com"
    result = await extract_text_from_url(url, output_format=OutputFormat.MARKDOWN)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    md_content = result.get("content") or ""
    assert "[" in md_content and "](" in md_content


@pytest.mark.asyncio
async def test_extract_text_from_example_com_html_output():
    url = "http://example.com"
    result = await extract_text_from_url(url, output_format=OutputFormat.HTML)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    html = result.get("content")
    assert html is not None
    BeautifulSoup(html, "html.parser")


@pytest.mark.asyncio
async def test_extract_text_from_example_com_with_max_length():
    url = "http://example.com"
    result = await extract_text_from_url(url, max_length=50, output_format=OutputFormat.HTML)
    assert isinstance(result, dict)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    html = result.get("content")
    assert html is not None
    assert len(html) <= 50 + len("\n\n[Content truncated due to length]")
    BeautifulSoup(html, "html.parser")


@pytest.mark.asyncio
async def test_extract_text_from_wikipedia():
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    result = await extract_text_from_url(url)
    assert isinstance(result, dict)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    assert result.get("title") is not None
    assert "Web scraping" in (result.get("title") or "") or "Web scraping" in (
        result.get("content") or "")
    assert result.get("content") is not None
    assert result.get("final_url") == url or result.get(
        "final_url", "").startswith("https://en.wikipedia.org/wiki/")


@pytest.mark.asyncio
async def test_nonexistent_domain():
    url = "https://nonexistent-domain-for-testing-12345.com/somepage"
    result = await extract_text_from_url(url)
    assert isinstance(result, dict)
    assert result.get("error")
    assert "Could not resolve" in result.get(
        "error") or "error" in result.get("error").lower()


@pytest.mark.asyncio
async def test_invalid_url_format():
    url = "not-a-valid-url"
    result = await extract_text_from_url(url)
    assert isinstance(result, dict)
    assert result.get("error")
    assert "invalid url" in result.get(
        "error").lower() or "error" in result.get("error").lower()


@pytest.mark.asyncio
async def test_http_404_page():
    url = "https://httpstat.us/404"
    result = await extract_text_from_url(url)
    assert isinstance(result, dict)
    assert result.get("error")
    assert "404" in result.get(
        "error") or "not found" in result.get("error").lower()


def test_get_domain_from_url():
    assert get_domain_from_url("https://example.com") == "example.com"
    assert get_domain_from_url("https://www.example.com") == "example.com"
    assert get_domain_from_url(
        "http://blog.example.com/post/123") == "blog.example.com"
    assert get_domain_from_url(
        "https://example.com:8080") == "example.com:8080"
    assert get_domain_from_url("not-a-url") is None
    assert get_domain_from_url("") is None


@pytest.mark.asyncio
async def test_rate_limiting():
    domain = "test-domain.com"
    url = f"https://{domain}"
    start_time = asyncio.get_event_loop().time()

    await apply_rate_limiting(url)
    first_request_time = asyncio.get_event_loop().time() - start_time
    start_time = asyncio.get_event_loop().time()

    await apply_rate_limiting(url)
    second_request_time = asyncio.get_event_loop().time() - start_time

    assert second_request_time >= DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS - \
        0.1, f"Rate limiting not working, delay was only {second_request_time} seconds"
    different_url = "https://different-domain.com"
    start_time = asyncio.get_event_loop().time()

    await apply_rate_limiting(different_url)
    different_domain_time = asyncio.get_event_loop().time() - start_time

    assert different_domain_time < DEFAULT_TEST_NO_DELAY_THRESHOLD, f"Different domain was delayed: {different_domain_time} seconds"


@pytest.mark.asyncio
async def test_extract_real_article():
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    result = await extract_text_from_url(url)
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result}")
    assert isinstance(result, dict)
    assert result.get("title") is not None
    assert "Web scraping" in (result.get("title") or "") or "Web scraping" in (
        result.get("content") or "")
    assert result.get("content") is not None
    assert result.get("final_url") == url or result.get(
        "final_url", "").startswith("https://en.wikipedia.org/wiki/")


@pytest.mark.asyncio
@pytest.mark.parametrize("domain_info", [
    ("fortune.com", "/"),
    ("techcrunch.com", "/"),
    ("wired.com", "/"),
    ("engadget.com", "/"),
    ("medium.com", "/"),
    ("dev.to", "/"),
    ("tomsguide.com", "/news"),
    ("xda-developers.com", "/"),
    ("dmnews.com", "/"),
], ids=[
    "fortune.com",
    "techcrunch.com",
    "wired.com",
    "engadget.com",
    "medium.com",
    "dev.to",
    "tomsguide.com",
    "xda-developers.com",
    "dmnews.com",
])
async def test_dynamic_article_extraction(domain_info):
    domain, start_path = domain_info
    start_url = f"https://{domain}{start_path or '/'}"
    try:
        resp = requests.get(start_url, timeout=DEFAULT_TEST_REQUEST_TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")
        link = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(x in href for x in ["/article", "/news", "/story", "/202", "/p/"]):
                if href.startswith("/"):
                    link = f"https://{domain}{href}"
                elif href.startswith("http"):
                    link = href
                break
        if not link:
            pytest.skip(
                f"Could not dynamically find an article link on {start_url}")
            return
    except Exception as e:
        pytest.skip(f"Failed to fetch homepage for {domain}: {e}")
        return
    result = await extract_text_from_url(link)
    if result.get("error") and "Cloudflare challenge" in result.get("error"):
        pytest.skip(f"Cloudflare challenge detected for {link}")
        return
    if result.get("error"):
        pytest.skip(f"Extraction failed for {link}: {result}")
        return
    assert isinstance(result, dict)
    assert result.get("title") is not None
    assert result.get("content") is not None
    content = result.get("content") or ""
    if 'dev.to' not in link and 'forem.com' not in link:
        assert len(
            content) >= DEFAULT_MIN_CONTENT_LENGTH, f"Extracted text too short ({len(content)} chars) for {link}"


@pytest.mark.asyncio
async def test_missing_url_argument():
    result = await extract_text_from_url("")
    assert isinstance(result, dict)
    assert result.get("error")
    assert "url" in result.get("error").lower() or "invalid" in result.get(
        "error").lower() or "error" in result.get("error").lower()


@pytest.mark.asyncio
async def test_404_page():
    url = "https://httpbin.org/status/404"
    result = await extract_text_from_url(url)
    assert isinstance(result, dict)
    assert result.get("error")
    assert "404" in result.get(
        "error") or "not found" in result.get("error").lower()


@pytest.mark.asyncio
async def test_grace_period_seconds_js_delay():
    """
    This test checks that increasing grace_period_seconds allows the scraper to capture JS-rendered content that appears after a delay.
    It uses a public test page that adds content after a JS timeout. If no such page is available, this test will be skipped.
    """
    # Example public test page that adds content after 2 seconds via JS
    # This is a placeholder; ideally use a real JS-delay demo page
    test_url = "https://httpbin.org/delay/2"

    # Try with a short grace period (should not capture delayed content)
    result_short = await extract_text_from_url(test_url, grace_period_seconds=0.5)
    # Try with a longer grace period (should capture delayed content)
    result_long = await extract_text_from_url(test_url, grace_period_seconds=3.0)

    # If the page does not actually use JS to delay content, skip the test
    if result_short.get("content") == result_long.get("content"):
        pytest.skip(
            "Test page does not have JS-delayed content or is not suitable for this test.")

    # The longer grace period should yield more content
    assert len(result_long.get("content") or "") > len(result_short.get("content") or ""), "Longer grace period did not capture more content."


@pytest.mark.asyncio
async def test_custom_user_agent_and_no_network_idle():
    url = "http://example.com"
    result = await extract_text_from_url(
        url,
        user_agent=random.choice(USER_AGENTS),
        wait_for_network_idle=False,
    )
    assert isinstance(result, dict)
    assert result.get("content") is not None
    assert not result.get("error")
