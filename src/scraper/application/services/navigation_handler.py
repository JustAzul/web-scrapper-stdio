"""
NavigationHandler - Single Responsibility: URL Navigation

Handles the navigation responsibility extracted from WebScrapingService.scrape_url
following the Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Optional

from src.logger import get_logger
from src.scraper.application.contracts.browser_automation import (
    BrowserAutomation,
    BrowserAutomationFactory,
)
from src.scraper.application.services.scraping_configuration_service import (
    ScrapingConfigurationService,
)
from src.scraper.application.services.scraping_request import ScrapingRequest
from src.scraper.infrastructure.web_scraping.rate_limiting import apply_rate_limiting

logger = get_logger(__name__)


@dataclass
class NavigationResult:
    """Result of navigation operation"""

    success: bool
    final_url: str
    browser_automation: Optional[BrowserAutomation]
    error: Optional[str]


class NavigationHandler:
    """
    Handles URL navigation and browser setup.

    Single Responsibility: Navigate to URLs and set up browser instances

    Responsibilities:
    - Apply rate limiting
    - Create browser instances
    - Navigate to target URLs
    - Handle navigation errors
    - Extract final URLs (after redirects)
    """

    def __init__(
        self,
        browser_factory: BrowserAutomationFactory,
        configuration_service: ScrapingConfigurationService,
    ):
        """
        Initialize navigation handler with dependencies.

        Args:
            browser_factory: Factory for creating browser automation instances
            configuration_service: Configuration management service
        """
        self.browser_factory = browser_factory
        self.configuration_service = configuration_service

    async def navigate(self, request: ScrapingRequest) -> NavigationResult:
        """
        Handles URL navigation and browser setup.

        Returns:
            NavigationResult with success status, final URL,
            browser instance, and any error
        """
        browser_automation = None
        try:
            # Get configuration for this specific request
            actual_timeout = request.get_effective_timeout()
            browser_config = self.configuration_service.get_browser_config(
                custom_user_agent=request.user_agent,
                timeout_seconds=actual_timeout,
            )

            # Create a new browser instance for this request
            browser_automation = await self.browser_factory.create_browser(
                browser_config
            )

            # Apply rate limiting
            await apply_rate_limiting(request.url)

            # Navigate to URL
            logger.debug(f"Navigating to URL: {request.url}")
            navigation_response = await browser_automation.navigate_to_url(request.url)

            if not navigation_response.success:
                return NavigationResult(
                    success=False,
                    final_url=request.url,
                    browser_automation=browser_automation,
                    error=navigation_response.error,
                )

            # Extract the final URL from browser response
            # (handles redirects and normalization)
            final_url = navigation_response.url or request.url

            return NavigationResult(
                success=True,
                final_url=final_url,
                browser_automation=browser_automation,
                error=None,
            )

        except Exception as e:
            logger.warning(f"Unexpected error during navigation to {request.url}: {e}")
            return NavigationResult(
                success=False,
                final_url=request.url,
                browser_automation=browser_automation,
                error=f"[ERROR] Navigation failed: {str(e)}",
            )
