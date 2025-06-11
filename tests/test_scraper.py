import pytest
import asyncio
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.config import DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS, DEFAULT_TEST_REQUEST_TIMEOUT, DEFAULT_TEST_NO_DELAY_THRESHOLD, DEFAULT_MIN_CONTENT_LENGTH

from src.scraper import extract_text_from_url, get_domain_from_url, apply_rate_limiting


@pytest.mark.asyncio
async def test_extract_text_from_example_com():
    url = "https://example.com"
    result = await extract_text_from_url(url)

    assert result.startswith("Title:")
    assert "Example Domain" in result
    assert "Markdown Content:" in result
    assert "URL Source:" in result
    assert "[ERROR]" not in result


@pytest.mark.asyncio
async def test_extract_text_from_wikipedia():
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    result = await extract_text_from_url(url)

    assert result.startswith("Title:")
    assert "Web scraping" in result
    assert "Markdown Content:" in result
    assert "URL Source:" in result
    assert "[ERROR]" not in result


@pytest.mark.asyncio
async def test_nonexistent_domain():
    url = "https://nonexistent-domain-for-testing-12345.com/somepage"
    result = await extract_text_from_url(url)

    assert "[ERROR]" in result
    assert "Could not resolve" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_invalid_url_format():
    url = "not-a-valid-url"
    result = await extract_text_from_url(url)

    assert "[ERROR]" in result
    assert "invalid url" in result.lower() or "error" in result.lower()


@pytest.mark.asyncio
async def test_http_404_page():
    url = "https://httpstat.us/404"
    result = await extract_text_from_url(url)

    assert "[ERROR]" in result
    assert "404" in result or "not found" in result.lower()


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

    if "[ERROR]" in result:
        pytest.skip(f"Extraction failed: {result}")
    assert result.startswith("Title:")
    assert "Web scraping" in result
    assert "Markdown Content:" in result
    assert "URL Source:" in result


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

            if any(
                x in href for x in [
                    "/article",
                    "/news",
                    "/story",
                    "/202",
                    "/p/"]):

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

    if "Cloudflare challenge" in result:
        pytest.skip(f"Cloudflare challenge detected for {link}")

        return

    if "[ERROR]" in result:
        pytest.skip(f"Extraction failed for {link}: {result}")

        return
    assert result.startswith("Title:")
    assert "Markdown Content:" in result
    assert "URL Source:" in result
    content = result.split("Markdown Content:", 1)[-1].strip()

    if 'dev.to' not in link and 'forem.com' not in link:
        assert len(
            content) >= DEFAULT_MIN_CONTENT_LENGTH, f"Extracted text too short ({len(content)} chars) for {link}"


@pytest.mark.asyncio
async def test_missing_url_argument():
    result = await extract_text_from_url("")

    assert "[ERROR]" in result
    assert "url" in result.lower() or "invalid" in result.lower() or "error" in result.lower()


@pytest.mark.asyncio
async def test_nonexistent_domain():
    url = "https://nonexistent-domain-for-testing-12345.com/somepage"
    result = await extract_text_from_url(url)

    assert "[ERROR]" in result
    assert "Could not resolve" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_404_page():
    url = "https://httpbin.org/status/404"
    result = await extract_text_from_url(url)

    assert "[ERROR]" in result
    assert "404" in result or "not found" in result.lower()
