"""
Async Scraper class using Playwright's async API.
Implements core scraping logic with robust error handling and extensibility.
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
from src.logger import get_logger
from src.models import ScrapeArgs
from src.output_format_handler import (
    OutputFormat,
    to_markdown,
    to_text,
    truncate_content,
)

logger = get_logger(__name__)

class ScraperTimeoutError(Exception):
    """Raised when a scraping operation times out."""

class ScraperHTTPError(Exception):
    """Raised for non-2xx HTTP responses."""

class ScraperContentError(Exception):
    """Raised when content extraction or parsing fails."""

class AsyncScraper:
    """
    Asynchronous scraper using Playwright's async API.
    """

    async def scrape(self, args: ScrapeArgs) -> Dict[str, Any]:
        """
        Main scraping method that handles the entire process using async API.

        Args:
            args (ScrapeArgs): Scraping arguments.

        Returns:
            Dict[str, Any]: Scraping result with title, final_url, content, and error.
        """
        logger.info(f"Starting async scrape for URL: {args.url}")

        # 6. Validação proativa de argumentos
        validation_error = self._validate_args(args)
        if validation_error:
            logger.error(f"Validation error: {validation_error}")
            return {
                "title": None,
                "final_url": str(getattr(args, "url", None)),
                "content": None,
                "error": validation_error,
            }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = None
            try:
                page = await browser.new_page()
                await self._configure_page(page, args)

                try:
                    response = await page.goto(
                        str(args.url), timeout=args.timeout_seconds * 1000
                    )
                except Exception as e:
                    logger.error(f"Timeout or navigation error for {args.url}: {e}")
                    raise ScraperTimeoutError(f"Timeout or navigation error: {e}")

                if response and not 200 <= response.status < 300:
                    logger.error(f"HTTP error {response.status} {response.status_text} for {args.url}")
                    raise ScraperHTTPError(f"HTTP {response.status} {response.status_text}")

                if args.grace_period_seconds > 0:
                    await asyncio.sleep(args.grace_period_seconds)

                try:
                    html_content = await page.content()
                    final_url = page.url
                    title = await page.title()
                except Exception as e:
                    logger.error(f"Failed to extract content for {args.url}: {e}")
                    raise ScraperContentError(f"Failed to extract content: {e}")

                try:
                    processed_content = self._process_html(html_content, args)
                except Exception as e:
                    logger.error(f"HTML processing error for {args.url}: {e}")
                    raise ScraperContentError(f"HTML processing error: {e}")

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
            except (ScraperTimeoutError, ScraperHTTPError, ScraperContentError) as e:
                error_message = str(e)
                logger.error(f"Async scraping failed for {args.url}: {error_message}")
                # 4. Fallback para Requests+BeautifulSoup se Playwright falhar por erro de infraestrutura
                fallback_result = self._fallback_requests_scrape(args, error_message)
                if fallback_result:
                    return fallback_result
                return {
                    "title": None,
                    "final_url": str(args.url),
                    "content": None,
                    "error": error_message,
                }
            except Exception as e:
                error_message = f"Unexpected error: {e}"
                logger.error(f"Async scraping failed for {args.url}: {error_message}")
                fallback_result = self._fallback_requests_scrape(args, error_message)
                if fallback_result:
                    return fallback_result
                return {
                    "title": None,
                    "final_url": str(args.url),
                    "content": None,
                    "error": error_message,
                }
            finally:
                if page:
                    await page.close()
                await browser.close()

    async def _configure_page(self, page: Page, args: ScrapeArgs):
        """Configure the page with random user agent and viewport."""
        secure_random = secrets.SystemRandom()

        viewport = secure_random.choice(DEFAULT_BROWSER_VIEWPORTS)
        await page.set_viewport_size(viewport)

        user_agent = self._get_user_agent(args.user_agent)
        await page.set_extra_http_headers(
            {
                "User-Agent": user_agent,
                "Accept-Language": secure_random.choice(DEFAULT_ACCEPT_LANGUAGES),
            }
        )

        if hasattr(args, "custom_headers") and args.custom_headers:
            await page.set_extra_http_headers(args.custom_headers)

    def _get_user_agent(self, custom_user_agent: Optional[str] = None) -> str:
        """Get user agent string."""
        if custom_user_agent:
            return custom_user_agent
        return secrets.SystemRandom().choice(DEFAULT_USER_AGENTS)

    def _validate_args(self, args: ScrapeArgs) -> Optional[str]:
        """Valida argumentos do usuário antes do scraping."""
        url = getattr(args, "url", None)
        # Aceita tanto str quanto HttpUrl (Pydantic)
        url_str = str(url) if url is not None else None
        if not url_str:
            return "URL is required."
        if not (url_str.startswith("http://") or url_str.startswith("https://")):
            return "URL must be a valid HTTP/HTTPS address."
        if getattr(args, "timeout_seconds", 0) <= 0:
            return "Timeout must be greater than zero."
        if getattr(args, "grace_period_seconds", 1) < 0:
            return "Grace period must be zero or positive."
        return None

    def _fallback_requests_scrape(self, args: ScrapeArgs, previous_error: str) -> Optional[Dict[str, Any]]:
        """
        Fallback: tenta scraping simples via requests+BeautifulSoup se Playwright falhar por erro de infraestrutura.
        Só executa para erros de infraestrutura, não para HTTP 4xx/5xx do site.
        """
        try:
            import requests
            logger.info(f"Trying fallback requests scrape for {args.url}")
            headers = {
                "User-Agent": self._get_user_agent(args.user_agent),
                "Accept-Language": secrets.SystemRandom().choice(DEFAULT_ACCEPT_LANGUAGES),
            }
            if getattr(args, "custom_headers", None):
                headers.update(args.custom_headers)
            resp = requests.get(args.url, headers=headers, timeout=getattr(args, "timeout_seconds", 10))
            if not 200 <= resp.status_code < 300:
                return None  # Não faz fallback para HTTP error
            soup = BeautifulSoup(resp.text, "html.parser")
            elements_to_remove = set(DEFAULT_ELEMENTS_TO_REMOVE)
            if getattr(args, "custom_elements_to_remove", None):
                elements_to_remove.update(args.custom_elements_to_remove)
            for selector in elements_to_remove:
                for element in soup.select(selector):
                    element.decompose()
            content = soup.get_text(separator=" ", strip=True)
            if getattr(args, "max_length", None):
                content = truncate_content(content, int(args.max_length))
            return {
                "title": soup.title.string if soup.title else None,
                "final_url": resp.url,
                "content": content,
                "error": f"Fallback mode (requests): Playwright error: {previous_error}",
            }
        except Exception as e:
            logger.error(f"Fallback requests scrape failed for {args.url}: {e}")
            return None

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
