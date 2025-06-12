import random
from playwright.async_api import async_playwright
from src.config import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MIN_CONTENT_LENGTH,
    DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP)
from src.logger import Logger
from .helpers.rate_limiting import get_domain_from_url, apply_rate_limiting
from .helpers.browser import _setup_browser_context, USER_AGENTS, VIEWPORTS, LANGUAGES
from .helpers.content_selectors import _wait_for_content_stabilization
from .helpers.html_utils import _extract_and_clean_html, _extract_markdown_and_text, _is_content_too_short
from .helpers.errors import _navigate_and_handle_errors, _handle_cloudflare_block

logger = Logger(__name__)


def extract_and_format_content(html_content, elements_to_remove, url):
    soup, target_element = _extract_and_clean_html(
        html_content, elements_to_remove)

    if not target_element:
        logger.warning(f"Could not find body tag for {url}")

        return None, None, None, "[ERROR] Could not find body tag in HTML."
    markdown_content, text = _extract_markdown_and_text(target_element)
    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

    return page_title, markdown_content, text, None


async def extract_text_from_url(url: str,
                                custom_elements_to_remove: list = None,
                                custom_timeout: int = None) -> dict:
    timeout_seconds = custom_timeout if custom_timeout is not None else DEFAULT_TIMEOUT_SECONDS

    try:
        async with async_playwright() as p:
            user_agent = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORTS)
            accept_language = random.choice(LANGUAGES)

            browser, context, page = await _setup_browser_context(p, user_agent, viewport, accept_language, timeout_seconds)

            try:
                await apply_rate_limiting(url)
                logger.debug(f"Navigating to URL: {url}")
                response, nav_error = await _navigate_and_handle_errors(page, url, timeout_seconds)

                if nav_error:
                    await browser.close()
                    return {
                        "title": None,
                        "final_url": url,
                        "markdown_content": None,
                        "error": nav_error
                    }

                logger.debug(f"Waiting for content to stabilize on {page.url}")
                domain = get_domain_from_url(page.url)
                content_found = await _wait_for_content_stabilization(page, domain, timeout_seconds)

                if not content_found:
                    logger.warning(f"<body> tag not found for {page.url}")
                    await browser.close()
                    return {
                        "title": None,
                        "final_url": page.url,
                        "markdown_content": None,
                        "error": "[ERROR] <body> tag not found."
                    }

                logger.debug(f"Extracting content from: {page.url}")
                html_content = await page.content()

                is_blocked, cf_error = _handle_cloudflare_block(
                    html_content, page.url)

                if is_blocked:
                    await browser.close()
                    return {
                        "title": None,
                        "final_url": page.url,
                        "markdown_content": None,
                        "error": cf_error
                    }

                default_elements_to_remove = [
                    'script',
                    'style',
                    'nav',
                    'footer',
                    'aside',
                    'header',
                    'form',
                    'button',
                    'input',
                    'select',
                    'textarea',
                    'label',
                    'iframe',
                    'figure',
                    'figcaption']

                elements_to_remove = default_elements_to_remove.copy()

                if custom_elements_to_remove:
                    elements_to_remove.extend(custom_elements_to_remove)

                page_title, markdown_content, text, content_error = extract_and_format_content(
                    html_content, elements_to_remove, page.url)

                if content_error:
                    await browser.close()
                    return {
                        "title": None,
                        "final_url": page.url,
                        "markdown_content": None,
                        "error": content_error
                    }

                original_domain = get_domain_from_url(url)
                min_content_length = DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP if original_domain and 'search.app' in original_domain else DEFAULT_MIN_CONTENT_LENGTH

                if _is_content_too_short(text, min_content_length):
                    logger.warning(
                        f"No significant text content extracted (length < {min_content_length}) at {page.url}")
                    await browser.close()
                    return {
                        "title": page_title,
                        "final_url": page.url,
                        "markdown_content": None,
                        "error": f"[ERROR] No significant text content extracted (too short, less than {min_content_length} characters)."
                    }
                else:
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

                    logger.debug(
                        f"Successfully extracted text from {page.url}")

                    await browser.close()

                    return {
                        "title": page_title,
                        "final_url": page.url,
                        "markdown_content": markdown_content,
                        "error": None
                    }

            except Exception as e:
                logger.warning(
                    f"Unexpected error during scraping of {url}: {e}")
                await browser.close()

                return {
                    "title": None,
                    "final_url": url,
                    "markdown_content": None,
                    "error": f"[ERROR] An unexpected error occurred: {str(e)}"
                }

    except ImportError:
        logger.warning(
            "Playwright is not installed. Please run 'pip install playwright && playwright install'")

        return {
            "title": None,
            "final_url": url,
            "markdown_content": None,
            "error": "[ERROR] Playwright installation missing."
        }

    except Exception as e:
        logger.warning(
            f"General error setting up Playwright or during execution for {url}: {e}")

        return {
            "title": None,
            "final_url": url,
            "markdown_content": None,
            "error": f"[ERROR] An unexpected error occurred: {str(e)}"
        }

    return {
        "title": None,
        "final_url": url,
        "markdown_content": None,
        "error": "[ERROR] Unknown error occurred."
    }
