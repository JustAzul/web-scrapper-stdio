"""
Browser automation interfaces for dependency inversion.

These interfaces define the contracts that browser automation
implementations must satisfy, enabling easy testing and
swapping of implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class BrowserResponse:
    """Standardized response from browser navigation."""

    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    url: Optional[str] = None


@dataclass(frozen=True)
class BrowserConfiguration:
    """Browser configuration settings."""

    user_agent: str
    timeout_seconds: int
    viewport: Optional[Dict[str, int]] = None
    accept_language: Optional[str] = None


class NavigationResponse:
    """Data class for navigation responses."""

    def __init__(
        self, success: bool, url: Optional[str] = None, error: Optional[str] = None
    ):
        self.success = success
        self.url = url
        self.error = error


class BrowserAutomation(ABC):
    """Abstract base class for browser automation providers."""

    @abstractmethod
    async def navigate_to_url(self, url: str) -> NavigationResponse:
        """Navigates to the specified URL."""
        pass

    @abstractmethod
    async def wait_for_content_stabilization(self, timeout_seconds: int) -> bool:
        """Waits for the page content to stabilize."""
        pass

    @abstractmethod
    async def click_element(self, selector: str) -> bool:
        """Clicks an element specified by a selector."""
        pass

    @abstractmethod
    async def get_page_content(self) -> str:
        """Returns the full HTML content of the page."""
        pass

    @abstractmethod
    async def close(self):
        """Closes the browser and cleans up resources."""
        pass


class BrowserAutomationFactory(ABC):
    """Factory for creating browser automation instances."""

    @abstractmethod
    async def create_browser(self, config: BrowserConfiguration) -> BrowserAutomation:
        """
        Create a browser automation instance.

        Args:
            config: Browser configuration

        Returns:
            Browser automation instance
        """
        pass
