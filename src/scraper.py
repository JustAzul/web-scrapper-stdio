import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from bs4 import BeautifulSoup
import logging
import re
from urllib.parse import urlparse
import time # Added for time tracking
import asyncio # Added for lock and sleep

# Try different import approaches to handle various contexts
try:
    # When imported as part of the src package
    from .config import TIMEOUT_SECONDS, USER_AGENT, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
except ImportError:
    try:
        # When using absolute imports
        from src.config import TIMEOUT_SECONDS, USER_AGENT, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
    except ImportError:
        # When run directly or in special contexts
        import sys
        import os
        # Add parent directory to path
        sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        from src.config import TIMEOUT_SECONDS, USER_AGENT, VIEWPORT_WIDTH, VIEWPORT_HEIGHT

logger = logging.getLogger(__name__)

# --- Rate Limiting Globals ---
_domain_access_times = {}
_domain_lock = asyncio.Lock()
MIN_SECONDS_BETWEEN_REQUESTS = 2 # Be polite: Wait at least 2 seconds between requests to the same domain

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
        logger.debug(f"No valid domain for rate limiting: {url}")
        return # Cannot rate limit without a domain

    async with _domain_lock:
        current_time = time.time()
        last_access_time = _domain_access_times.get(domain)

        if last_access_time:
            time_since_last = current_time - last_access_time
            if time_since_last < MIN_SECONDS_BETWEEN_REQUESTS:
                sleep_duration = MIN_SECONDS_BETWEEN_REQUESTS - time_since_last
                logger.info(f"Rate limiting {domain}: Sleeping for {sleep_duration:.2f}s")
                await asyncio.sleep(sleep_duration)
                # Update current_time after sleeping
                current_time = time.time()

        # Update the last access time for this domain
        _domain_access_times[domain] = current_time

async def extract_text_from_url(url: str) -> dict:
    """Fetches and extracts primary text content from a URL using Playwright.

    Args:
        url: The URL to scrape.

    Returns:
        A dictionary containing:
            - extracted_text: The extracted text.
            - status: The outcome status string.
            - error_message: Description of the error if any.
            - final_url: The URL after potential redirects.
    """
    result = {
        "extracted_text": "",
        "status": "error_unknown",
        "error_message": None,
        "final_url": url, # Start with the input URL
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT},
                java_script_enabled=True,
            )
            page = await context.new_page()

            # Set navigation timeout
            page.set_default_navigation_timeout(TIMEOUT_SECONDS * 1000)
            page.set_default_timeout(TIMEOUT_SECONDS * 1000)

            try:
                # --- Apply Rate Limiting BEFORE navigation ---
                await apply_rate_limiting(url)
                
                logger.info(f"Navigating to URL: {url}")
                response = await page.goto(url, wait_until="domcontentloaded")
                result["final_url"] = page.url # Update with the final URL after redirects

                # CRITICAL: Check response status *immediately* after navigation
                if response is None:
                    # This case might happen if navigation itself fails critically
                    logger.error(f"Playwright returned None response for {url}")
                    result["status"] = "error_fetching"
                    result["error_message"] = "Navigation failed, no response received."
                    await browser.close()
                    return result
                
                # Also check for common 404 page indicators even if status is 200 OK
                page_title = await page.title()
                page_content_preview = await page.content() # Get initial content quickly
                not_found_patterns = [
                    r"404 Not Found", r"Page Not Found", r"couldn't find this page",
                    r"can't find page", r"doesn't exist", r"Oops! Nothing was found"
                ]
                is_likely_404 = False
                if not response.ok:
                    is_likely_404 = True
                else:
                    # Check title and body for patterns if response was OK
                    for pattern in not_found_patterns:
                        if re.search(pattern, page_title, re.IGNORECASE) or \
                           re.search(pattern, page_content_preview[:2000], re.IGNORECASE): # Check first 2k chars
                            logger.warning(f"Detected likely 404 content pattern ('{pattern}') despite 200 OK for {url}")
                            is_likely_404 = True
                            break
                
                if is_likely_404:
                    status_code = response.status
                    logger.warning(f"HTTP error or 404 content detected for {url}. Status: {status_code} at {result['final_url']}")
                    result["status"] = "error_fetching"
                    result["error_message"] = f"HTTP status code: {status_code} or page indicates 'Not Found'"
                    # Don't try to parse content from an error page
                    await browser.close()
                    return result

                # For some sites, the initial load doesn't have full content, so we need to wait
                # Wait for potential dynamic content loading - a simple heuristic
                # Only wait if the initial fetch was successful and not likely a 404
                await asyncio.sleep(3) # Give some time for JS execution

                logger.info(f"Extracting content from: {result['final_url']}")
                html_content = await page.content()

                # Parse the domain to use domain-specific extraction strategies
                domain = urlparse(result["final_url"]).netloc.lower()
                
                # --- Text Extraction Logic --- 
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style elements
                # Added more common non-content tags
                for script_or_style in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'input', 'select', 'textarea', 'label', 'iframe', 'figure', 'figcaption']):
                    script_or_style.decompose()
                
                # Domain-specific extraction strategies
                target_element = None
                
                # Handle dev.to and forem.com (which dev.to redirects to) domains
                if 'dev.to' in domain or 'forem.com' in domain:
                    logger.info(f"Using specialized extraction for dev.to/forem.com")
                    
                    # First look for the article tag with .crayons-article class
                    target_element = soup.find('article', class_='crayons-article')
                    
                    # If not found, look for the main content div with id=article-body
                    if not target_element:
                        target_element = soup.find('div', id='article-body')
                    
                    # Sometimes the content is in div.article-body
                    if not target_element:
                        target_element = soup.find('div', class_='article-body')
                    
                    # Also try finding the main section with article role
                    if not target_element:
                        target_element = soup.find('section', attrs={'role': 'main'})
                    
                    # Try to include the title for dev.to articles
                    title_element = soup.find('h1')
                    title_text = title_element.get_text(strip=True) if title_element else ""
                    
                    if target_element:
                        # Get text with the title included
                        text = title_text + "\n\n" + target_element.get_text(separator='\n', strip=True)
                        text = re.sub(r'\n\s*\n', '\n\n', text).strip()
                        
                        # dev.to often has short content that is still valid, so use a lower threshold
                        if text and len(text) > 30:  # Even lower threshold for dev.to/forem.com
                            result["extracted_text"] = text
                            result["status"] = "success"
                            await browser.close()
                            return result
                
                # General extraction if domain-specific logic didn't succeed
                if not target_element:
                    # Attempt to find common main content containers
                    main_content = soup.find('article') or soup.find('main') or soup.find(role='main')
                    # Fallback: check for common content divs if no semantic tag found
                    if not main_content:
                        common_divs = soup.find_all('div', class_=lambda x: x and ('content' in x or 'post' in x or 'entry' in x or 'article' in x))
                        if common_divs:
                             # Find the largest div among common ones, assuming it's the main content
                             main_content = max(common_divs, key=lambda tag: len(tag.get_text(strip=True)))

                    target_element = main_content if main_content else soup.body
                
                if not target_element:
                    logger.warning(f"Could not find body tag for {result['final_url']}")
                    result["status"] = "error_parsing"
                    result["error_message"] = "Could not find body tag in HTML."
                    await browser.close()
                    return result
                    
                # Get text and clean up whitespace
                text = target_element.get_text(separator='\n', strip=True)
                text = re.sub(r'\n\s*\n', '\n\n', text).strip() # Consolidate multiple newlines

                # Add a simple length check to avoid returning just boilerplate/empty strings
                if not text or len(text) < 100: # Arbitrary threshold, adjust as needed
                    logger.warning(f"No significant text content extracted (length < 100) at {result['final_url']}")
                    result["status"] = "error_parsing"
                    result["error_message"] = "No significant text content extracted (too short)."
                else:
                    logger.info(f"Successfully extracted text from {result['final_url']}")
                    result["extracted_text"] = text
                    result["status"] = "success"

            except PlaywrightTimeoutError:
                logger.error(f"Timeout error navigating to/loading {url}")
                result["status"] = "error_timeout"
                result["error_message"] = f"Page load timed out after {TIMEOUT_SECONDS} seconds."
            except PlaywrightError as e:
                 # Handle potential navigation errors more specifically
                if "net::ERR_NAME_NOT_RESOLVED" in str(e) or "net::ERR_CONNECTION_REFUSED" in str(e):
                     logger.error(f"Navigation error for {url}: {e}")
                     result["status"] = "error_fetching"
                     result["error_message"] = f"Could not resolve or connect to host: {url}"
                elif "Target closed" in str(e):
                    logger.warning(f"Browser tab closed unexpectedly for {url}: {e}")
                    result["status"] = "error_fetching"
                    result["error_message"] = "Browser tab closed unexpectedly during operation."
                else:
                    logger.error(f"Playwright error accessing {url}: {e}")
                    result["status"] = "error_fetching"
                    result["error_message"] = f"Browser/Navigation error: {str(e)}"
            except Exception as e:
                logger.exception(f"Unexpected error during scraping of {url}: {e}") # Log full traceback for unexpected errors
                result["status"] = "error_parsing" # Assume parsing issue if not caught above
                result["error_message"] = f"An unexpected error occurred: {str(e)}"
            finally:
                # Ensure browser is closed even if context/page creation failed
                if 'browser' in locals() and browser.is_connected():
                    await browser.close()

    except ImportError:
         logger.error("Playwright is not installed. Please run 'pip install playwright && playwright install'")
         result["status"] = "error_unknown"
         result["error_message"] = "Playwright installation missing."
    except Exception as e:
        logger.exception(f"General error setting up Playwright or during execution for {url}: {e}")
        result["status"] = "error_unknown"
        result["error_message"] = f"An unexpected error occurred: {str(e)}"

    return result 