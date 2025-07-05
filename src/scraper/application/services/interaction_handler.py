"""
InteractionHandler - Single Responsibility: Element Interactions

Handles the element interaction responsibility extracted from
WebScrapingService.scrape_url following the Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Optional

from src.logger import get_logger
from src.scraper.application.contracts.browser_automation import BrowserAutomation
from src.scraper.application.services.scraping_request import ScrapingRequest

logger = get_logger(__name__)


@dataclass
class InteractionResult:
    """Dataclass for interaction results."""

    success: bool
    error: Optional[str] = None


class InteractionHandler:
    """Single Responsibility: Handle element clicks and interactions"""

    def __init__(self, browser_automation: BrowserAutomation):
        self.browser_automation = browser_automation
        self.logger = get_logger(__name__)

    async def handle_interaction(self, request: ScrapingRequest) -> InteractionResult:
        """
        Handles user interactions like clicking elements.
        """
        if not request.click_selector:
            return InteractionResult(success=True)

        try:
            self.logger.debug(f"Attempting to click selector: {request.click_selector}")
            click_success = await self.browser_automation.click_element(
                request.click_selector
            )

            if click_success:
                self.logger.debug(
                    f"Successfully clicked selector: {request.click_selector}"
                )
                return InteractionResult(success=True)
            else:
                warning_msg = f"Could not click selector '{request.click_selector}'"
                self.logger.warning(warning_msg)
                return InteractionResult(success=True, error=warning_msg)

        except Exception as e:
            warning_msg = f"Exception during click on '{request.click_selector}': {e}"
            self.logger.warning(warning_msg)
            return InteractionResult(success=True, error=warning_msg)
