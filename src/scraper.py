import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time # Added for time tracking
import random
from playwright_stealth import stealth_async
from markdownify import markdownify as md
from src.config import (
    DEFAULT_TIMEOUT_SECONDS, DEFAULT_MIN_CONTENT_LENGTH, DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP,
    DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS, DEFAULT_SELECTOR_WAIT_DOMAIN_MS, DEFAULT_SELECTOR_WAIT_GENERIC_MS, DEFAULT_GRACE_PERIOD_SECONDS,
    DEBUG_LOGS_ENABLED
)
from src.logger import Logger

logger = Logger(__name__)

# --- Rate Limiting Globals ---
_domain_access_times = {}
_domain_lock = asyncio.Lock()
MIN_SECONDS_BETWEEN_REQUESTS = DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS

# --- User Agent and Viewport Pools ---
USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
    {"width": 1280, "height": 800},
]
LANGUAGES = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7"]

def get_domain_from_url(url):
    """Extract the domain from a URL, removing www. prefix"""
    try:
        parsed = urlparse(url)
        # Handle cases where netloc might be empty or invalid
        domain = parsed.netloc
        if not domain:
            return None
        return domain.replace("www.", "")
    except ValueError:
        logger.warning(f"Could not parse domain from URL: {url}")
        return None

async def apply_rate_limiting(url: str):
    """Checks and applies delay if hitting the same domain too frequently."""
    domain = get_domain_from_url(url)
    if not domain:
        logger.warning(f"No valid domain for rate limiting: {url}")
        return

    async with _domain_lock:
        current_time = time.time()
        last_access_time = _domain_access_times.get(domain)

        if last_access_time:
            time_since_last = current_time - last_access_time
            if time_since_last < MIN_SECONDS_BETWEEN_REQUESTS:
                sleep_duration = MIN_SECONDS_BETWEEN_REQUESTS - time_since_last
                logger.warning(f"Rate limiting {domain}: Sleeping for {sleep_duration:.2f}s")
                await asyncio.sleep(sleep_duration)
                current_time = time.time()

        _domain_access_times[domain] = current_time

async def extract_text_from_url(url: str, 
                               custom_elements_to_remove: list = None, 
                               custom_timeout: int = None) -> str:
    """Fetches and extracts primary text content from a URL using Playwright and returns formatted output."""
    timeout_seconds = custom_timeout if custom_timeout is not None else DEFAULT_TIMEOUT_SECONDS

    try:
        async with async_playwright() as p:
            # --- Randomize user agent, viewport, and language ---
            user_agent = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORTS)
            accept_language = random.choice(LANGUAGES)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                java_script_enabled=True,
                locale=accept_language.split(",")[0],
                extra_http_headers={"Accept-Language": accept_language},
            )
            page = await context.new_page()
            # --- Apply stealth ---
            await stealth_async(page)
            # --- Additional navigator property tweaks (if needed) ---
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"
                "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});"
            )
            page.set_default_navigation_timeout(timeout_seconds * 1000)
            page.set_default_timeout(timeout_seconds * 1000)

            try:
                # --- Apply Rate Limiting BEFORE navigation ---
                await apply_rate_limiting(url)
                
                if DEBUG_LOGS_ENABLED:
                    logger.debug(f"Navigating to URL: {url}")
                response = await page.goto(url, wait_until="domcontentloaded")

                # CRITICAL: Check response status *immediately* after navigation
                if response is None:
                    logger.debug(f"Playwright returned None response for {url}")
                    await browser.close()
                    return "[ERROR] Navigation failed, no response received."
                
                # Also check for common 404 page indicators even if status is 200 OK
                page_title = await page.title()
                page_content_preview = await page.content()
                not_found_patterns = [
                    r"404 Not Found", r"Page Not Found", r"couldn't find this page",
                    r"can't find page", r"doesn't exist", r"Oops! Nothing was found"
                ]
                is_likely_404 = False
                if not response.ok:
                    is_likely_404 = True
                else:
                    for pattern in not_found_patterns:
                        if re.search(pattern, page_title, re.IGNORECASE) or \
                           re.search(pattern, page_content_preview[:2000], re.IGNORECASE):
                            logger.warning(f"Detected likely 404 content pattern ('{pattern}') despite 200 OK for {url}")
                            is_likely_404 = True
                            break
                
                if is_likely_404:
                    status_code = response.status
                    logger.warning(f"HTTP error or 404 content detected for {url}. Status: {status_code} at {page.url}")
                    await browser.close()
                    return f"[ERROR] HTTP status code: {status_code} or page indicates 'Not Found'"

                if DEBUG_LOGS_ENABLED:
                    logger.debug(f"Waiting for content to stabilize on {page.url}")

                try:
                    await page.wait_for_load_state("networkidle", timeout=timeout_seconds * 1000 / 2)
                    if DEBUG_LOGS_ENABLED:
                        logger.debug("Network became idle")
                except PlaywrightTimeoutError:
                    if DEBUG_LOGS_ENABLED:
                        logger.debug(f"Network didn't become fully idle after {timeout_seconds/2}s, continuing anyway")

                domain = urlparse(page.url).netloc.lower()
                content_found = False

                # Domain-specific content selectors to wait for
                domain_specific_selectors = {
                    "dev.to": ["article.crayons-article", "div#article-body", "div.article-body", "section[role='main']", "#article-show", "div.article-wrapper"],
                    "forem.com": ["article.crayons-article", "div#article-body", "div.article-body", "section[role='main']", "#article-show", "div.article-wrapper"],
                    "dmnews.com": ["div.story-content", "div.single-post", "article.content-page", "div.article-content", "div.article-body", "div[itemprop='articleBody']"],
                    "medium.com": ["article", "div.story", "section.story"],
                    "forbes.com": ["div.article-body", "article.article"]
                }

                # First try domain-specific waiting if available
                if any(d in domain for d in domain_specific_selectors.keys()):
                    matching_domain = next((d for d in domain_specific_selectors.keys() if d in domain), None)
                    if matching_domain:
                        if DEBUG_LOGS_ENABLED:
                            logger.debug(f"Using domain-specific selectors for {matching_domain}")
                        for selector in domain_specific_selectors[matching_domain]:
                            try:
                                await page.wait_for_selector(selector, timeout=DEFAULT_SELECTOR_WAIT_DOMAIN_MS)
                                if DEBUG_LOGS_ENABLED:
                                    logger.debug(f"Found domain-specific content container: {selector}")
                                content_found = True
                                break
                            except PlaywrightTimeoutError:
                                continue

                if not content_found:
                    # General content selectors
                    generic_selectors = ["article", "main", "[role='main']", ".post-content", ".article-content", "#article-body", ".content"]
                    if DEBUG_LOGS_ENABLED:
                        logger.debug("Trying generic content selectors")
                    
                    for selector in generic_selectors:
                        try:
                            await page.wait_for_selector(selector, timeout=DEFAULT_SELECTOR_WAIT_GENERIC_MS)
                            if DEBUG_LOGS_ENABLED:
                                logger.debug(f"Found content container: {selector}")
                            content_found = True
                            break
                        except PlaywrightTimeoutError:
                            continue

                if not content_found:
                    if DEBUG_LOGS_ENABLED:
                        logger.debug("No specific content containers found, allowing short grace period")
                    await asyncio.sleep(DEFAULT_GRACE_PERIOD_SECONDS)

                if DEBUG_LOGS_ENABLED:
                    logger.debug(f"Extracting content from: {page.url}")
                html_content = await page.content()

                # --- Cloudflare Challenge Detection ---
                cloudflare_patterns = [
                    r'Attention Required! \| Cloudflare',
                    r'cf-browser-verification',
                    r'Checking your browser before accessing',
                    r'Please enable JavaScript and Cookies to continue',
                    r'Cloudflare Ray ID',
                    r'cloudflare.com/speedtest',
                    r'Why do I have to complete a CAPTCHA?'
                ]
                if any(re.search(pattern, html_content, re.IGNORECASE) for pattern in cloudflare_patterns):
                    logger.warning(f"Cloudflare challenge detected for {page.url}")
                    await browser.close()
                    return "Cloudflare challenge or anti-bot screen detected. Content extraction blocked."

                domain = urlparse(page.url).netloc.lower()
                
                # --- Text Extraction Logic --- 
                soup = BeautifulSoup(html_content, 'html.parser')

                # Define default elements to remove
                default_elements_to_remove = ['script', 'style', 'nav', 'footer', 'aside', 'header', 
                                           'form', 'button', 'input', 'select', 'textarea', 
                                           'label', 'iframe', 'figure', 'figcaption']
                
                # Add custom elements to remove if provided
                elements_to_remove = default_elements_to_remove
                if custom_elements_to_remove:
                    elements_to_remove.extend(custom_elements_to_remove)
                
                # Remove script and style elements and other non-content tags
                for element in soup(elements_to_remove):
                    element.decompose()

                # Always extract the full <body> content
                target_element = soup.body
                if not target_element:
                    logger.warning(f"Could not find body tag for {page.url}")
                    await browser.close()
                    return "[ERROR] Could not find body tag in HTML."

                text = target_element.get_text(separator='\n', strip=True)
                text = re.sub(r'\n\s*\n', '\n\n', text).strip()

                page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

                markdown_content = md(str(target_element))

                original_domain = urlparse(url).netloc.lower()
                min_content_length = DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP if 'search.app' in original_domain else DEFAULT_MIN_CONTENT_LENGTH

                # --- NEW LOGIC: Check min length BEFORE truncation ---
                if not text or len(text) < min_content_length:
                    logger.warning(f"No significant text content extracted (length < {min_content_length}) at {page.url}")
                    await browser.close()
                    return f"[ERROR] No significant text content extracted (too short, less than {min_content_length} characters)."
                else:
                    # Truncate to max_length if specified in kwargs or context (MCP/stdio)
                    max_length = None
                    import inspect
                    frame = inspect.currentframe()
                    while frame:
                        if 'max_length' in frame.f_locals:
                            max_length = frame.f_locals['max_length']
                            break
                        frame = frame.f_back
                    if max_length is not None:
                        text = text[:max_length]
                        markdown_content = markdown_content[:max_length]
                    if DEBUG_LOGS_ENABLED:
                        logger.debug(f"Successfully extracted text from {page.url}")
                    await browser.close()
                    return (
                        f"Title: {page_title}\n\n"
                        f"URL Source: {page.url}\n\n"
                        f"Markdown Content:\n"
                        f"{markdown_content}"
                    )

            except PlaywrightTimeoutError:
                logger.warning(f"Timeout error navigating to/loading {url}")
                await browser.close()
                return f"[ERROR] Page load timed out after {timeout_seconds} seconds."
            except PlaywrightError as e:
                if "net::ERR_NAME_NOT_RESOLVED" in str(e) or "net::ERR_CONNECTION_REFUSED" in str(e):
                    logger.warning(f"Navigation error for {url}: {e}")
                    await browser.close()
                    return f"[ERROR] Could not resolve or connect to host: {url}"
                elif "Target closed" in str(e):
                    logger.warning(f"Browser tab closed unexpectedly for {url}: {e}")
                    await browser.close()
                    return "Browser tab closed unexpectedly during operation."
                else:
                    logger.warning(f"Playwright error accessing {url}: {e}")
                    await browser.close()
                    return f"[ERROR] Browser/Navigation error: {str(e)}"
            except Exception as e:
                logger.warning(f"Unexpected error during scraping of {url}: {e}")
                await browser.close()
                return f"[ERROR] An unexpected error occurred: {str(e)}"

    except ImportError:
        logger.warning("Playwright is not installed. Please run 'pip install playwright && playwright install'")
        return "[ERROR] Playwright installation missing."
    except Exception as e:
        logger.warning(f"General error setting up Playwright or during execution for {url}: {e}")
        return f"[ERROR] An unexpected error occurred: {str(e)}"

    return "[ERROR] Unknown error occurred." 