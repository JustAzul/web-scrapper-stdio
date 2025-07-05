"""
Defines the interface for a browser service, abstracting the underlying
web browser automation technology.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IBrowserService(ABC):
    """
    Interface for a service that provides browser automation capabilities.
    """

    @abstractmethod
    async def get_page_content(
        self,
        url: str,
        user_agent: Optional[str] = None,
        timeout: Optional[int] = None,
        wait_for_network_idle: bool = True,
        grace_period_seconds: float = 2.0,
        click_selector: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Retrieves the HTML content and final URL of a web page.

        Args:
            url: The URL to navigate to.
            user_agent: The user agent string to use.
            timeout: The timeout in seconds for the page load.
            wait_for_network_idle: Whether to wait for the network to be idle.
            grace_period_seconds: Grace period after load before returning.
            click_selector: An optional CSS selector to click before getting content.

        Returns:
            A tuple containing the page's HTML content and the final URL.
        """
        pass
