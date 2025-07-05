"""
ContentStabilizationHandler - Single Responsibility: Content Stabilization

Handles the content stabilization responsibility extracted from WebScrapingService.scrape_url
following the Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Optional

from src.logger import get_logger
from src.scraper.application.services.scraping_request import ScrapingRequest

logger = get_logger(__name__)


@dataclass
class StabilizationResult:
    """Result of content stabilization operation"""

    success: bool
    error: Optional[str]


class ContentStabilizationHandler:
    """
    Handles content stabilization and waiting for page readiness.

    Single Responsibility: Wait for content to stabilize and be ready for extraction

    Responsibilities:
    - Wait for content stabilization
    - Handle stabilization timeouts
    - Log stabilization status
    """

    def __init__(self):
        """Initialize content stabilization handler"""
        pass

    async def stabilize_content(
        self, browser_automation: object, request: ScrapingRequest, timeout_seconds: int
    ) -> StabilizationResult:
        """
        Wait for content to stabilize on the page.

        Args:
            browser_automation: Browser automation instance
            request: Scraping request containing configuration
            timeout_seconds: Timeout for stabilization

        Returns:
            StabilizationResult with success status and any error
        """
        try:
            logger.debug(f"Waiting for content to stabilize on {request.url}")

            # Wait for content stabilization using the browser interface
            content_stabilized = (
                await browser_automation.wait_for_content_stabilization(timeout_seconds)
            )

            if not content_stabilized:
                error_msg = f"[ERROR] Content did not stabilize within timeout for {request.url}."
                logger.warning(
                    f"Content did not stabilize within timeout for {request.url}"
                )
                return StabilizationResult(success=False, error=error_msg)

            logger.debug(f"Content stabilized successfully for {request.url}")
            return StabilizationResult(success=True, error=None)

        except Exception as e:
            error_msg = (
                f"[ERROR] Unexpected error during content stabilization: {str(e)}"
            )
            logger.warning(
                f"Unexpected error during content stabilization for {request.url}: {e}"
            )
            return StabilizationResult(success=False, error=error_msg)
