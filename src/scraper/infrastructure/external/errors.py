from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)
import re
from src.logger import Logger
from src.core.constants import CLOUDFLARE_PATTERNS, NOT_FOUND_PATTERNS

logger = Logger(__name__)


def _detect_cloudflare_challenge(html_content):
    return any(
        re.search(pattern, html_content, re.IGNORECASE)
        for pattern in CLOUDFLARE_PATTERNS
    )


async def _navigate_and_handle_errors(page, url, timeout_seconds):
    try:
        response = await page.goto(url, wait_until="domcontentloaded")

        if response is None:
            return None, "[ERROR] Navigation failed, no response received."

        page_title = await page.title()
        page_content_preview = await page.content()
        is_likely_404 = False

        if not response.ok:
            is_likely_404 = True

        else:
            for pattern in NOT_FOUND_PATTERNS:
                if re.search(pattern, page_title, re.IGNORECASE) or re.search(
                    pattern, page_content_preview[:2000], re.IGNORECASE
                ):
                    logger.warning(
                        f"Detected likely 404 content pattern ('{pattern}') despite 200 OK for {url}"
                    )
                    is_likely_404 = True

                    break

        if is_likely_404:
            status_code = response.status

            logger.warning(
                f"HTTP error or 404 content detected for {url}. Status: {status_code} at {page.url}"
            )

            return (
                response,
                f"[ERROR] HTTP status code: {status_code} or page indicates 'Not Found'",
            )

        return response, None

    except PlaywrightTimeoutError:
        logger.warning(f"Timeout error navigating to/loading {url}")
        return None, f"[ERROR] Page load timed out after {timeout_seconds} seconds."

    except PlaywrightError as e:
        if "net::ERR_NAME_NOT_RESOLVED" in str(
            e
        ) or "net::ERR_CONNECTION_REFUSED" in str(e):
            logger.warning(f"Navigation error for {url}: {e}")
            return None, f"[ERROR] Could not resolve or connect to host: {url}"

        elif "Target closed" in str(e):
            logger.warning(f"Browser tab closed unexpectedly for {url}: {e}")
            return None, "Browser tab closed unexpectedly during operation."

        else:
            logger.warning(f"Playwright error accessing {url}: {e}")
            return None, f"[ERROR] Browser/Navigation error: {str(e)}"

    except Exception as e:
        logger.warning(f"Unexpected error during scraping of {url}: {e}")
        return None, f"[ERROR] An unexpected error occurred: {str(e)}"


def _handle_cloudflare_block(html_content, page_url):
    if _detect_cloudflare_challenge(html_content):
        logger.warning(f"Cloudflare challenge detected for {page_url}")
        return (
            True,
            "Cloudflare challenge or anti-bot screen detected. Content extraction blocked.",
        )
    return False, None
