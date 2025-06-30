"""Web Scraping Service for orchestrating the complete web scraping workflow.

This service implements the Single Responsibility Principle by focusing solely on
orchestrating the web scraping process, extracted from the large extract_text_from_url function.

REFACTORED VERSION: Now uses ScrapingRequest internally while maintaining
backward compatibility with the original 10-parameter interface.
"""

import asyncio
from typing import Any, Dict, List, Optional

from src.logger import Logger
from src.output_format_handler import OutputFormat
from src.scraper.application.contracts.browser_automation import BrowserAutomation
from src.scraper.application.services.content_processing_service import (
    ContentProcessingService,
)
from src.scraper.application.services.scraping_configuration_service import (
    ScrapingConfigurationService,
)
from src.scraper.application.services.scraping_request import ScrapingRequest
from src.scraper.infrastructure.web_scraping.rate_limiting import apply_rate_limiting

logger = Logger(__name__)


class WebScrapingService:
    """
    Orchestrates the web scraping workflow.
    This service handles the high-level process of scraping a URL, including
    configuration, browser interaction, and content processing.
    """

    def __init__(
        self,
        browser_factory: any,  # Should be a factory or provider for BrowserAutomation
        content_processor: ContentProcessingService,
        configuration_service: ScrapingConfigurationService,
    ):
        """
        Initializes the web scraping service with its dependencies.
        """
        self.browser_factory = browser_factory
        self.content_processor = content_processor
        self.configuration_service = configuration_service
        self.logger = logger

    async def scrape_url(
        self,
        url: str,
        custom_elements_to_remove: Optional[List[str]] = None,
        custom_timeout: Optional[int] = None,
        grace_period_seconds: float = 2.0,
        max_length: Optional[int] = None,
        user_agent: Optional[str] = None,
        wait_for_network_idle: bool = True,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        click_selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates the complete web scraping workflow by converting legacy
        parameters into a ScrapingRequest and delegating to the internal method.
        """
        request = ScrapingRequest(
            url=url,
            timeout_seconds=custom_timeout,
            custom_elements_to_remove=custom_elements_to_remove,
            grace_period_seconds=grace_period_seconds,
            max_length=max_length,
            user_agent=user_agent,
            wait_for_network_idle=wait_for_network_idle,
            output_format=output_format,
            click_selector=click_selector,
        )
        return await self._scrape_with_request(request)

    async def _scrape_with_request(self, request: ScrapingRequest) -> Dict[str, Any]:
        browser_automation: Optional[BrowserAutomation] = None
        try:
            await apply_rate_limiting(request.url)

            browser_config = self.configuration_service.get_browser_config(
                custom_user_agent=request.user_agent,
                timeout_seconds=request.timeout_seconds,
            )
            browser_automation = await self.browser_factory.create_browser(
                browser_config
            )

            self.logger.debug(f"Navigating to URL: {request.url}")
            nav_response = await browser_automation.navigate_to_url(request.url)
            if not nav_response.success:
                return {
                    "error": nav_response.error,
                    "final_url": request.url,
                    "content": None,
                    "title": None,
                }

            final_url = nav_response.url or request.url
            self.logger.debug(f"Waiting for content to stabilize on {final_url}")
            await browser_automation.wait_for_content_stabilization(
                browser_config.timeout_seconds
            )

            if request.click_selector:
                await browser_automation.click_element(request.click_selector)
                await asyncio.sleep(request.grace_period_seconds)  # Wait after click

            html_content = await browser_automation.get_page_content()

            title, clean_html, text_content, error = (
                self.content_processor.process_html(
                    html_content,
                    self.configuration_service.get_elements_to_remove(
                        request.custom_elements_to_remove
                    ),
                    final_url,
                )
            )
            if error:
                return {
                    "error": error,
                    "final_url": final_url,
                    "content": None,
                    "title": title,
                }

            formatted_content = self.content_processor.format_content(
                title=title,
                html_content=clean_html,
                text_content=text_content,
                output_format=request.output_format,
                max_length=request.max_length,
            )

            return {
                "title": title,
                "final_url": final_url,
                "content": formatted_content,
                "error": None,
            }
        except Exception as e:
            self.logger.warning(f"Unexpected error for {request.url}: {e}")
            return {
                "error": str(e),
                "final_url": request.url,
                "content": None,
                "title": None,
            }
        finally:
            if browser_automation:
                await browser_automation.close()
