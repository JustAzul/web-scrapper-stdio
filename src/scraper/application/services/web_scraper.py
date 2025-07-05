"""
RefactoredWebScrapingService - Orchestrates specialized handlers following SRP

This is the refactored version of WebScrapingService that uses specialized handlers
instead of a monolithic scrape_url method with 10 parameters.
"""

from typing import Any, Dict

from src.core.constants import DEFAULT_TIMEOUT_SECONDS
from src.logger import get_logger
from src.scraper.application.services.content_extraction_handler import (
    ContentExtractionHandler,
)
from src.scraper.application.services.content_stabilization_handler import (
    ContentStabilizationHandler,
)
from src.scraper.application.services.interaction_handler import InteractionHandler
from src.scraper.application.services.navigation_handler import NavigationHandler
from src.scraper.application.services.scraping_request import ScrapingRequest

logger = get_logger(__name__)


class RefactoredWebScrapingService:
    """
    Refactored web scraping service using specialized handlers.

    This service follows SRP by delegating specific responsibilities to
    specialized handlers:
    - NavigationHandler: URL navigation and browser setup
    - ContentStabilizationHandler: Content stabilization
    - InteractionHandler: Element interactions
    - ContentExtractionHandler: Content extraction and processing

    This design eliminates the 10-parameter method and improves maintainability.
    """

    def __init__(
        self,
        navigation_handler: NavigationHandler,
        stabilization_handler: ContentStabilizationHandler,
        interaction_handler: InteractionHandler,
        extraction_handler: ContentExtractionHandler,
    ):
        """
        Initialize the refactored web scraping service with specialized handlers.

        Args:
            navigation_handler: Handles URL navigation and browser setup
            stabilization_handler: Handles content stabilization
            interaction_handler: Handles element interactions
            extraction_handler: Handles content extraction and processing
        """
        self.navigation_handler = navigation_handler
        self.stabilization_handler = stabilization_handler
        self.interaction_handler = interaction_handler
        self.extraction_handler = extraction_handler

    async def scrape(self, request: ScrapingRequest) -> Dict[str, Any]:
        """
        Orchestrate the complete web scraping workflow using specialized handlers.

        This method now takes a single ScrapingRequest parameter
        instead of 10 individual parameters, following the Parameter Object pattern.
        """
        logger.info(f"Starting scraping for URL: {request.url}")
        browser_automation = None

        try:
            # Step 1: Navigate to URL
            navigation_result = await self.navigation_handler.navigate(request)

            if not navigation_result.success:
                return {
                    "title": None,
                    "final_url": request.url,
                    "content": None,
                    "error": navigation_result.error,
                }

            browser_automation = navigation_result.browser_automation
            final_url = navigation_result.final_url

            # Step 2: Wait for content stabilization
            timeout_seconds = request.get_effective_timeout() or DEFAULT_TIMEOUT_SECONDS
            stabilization_result = await self.stabilization_handler.stabilize_content(
                browser_automation, request, timeout_seconds
            )

            if not stabilization_result.success:
                return {
                    "title": None,
                    "final_url": final_url,
                    "content": None,
                    "error": stabilization_result.error,
                }

            # Step 3: Handle element interactions
            interaction_result = await self.interaction_handler.handle_interactions(
                browser_automation, request
            )

            # Note: Interaction failures are non-critical, so we continue even if
            # they fail
            if interaction_result.error:
                logger.debug(f"Interaction warning: {interaction_result.error}")

            # Step 4: Extract and process content
            elements_to_remove = request.get_elements_to_remove()
            extraction_result = (
                await self.extraction_handler.extract_and_process_content(
                    browser_automation, request, final_url, elements_to_remove
                )
            )

            if not extraction_result.success:
                return {
                    "title": extraction_result.title,
                    "final_url": final_url,
                    "content": None,
                    "error": extraction_result.error,
                }

            # Success - return extracted content
            return {
                "title": extraction_result.title,
                "final_url": final_url,
                "content": extraction_result.content,
                "error": None,
            }

        except Exception as e:
            logger.warning(f"Unexpected error during scraping of {request.url}: {e}")
            return {
                "title": None,
                "final_url": request.url,
                "content": None,
                "error": f"[ERROR] An unexpected error occurred: {str(e)}",
            }
        finally:
            # Always cleanup browser resources
            if browser_automation:
                try:
                    await browser_automation.close()
                except Exception as cleanup_error:
                    logger.warning(f"Error during browser cleanup: {cleanup_error}")
