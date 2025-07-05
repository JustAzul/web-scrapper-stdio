"""
This module contains the ScrapingOrchestrator, which is the central service
for coordinating the web scraping process.
"""

from typing import Any, Dict

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

from src.core.constants import DEFAULT_TIMEOUT_SECONDS
from src.enums import OutputFormat
from src.logger import get_logger
from src.scraper.api.handlers.content_extractor import ContentExtractor
from src.scraper.api.handlers.output_formatter import OutputFormatter
from src.scraper.application.services.url_validator import URLValidator

logger = get_logger(__name__)


class ScrapingOrchestrator:
    """
    Orchestrates the scraping process by delegating to specialized services for
    each step of the process, from validation to content extraction.
    """

    def __init__(
        self,
        url_validator: URLValidator,
        content_extractor: ContentExtractor,
        output_formatter: OutputFormatter,
    ):
        """
        Initializes the orchestrator with its dependencies.

        Args:
            url_validator: A service to validate and normalize URLs.
            content_extractor: A service to extract content from a page.
            output_formatter: A service to format and truncate the final content.
        """
        self.url_validator = url_validator
        self.content_extractor = content_extractor
        self.output_formatter = output_formatter

    async def scrape_url(
        self, url: str, output_format: OutputFormat = OutputFormat.MARKDOWN, **kwargs
    ) -> Dict[str, Any]:
        """
        Orchestrates the scraping of a URL by validating it, extracting content,
        and formatting the output.
        """
        if not self.url_validator.validate(url):
            return {"error": "Invalid URL provided."}

        normalized_url = self.url_validator.normalize(url)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                response = await page.goto(
                    normalized_url,
                    timeout=(kwargs.get("custom_timeout") or DEFAULT_TIMEOUT_SECONDS) * 1000,
                )

                if response and response.status >= 400:
                    await browser.close()
                    return {
                        "title": None,
                        "content": None,
                        "error": f"HTTP error {response.status}",
                        "final_url": normalized_url,
                    }

                extraction_result = await self.content_extractor.extract(
                    page, config=kwargs
                )

                await browser.close()
        except PlaywrightError as e:
            logger.error(f"Error scraping {url}: {e}")
            error_message = str(e)
            if "net::ERR_NAME_NOT_RESOLVED" in error_message:
                error_message = f"Could not resolve domain: {url}"

            return {
                "title": None,
                "content": None,
                "error": error_message,
                "final_url": normalized_url,
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred while scraping {url}: {e}")
            return {
                "title": None,
                "content": None,
                "error": str(e),
                "final_url": normalized_url,
            }

        if extraction_result.error:
            return {
                "title": None,
                "content": None,
                "error": extraction_result.error,
                "final_url": normalized_url,
            }

        # The test mock for format() should handle the content correctly.
        formatted_content = self.output_formatter.format(
            extraction_result.clean_html, output_format, soup=extraction_result.soup
        )

        # The test mock for truncate() should handle the content correctly.
        truncated_content = self.output_formatter.truncate(
            formatted_content, kwargs.get("max_length")
        )

        return {
            "title": extraction_result.title,
            "content": truncated_content,
            "error": None,
            "final_url": normalized_url,
        }

    async def scrape(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Scrapes a given URL and returns the extracted content.

        Args:
            url: The URL to scrape.
            **kwargs: Additional configuration options.

        Returns:
            A dictionary containing the title, final URL, content, and any errors.
        """
        if not self.url_validator.validate(url):
            return {"error": "Invalid URL"}

        normalized_url = self.url_validator.normalize(url)

        extraction_result = await self.content_extractor.extract(
            normalized_url, **kwargs
        )

        if extraction_result.error:
            return {
                "title": extraction_result.title,
                "content": None,
                "error": extraction_result.error,
                "final_url": extraction_result.final_url,
            }

        formatted_content = self.output_formatter.format_and_truncate(
            extraction_result.content
        )

        return {
            "title": extraction_result.title,
            "content": formatted_content,
            "error": None,
            "final_url": extraction_result.final_url,
        }
