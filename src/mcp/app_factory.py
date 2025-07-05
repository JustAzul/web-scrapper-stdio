from logging import Logger
from typing import Any

from pydantic import BaseModel, Field

from mcp.server import FastMCP, Tool
from src.scraper.application.services.content_processing_service import (
    ContentProcessingService,
)
from src.scraper.application.services.web_scraping_service import WebScrapingService
from src.scraper.infrastructure.web_scraping.browser_automation import BrowserAutomation
from src.scraper.infrastructure.web_scraping.circuit_breaker import CircuitBreaker
from src.scraper.infrastructure.web_scraping.fallback_orchestrator import (
    FallbackOrchestrator,
)
from src.scraper.infrastructure.web_scraping.fallback_scraper import (
    FallbackScraper,
)
from src.scraper.infrastructure.web_scraping.http_client import AsyncHttpClient
from src.scraper.infrastructure.web_scraping.scraper_config import ScraperConfig


class ScrapeWebInput(BaseModel):
    url: str = Field(..., description="The URL of the webpage to scrape.")
    # Add other fields from WebScrapingService.scrape_url method
    custom_elements_to_remove: list[str] | None = Field(
        None, description="A list of CSS selectors for elements to remove."
    )
    custom_timeout: int | None = Field(
        None, description="A custom timeout in seconds for the request."
    )
    grace_period_seconds: float = Field(
        2.0, description="A grace period in seconds to wait for the page to load."
    )
    max_length: int | None = Field(
        None, description="The maximum length of the scraped content."
    )
    user_agent: str | None = Field(None, description="A custom user agent string.")
    wait_for_network_idle: bool = Field(
        True, description="Whether to wait for the network to be idle."
    )
    output_format: str = Field(
        "markdown", description="The output format for the scraped content."
    )
    click_selector: str | None = Field(
        None, description="A CSS selector for an element to click before scraping."
    )


class ScrapeWebTool(Tool):
    """A tool for scraping web pages."""

    name: str = "scrape_web"
    description: str = "Scrapes the specified URL and returns its content."
    args_schema = ScrapeWebInput
    service: WebScrapingService

    def __init__(self, service: WebScrapingService):
        super().__init__()
        self.service = service

    async def __call__(self, **kwargs: Any) -> Any:
        return await self.service.scrape_url(**kwargs)


def create_browser_automation(logger: Logger) -> BrowserAutomation:
    """Factory function to create a BrowserAutomation instance."""
    return BrowserAutomation(logger)


def create_app(logger: Logger) -> FastMCP:
    """
    Creates and configures the MCP application server with all dependencies.
    """
    # Create dependent services
    http_client = AsyncHttpClient()
    scraper_config = ScraperConfig()
    circuit_breaker = CircuitBreaker()
    content_processor = ContentProcessingService(logger=logger)

    # Create the fallback scraper
    fallback_scraper = FallbackScraper(
        client=http_client, config=scraper_config, logger=logger
    )

    # Create the fallback orchestrator with the factory
    orchestrator = FallbackOrchestrator(
        primary_scraper=fallback_scraper,
        browser_automation_factory=lambda: create_browser_automation(logger),
        circuit_breaker=circuit_breaker,
        logger=logger,
    )

    # Create the main web scraping service
    web_scraping_service = WebScrapingService(
        content_processor=content_processor, orchestrator=orchestrator
    )

    # Create the tool and the MCP App
    scrape_web_tool = ScrapeWebTool(service=web_scraping_service)

    app = FastMCP(
        tools=[scrape_web_tool],
        title="MCP Web Scrapper",
    )
    logger.info("Service dependencies initialized and app created.")
    return app
