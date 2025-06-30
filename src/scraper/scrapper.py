"""
Simplified consolidated Scraper class that works directly with Playwright.
"""

import asyncio
import secrets
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from playwright.async_api import Page, async_playwright

from src.core.constants import (
    DEFAULT_ACCEPT_LANGUAGES,
    DEFAULT_BROWSER_VIEWPORTS,
    DEFAULT_ELEMENTS_TO_REMOVE,
    DEFAULT_USER_AGENTS,
)
from src.logger import Logger
from src.models import ScrapeArgs
from src.output_format_handler import (
    OutputFormat,
    to_markdown,
    to_text,
    truncate_content,
)

logger = Logger(__name__)


class Scraper:
    """
    Simplified consolidated scraper that works directly with Playwright.
    """

    def __init__(self):
        """Initialize the scraper."""
        self.playwright = None
        self.browser = None

    async def scrape(self, args: ScrapeArgs) -> Dict[str, Any]:
        """
        Main scraping method that handles the entire process.
        Now accepts ScrapeArgs directly.
        """
        logger.info(f"Starting scrape for URL: {args.url}")

        playwright = None
        browser = None
        page = None

        try:
            # Initialize playwright for this scrape operation
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)

            # Create a new page with random configuration
            page = await browser.new_page()

            # Configure the page
            await self._configure_page(page, args)

            # Navigate and get content
            response = await page.goto(
                str(args.url), timeout=args.timeout_seconds * 1000
            )

            # Check for non-successful HTTP status codes
            if response and not 200 <= response.status < 300:
                raise Exception(f"HTTP {response.status} {response.status_text}")

            # Wait for grace period if specified
            if args.grace_period_seconds > 0:
                await asyncio.sleep(args.grace_period_seconds)

            # Get page content
            html_content = await page.content()
            final_url = page.url
            title = await page.title()

            # Process the HTML content
            processed_content = self._process_html(html_content, args)

            # Format output
            formatted_content = self._format_output(
                processed_content, args.output_format
            )

            # Apply length limit if specified
            if args.max_length:
                formatted_content = truncate_content(formatted_content, args.max_length)

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
            # Always clean up resources
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except Exception:
                    pass

    async def _configure_page(self, page: Page, args: ScrapeArgs):
        """Configure the page with random user agent and viewport."""
        # Use secure random for anti-detection features
        secure_random = secrets.SystemRandom()

        # Set random viewport
        viewport = secure_random.choice(DEFAULT_BROWSER_VIEWPORTS)
        await page.set_viewport_size(viewport)

        # Set user agent
        user_agent = self._get_user_agent(args.user_agent)
        await page.set_extra_http_headers(
            {
                "User-Agent": user_agent,
                "Accept-Language": secure_random.choice(DEFAULT_ACCEPT_LANGUAGES),
            }
        )

        # Add custom headers if provided
        if args.custom_headers:
            await page.set_extra_http_headers(args.custom_headers)

    def _get_user_agent(self, custom_user_agent: Optional[str] = None) -> str:
        """Get user agent string."""
        if custom_user_agent:
            return custom_user_agent

        secure_random = secrets.SystemRandom()
        return secure_random.choice(DEFAULT_USER_AGENTS)

    def _process_html(self, html_content: str, args: ScrapeArgs) -> str:
        """Process HTML content and extract main text."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        elements_to_remove = DEFAULT_ELEMENTS_TO_REMOVE.copy()

        for element_name in elements_to_remove:
            for element in soup.find_all(element_name):
                element.decompose()

        # Extract text content
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
            return to_markdown(content)  # Default to markdown

    async def close(self):
        """Clean up resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
