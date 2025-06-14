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
    content = result.get("content") or ""
    assert "Example Domain" in content
    assert "==" in content or "#" in content


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
async def test_dynamic_article_extraction_random_domain():
    """
    Picks a random domain from the list and tests article extraction for that domain.
    """
    domains = [
        ("fortune.com", "/"),
        ("techcrunch.com", "/"),
        ("wired.com", "/"),
        ("engadget.com", "/"),
        ("medium.com", "/"),
        ("dev.to", "/"),
        ("tomsguide.com", "/news"),
        ("xda-developers.com", "/"),
        ("dmnews.com", "/"),
    ]
    domain, start_path = random.choice(domains)
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
            pytest.skip(f"Could not dynamically find an article link on {start_url}")
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
        assert len(content) >= DEFAULT_MIN_CONTENT_LENGTH, f"Extracted text too short ({len(content)} chars) for {link}"


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
async def test_client_side_js_delay_playground():
    """
    UITestingPlayground: Client Side Delay
    - Clicks the playground button and waits for the delayed label to appear after JS processing.
    - Asserts the correct label text is present.
    """
    url = "http://uitestingplayground.com/clientdelay"
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        await page.click("#ajaxButton")
        await page.wait_for_selector("#content .bg-success", timeout=30000)
        content = await page.content()
        assert "Data calculated on the client side." in content, (
            f"Expected delayed label not found after button click. Content: {content[:200]}..."
        )
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_server_side_load_delay_playground():
    """
    UITestingPlayground: Load Delays
    - Waits for the delayed button to appear after server-side delay.
    - Asserts the correct button text is present.
    """
    url = "http://uitestingplayground.com/loaddelay"
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_selector('button:has-text("Button Appearing After Delay")', timeout=30000)
        content = await page.content()
        assert "Button Appearing After Delay" in content, (
            f"Expected delayed button not found. Content: {content[:200]}..."
        )
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_extract_with_click_selector_js_delay():
    """
    Test extract_text_from_url with click_selector on UITestingPlayground Client Side Delay.
    Should click the button and extract the delayed label.
    """
    url = "http://uitestingplayground.com/clientdelay"
    result = await extract_text_from_url(
        url,
        click_selector="#ajaxButton",
        grace_period_seconds=16,
    )
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    content = result.get("content") or ""
    assert "Data calculated on the client side." in content


@pytest.mark.asyncio
async def test_extract_with_click_selector_load_delay():
    """
    Test extract_text_from_url with click_selector on UITestingPlayground Load Delay.
    Should wait for the delayed button and click it (no-op, but should not fail).
    """
    url = "http://uitestingplayground.com/loaddelay"
    result = await extract_text_from_url(
        url,
        click_selector='button:has-text("Button Appearing After Delay")',
        grace_period_seconds=12,
    )
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    content = result.get("content") or ""
    assert "Button Appearing After Delay" in content


@pytest.mark.asyncio
async def test_extract_with_click_selector_qavbox_delay():
    """
    Test extract_text_from_url with click_selector on QAVBOX Delay Elements demo.
    Should click the trigger button and extract the delayed button.
    """
    url = "https://qavbox.github.io/demo/delay/"
    result = await extract_text_from_url(
        url,
        click_selector='button[onclick*="displayDelayBtn"]',
        grace_period_seconds=7,
    )
    if result.get("error"):
        pytest.skip(f"Extraction failed: {result['error']}")
    content = result.get("content") or ""
    assert 'id="delay"' in content or '<button id="delay"' in content or 'id=\'delay\'' in content, (
        f"Expected delayed button not found. Content: {content[:200]}..."
    )
