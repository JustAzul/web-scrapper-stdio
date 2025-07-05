"""
Application Factory
Single Responsibility: Create and configure the application instance.
"""
from injector import Injector
from src.app_factory_di import AppModule
from src.scraper.application.services.web_scraping_service import WebScrapingService
from src.settings import Settings


async def create_app_dependencies(settings: Settings) -> tuple[WebScrapingService, Settings]:
    """
    Creates and returns the application's core dependencies.
    This factory is now responsible only for DI and dependency creation,
    not for instantiating the session itself.
    """
    injector = Injector(AppModule(settings))
    web_scraper = injector.get(WebScrapingService)

    # Asynchronously initialize components that require it.
    await web_scraper.orchestrator.playwright_strategy.initialize()

    return web_scraper, settings