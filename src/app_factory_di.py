"""
Dependency Injection Module
Single Responsibility: Configure all dependency bindings for the application.
"""
from injector import Binder, Module, provider, singleton
from src.scraper.application.services.web_scraping_service import WebScrapingService
from src.scraper.application.services.fallback_orchestrator import FallbackOrchestrator
from src.scraper.infrastructure.circuit_breaker_pattern import CircuitBreakerPattern
from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
    ScrapingMetricsCollector,
)
from src.scraper.infrastructure.web_scraping.playwright_scraping_strategy import (
    PlaywrightScrapingStrategy,
)
from src.scraper.infrastructure.web_scraping.requests_scraping_strategy import (
    RequestsScrapingStrategy,
)
from src.settings import Settings


class AppModule(Module):
    def __init__(self, settings: Settings):
        self._settings = settings

    def configure(self, binder: Binder):
        binder.bind(Settings, to=self._settings, scope=singleton)

    @singleton
    @provider
    def provide_circuit_breaker(self, settings: Settings) -> CircuitBreakerPattern:
        return CircuitBreakerPattern(
            failure_threshold=settings.circuit_breaker_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_seconds,
        )

    @singleton
    @provider
    def provide_requests_strategy(self, settings: Settings) -> RequestsScrapingStrategy:
        return RequestsScrapingStrategy(config=settings)

    @singleton
    @provider
    def provide_playwright_strategy(
        self, settings: Settings
    ) -> PlaywrightScrapingStrategy:
        return PlaywrightScrapingStrategy(config=settings)

    @singleton
    @provider
    def provide_metrics_collector(self) -> ScrapingMetricsCollector:
        return ScrapingMetricsCollector()

    @singleton
    @provider
    def provide_fallback_orchestrator(
        self,
        playwright_strategy: PlaywrightScrapingStrategy,
        requests_strategy: RequestsScrapingStrategy,
        circuit_breaker: CircuitBreakerPattern,
        metrics_collector: ScrapingMetricsCollector,
    ) -> FallbackOrchestrator:
        return FallbackOrchestrator(
            playwright_strategy=playwright_strategy,
            requests_strategy=requests_strategy,
            circuit_breaker=circuit_breaker,
            metrics_collector=metrics_collector,
        )

    @singleton
    @provider
    def provide_web_scraping_service(
        self, orchestrator: FallbackOrchestrator
    ) -> WebScrapingService:
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        content_processor = ContentProcessingService()
        return WebScrapingService(
            orchestrator=orchestrator, content_processor=content_processor
        ) 