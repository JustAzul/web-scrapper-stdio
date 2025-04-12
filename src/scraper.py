import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from bs4 import BeautifulSoup
import logging
import re

from .config import TIMEOUT_SECONDS, USER_AGENT, VIEWPORT_WIDTH, VIEWPORT_HEIGHT

logger = logging.getLogger(__name__)

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
                logger.info(f"Navigating to URL: {url}")
                response = await page.goto(url, wait_until="domcontentloaded")
                result["final_url"] = page.url # Update with the final URL after redirects

                if response is None or not response.ok:
                    status_code = response.status if response else 'N/A'
                    logger.warning(f"Failed to fetch URL {url} with status {status_code}")
                    result["status"] = "error_fetching"
                    result["error_message"] = f"HTTP status code: {status_code}"
                    await browser.close()
                    return result

                # Wait for potential dynamic content loading - a simple heuristic
                await asyncio.sleep(3) # Give some time for JS execution

                logger.info(f"Extracting content from: {result['final_url']}")
                html_content = await page.content()

                # --- Text Extraction Logic --- 
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style elements
                for script_or_style in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form']):
                    script_or_style.decompose()

                # Attempt to find common main content containers
                main_content = soup.find('article') or soup.find('main') or soup.find(role='main')
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

                if not text:
                    logger.warning(f"No significant text content found at {result['final_url']}")
                    result["status"] = "error_parsing"
                    result["error_message"] = "No significant text content extracted."
                else:
                    logger.info(f"Successfully extracted text from {result['final_url']}")
                    result["extracted_text"] = text
                    result["status"] = "success"

            except PlaywrightTimeoutError:
                logger.error(f"Timeout error navigating to/loading {url}")
                result["status"] = "error_timeout"
                result["error_message"] = f"Page load timed out after {TIMEOUT_SECONDS} seconds."
            except PlaywrightError as e:
                logger.error(f"Playwright error accessing {url}: {e}")
                result["status"] = "error_fetching"
                result["error_message"] = f"Browser/Navigation error: {str(e)}"
            except Exception as e:
                logger.exception(f"Unexpected error during scraping of {url}: {e}") # Log full traceback for unexpected errors
                result["status"] = "error_parsing" # Assume parsing issue if not caught above
                result["error_message"] = f"An unexpected error occurred: {str(e)}"
            finally:
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