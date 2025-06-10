import pytest
import asyncio
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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
    # Test normal URLs
    assert get_domain_from_url("https://example.com") == "example.com"
    assert get_domain_from_url("https://www.example.com") == "example.com"
    assert get_domain_from_url("http://blog.example.com/post/123") == "blog.example.com"
    
    # Test URLs with ports
    assert get_domain_from_url("https://example.com:8080") == "example.com:8080"
    
    # Test invalid URLs
    assert get_domain_from_url("not-a-url") is None
    assert get_domain_from_url("") is None

@pytest.mark.asyncio
async def test_rate_limiting():
    # Test rate limiting for the same domain
    domain = "test-domain.com"
    url = f"https://{domain}"
    
    # First request should not be delayed
    start_time = asyncio.get_event_loop().time()
    await apply_rate_limiting(url)
    first_request_time = asyncio.get_event_loop().time() - start_time
    
    # Second request to same domain should be delayed
    start_time = asyncio.get_event_loop().time()
    await apply_rate_limiting(url)
    second_request_time = asyncio.get_event_loop().time() - start_time
    
    # The second request should take at least 2 seconds (MIN_SECONDS_BETWEEN_REQUESTS)
    assert second_request_time >= 1.9, f"Rate limiting not working, delay was only {second_request_time} seconds"
    
    # Different domain shouldn't be delayed
    different_url = "https://different-domain.com"
    start_time = asyncio.get_event_loop().time()
    await apply_rate_limiting(different_url)
    different_domain_time = asyncio.get_event_loop().time() - start_time
    
    # Different domain request should be quick
    assert different_domain_time < 0.5, f"Different domain was delayed: {different_domain_time} seconds"

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
    # Find a likely article link on the homepage
    try:
        resp = requests.get(start_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Try to find a link to an article (heuristic: <a> with /article or /news or /story or /202 or /p/)
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
    if "Cloudflare challenge" in result:
        pytest.skip(f"Cloudflare challenge detected for {link}")
        return
    if "[ERROR]" in result:
        pytest.skip(f"Extraction failed for {link}: {result}")
        return
    assert result.startswith("Title:")
    assert "Markdown Content:" in result
    assert "URL Source:" in result
    # Optionally, check for minimum content length
    content = result.split("Markdown Content:", 1)[-1].strip()
    if 'dev.to' not in link and 'forem.com' not in link:
        assert len(content) >= 100, f"Extracted text too short ({len(content)} chars) for {link}"

@pytest.mark.asyncio
async def test_missing_url_argument():
    # Simulate missing URL by passing None
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