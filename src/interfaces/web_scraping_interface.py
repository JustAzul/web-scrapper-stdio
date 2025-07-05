"""
Interface for a web scraping service.

This interface defines the contract for any web scraping implementation,
ensuring a consistent API for content extraction regardless of the underlying
technology (e.g., Playwright, Requests).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class IWebScrapingService(ABC):
    """Abstract interface for a web scraping service."""

    @abstractmethod
    async def scrape_url(
        self,
        url: str,
        custom_elements_to_remove: Optional[List[str]] = None,
        custom_timeout: Optional[int] = None,
        grace_period_seconds: Optional[float] = None,
        user_agent: Optional[str] = None,
        wait_for_network_idle: bool = True,
        click_selector: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Scrapes a URL and returns the content.

        Args:
            url: The URL to scrape.
            custom_elements_to_remove: A list of CSS selectors for elements to remove.
            custom_timeout: A custom timeout in seconds for the request.
            grace_period_seconds: A grace period in seconds to wait for the page to load.
            user_agent: A custom user agent string.
            wait_for_network_idle: Whether to wait for the network to be idle.
            click_selector: A CSS selector for an element to click before scraping.

        Returns:
            A tuple containing (scraped_content, error_message).
            scraped_content will be None if an error occurred.
        """
        pass
