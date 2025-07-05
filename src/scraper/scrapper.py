"""
Simplified consolidated Scraper class that works directly with Playwright's sync API.
"""

import secrets
import time
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from src.core.constants import (
    DEFAULT_ACCEPT_LANGUAGES,
    DEFAULT_BROWSER_VIEWPORTS,
    DEFAULT_ELEMENTS_TO_REMOVE,
    DEFAULT_USER_AGENTS,
)
from src.logger import get_logger
from src.models import ScrapeArgs
from src.output_format_handler import (
    OutputFormat,
    to_markdown,
    to_text,
    truncate_content,
)

logger = get_logger(__name__)


class Scraper:
    """
    Simplified consolidated scraper that works directly with Playwright's sync API.
    """

    def scrape(self, args: ScrapeArgs) -> Dict[str, Any]:
        """
        Main scraping method that handles the entire process using sync API.
        """
        logger.info(f"Starting scrape for URL: {args.url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = None
            try:
                page = browser.new_page()
                self._configure_page(page, args)

                response = page.goto(
                    str(args.url), timeout=args.timeout_seconds * 1000
                )

                if response and not 200 <= response.status < 300:
                    raise Exception(f"HTTP {response.status} {response.status_text}")

                if args.grace_period_seconds > 0:
                    time.sleep(args.grace_period_seconds)

                html_content = page.content()
                final_url = page.url
                title = page.title()

                processed_content = self._process_html(html_content, args)
                formatted_content = self._format_output(
                    processed_content, args.output_format
                )

                if args.max_length:
                    length = int(args.max_length)
                    formatted_content = truncate_content(formatted_content, length)

                return {
                    "title": title,
                    "final_url": final_url,
                    "content": formatted_content,
                    "error": None,
                }
            except Exception as e:
                error_message = str(e)
                logger.error(f"Scraping failed for {args.url}: {error_message}")
                return {
                    "title": None,
                    "final_url": str(args.url),
                    "content": None,
                    "error": error_message,
                }
            finally:
                if page:
                    page.close()
                browser.close()

    def _configure_page(self, page: Page, args: ScrapeArgs):
        """Configure the page with random user agent and viewport."""
        secure_random = secrets.SystemRandom()

        viewport = secure_random.choice(DEFAULT_BROWSER_VIEWPORTS)
        page.set_viewport_size(viewport)

        user_agent = self._get_user_agent(args.user_agent)
        page.set_extra_http_headers(
            {
                "User-Agent": user_agent,
                "Accept-Language": secure_random.choice(DEFAULT_ACCEPT_LANGUAGES),
            }
        )

        if "custom_headers" in args and args.custom_headers:
            page.set_extra_http_headers(args.custom_headers)

    def _get_user_agent(self, custom_user_agent: Optional[str] = None) -> str:
        """Get user agent string."""
        if custom_user_agent:
            return custom_user_agent
        return secrets.SystemRandom().choice(DEFAULT_USER_AGENTS)

    def _process_html(self, html_content: str, args: ScrapeArgs) -> str:
        """Process HTML content and extract main text."""
        soup = BeautifulSoup(html_content, "html.parser")

        elements_to_remove = set(DEFAULT_ELEMENTS_TO_REMOVE)
        if args.custom_elements_to_remove:
            elements_to_remove.update(args.custom_elements_to_remove)

        for selector in elements_to_remove:
            for element in soup.select(selector):
                element.decompose()

        return soup.get_text(separator=" ", strip=True)

    def _format_output(self, content: str, output_format: OutputFormat) -> str:
        """Format the output according to the specified format."""
        if output_format == OutputFormat.TEXT:
            return to_text(content)
        elif output_format == OutputFormat.MARKDOWN:
            return to_markdown(content)
        elif output_format == OutputFormat.HTML:
            return content
        else:
            return to_markdown(content)
