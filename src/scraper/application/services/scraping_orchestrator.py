"""
This module contains the ScrapingOrchestrator, which is the central service
for coordinating the web scraping process.
"""

from typing import Any, Dict


class ScrapingOrchestrator:
    """
    Orchestrates the scraping process by delegating to specialized services for
    each step of the process, from validation to content extraction.
    """

    def __init__(
        self, url_validator=None, content_extractor=None, output_formatter=None
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
