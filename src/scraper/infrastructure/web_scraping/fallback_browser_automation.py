"""
Fallback Browser Automation Implementation.

This module provides an adapter that integrates the fallback scraper
with the existing browser automation interface, enabling direct replacement
of the standard Playwright implementation with the fallback system.

Follows the Adapter pattern to maintain compatibility with existing code.
"""

from typing import Dict, List, Optional

from src.core.constants import DEFAULT_FALLBACK_TIMEOUT, HTTP_SUCCESS_STATUS
from src.logger import get_logger
from src.scraper.application.contracts.browser_automation import (
    BrowserAutomation,
    BrowserAutomationFactory,
    BrowserConfiguration,
    BrowserResponse,
)
from src.scraper.infrastructure.web_scraping.fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    IntelligentFallbackScraper,
)

logger = get_logger(__name__)


class FallbackBrowserAutomation(BrowserAutomation):
    """
    Adapter that integrates fallback scraper with browser automation
    interface.

    This class adapts the FallbackScraper to work with the existing
    browser automation interface, providing a consistent way to perform scraping
    """

    def __init__(
        self,
        scraper: IntelligentFallbackScraper,
        browser_config: BrowserConfiguration,
        fallback_config: FallbackConfig,
    ):
        """
        Initialize the fallback browser automation adapter.

        Args:
            scraper: Configured fallback scraper
            browser_config: Browser configuration from existing interface
            fallback_config: Fallback-specific configuration
        """
        self.scraper = scraper
        self.browser_config = browser_config
        self.fallback_config = fallback_config
        self._last_content: Optional[str] = None
        self._last_url: Optional[str] = None
        self._last_performance_metrics: Optional[Dict[str, float]] = None
        self._custom_headers: Optional[Dict[str, str]] = None

    async def navigate_to_url(self, url: str) -> BrowserResponse:
        """
        Navigate to URL using fallback strategy.

        Args:
            url: Target URL to navigate to

        Returns:
            BrowserResponse compatible with existing interface
        """
        try:
            logger.debug(f"Fallback browser navigating to: {url}")

            result = await self.scraper.scrape_url(
                url=url, custom_headers=self._custom_headers
            )

            self._last_content = result.content
            self._last_url = result.final_url or url
            self._last_performance_metrics = result.performance_metrics

            if result.success:
                status_code = HTTP_SUCCESS_STATUS
                if result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK:
                    status_code = HTTP_SUCCESS_STATUS
                elif result.strategy_used == FallbackStrategy.PLAYWRIGHT:
                    status_code = HTTP_SUCCESS_STATUS

                return BrowserResponse(
                    success=True,
                    content=result.content,
                    error=None,
                    status_code=status_code,
                    url=result.final_url or url,
                    performance_metrics=result.performance_metrics,
                )
            else:
                return BrowserResponse(
                    success=False,
                    content=None,
                    error=result.error,
                    status_code=None,
                    url=url,
                    performance_metrics=result.performance_metrics,
                )

        except Exception as e:
            logger.error(f"Fallback browser navigation failed for {url}: {e}")
            return BrowserResponse(
                success=False,
                content=None,
                error=f"Navigation failed: {str(e)}",
                status_code=None,
                url=url,
            )

    async def get_page_content(self) -> str:
        """
        Get current page HTML content from last navigation.

        Returns:
            HTML content as string, or empty string if no content available
        """
        if self._last_content is not None:
            return self._last_content
        else:
            logger.warning("No content available - navigate to a URL first")
            return ""

    async def wait_for_content_stabilization(self, timeout_seconds: int) -> bool:
        """
        Wait for page content to stabilize.

        For fallback browser, content is always considered stable since we're
        dealing with static HTTP responses or already-loaded Playwright content.

        Args:
            timeout_seconds: Maximum wait time (ignored in fallback mode)

        Returns:
            Always True for fallback browser
        """
        # In fallback mode, content is always "stable" since we get complete responses
        return True

    async def click_element(self, selector: str) -> bool:
        """
        Click element by CSS selector.

        Note: Element clicking is not supported in fallback mode since we're
        primarily using HTTP requests. This method returns False to indicate
        the operation is not supported.

        Args:
            selector: CSS selector (ignored in fallback mode)

        Returns:
            False - clicking not supported in fallback mode
        """
        logger.warning(
            f"Element clicking not supported in fallback mode (selector: {selector})"
        )
        return False

    async def close(self) -> None:
        """
        Close browser and cleanup resources.

        For fallback browser, this performs minimal cleanup since we don't
        maintain persistent browser connections.
        """
        logger.debug("Fallback browser cleanup completed")
        # Clear cached data
        self._last_content = None
        self._last_url = None
        self._last_performance_metrics = None
        self._custom_headers = None

    def set_custom_headers(self, headers: Dict[str, str]) -> None:
        """
        Set custom headers for HTTP requests.

        Args:
            headers: Dictionary of custom headers to include in requests
        """
        self._custom_headers = headers
        logger.debug(f"Custom headers set: {list(headers.keys())}")

    def get_last_performance_metrics(self) -> Optional[Dict[str, float]]:
        """
        Get performance metrics from the last navigation.

        Returns:
            Dictionary with performance metrics, or None if no metrics available
        """
        return self._last_performance_metrics

    def get_last_strategy_used(self) -> Optional[str]:
        """
        Get the strategy used in the last navigation.

        Returns:
            String indicating which strategy was used, or None if no navigation yet
        """
        return None


class FallbackBrowserFactory(BrowserAutomationFactory):
    """
    Factory for creating fallback browser automation instances.

    This factory creates FallbackBrowserAutomation instances that use the
    fallback scraper system while maintaining compatibility
    with the existing browser automation interface.
    """

    async def create_browser(self, config: BrowserConfiguration) -> BrowserAutomation:
        """
        Create fallback browser automation instance with configuration.

        Args:
            config: Browser configuration from existing interface

        Returns:
            Configured fallback browser automation instance
        """
        # Create fallback configuration based on browser config
        fallback_config = FallbackConfig(
            playwright_timeout=config.timeout_seconds,
            requests_timeout=max(
                DEFAULT_FALLBACK_TIMEOUT, config.timeout_seconds // 2
            ),  # Shorter timeout for HTTP
            max_retries=3,
            circuit_breaker_threshold=5,
            enable_resource_blocking=True,
            blocked_resource_types=[
                "image",
                "stylesheet",
                "font",
                "media",
                "websocket",
                "eventsource",
                "manifest",
            ],
        )

        # Create scraper with fallback config
        scraper = IntelligentFallbackScraper(config=fallback_config)

        # Create and return the adapter
        fallback_browser = FallbackBrowserAutomation(
            scraper=scraper,
            browser_config=config,
            fallback_config=fallback_config,
        )

        logger.info(
            f"Created fallback browser with timeout={config.timeout_seconds}s, "
            f"resource_blocking=enabled"
        )

        return fallback_browser

    def create_config(
        self,
        base_config: BrowserConfiguration,
        enable_blocking: bool = True,
        custom_blocked_types: Optional[List[str]] = None,
    ) -> FallbackConfig:
        """
        Create fallback configuration for specific use cases.

        Args:
            base_config: Base browser configuration
            enable_blocking: Whether to enable blocking
            custom_blocked_types: Custom list of resource types to block

        Returns:
            Fallback configuration
        """
        blocked_types = custom_blocked_types or [
            "image",
            "stylesheet",
            "font",
            "media",
            "websocket",
        ]

        if enable_blocking:
            # Add more resource types for maximum performance
            blocked_types.extend(["eventsource", "manifest", "texttrack", "other"])

        return FallbackConfig(
            playwright_timeout=base_config.timeout_seconds,
            requests_timeout=base_config.timeout_seconds // 2,
            max_retries=3,
            circuit_breaker_threshold=5,
            enable_resource_blocking=enable_blocking,
            blocked_resource_types=blocked_types,
        )
