"""
Defines the abstract base class for all scraping strategies.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.scraper.application.services.scraping_request import ScrapingRequest


class ScrapingStrategy(ABC):
    """Abstract Base Class for a scraping strategy."""

    @abstractmethod
    async def scrape_url(
        self, request: ScrapingRequest, headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Scrapes a URL and returns the page content.

        Args:
            request: The scraping request object.
            headers: Optional dictionary of headers to use.

        Returns:
            The cleaned HTML content of the page.
        """
        raise NotImplementedError
