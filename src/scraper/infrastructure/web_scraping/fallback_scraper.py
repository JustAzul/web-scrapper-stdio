"""
Intelligent Fallback Scraper Implementation.

This module implements a robust web scraping system with intelligent fallback:
1. Primary: Optimized Playwright with resource blocking
2. Fallback: Pure HTTP requests with httpx
3. Circuit breaker pattern for reliability
4. Exponential backoff retry mechanism
5. Performance metrics collection

Based on validated research from official Playwright documentation and real-world
implementations.
"""

import asyncio
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from injector import Injector
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import (
    Page,
    async_playwright,
)
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.core.constants import (
    DEFAULT_CONFIG_TIMEOUT,
    DEFAULT_FALLBACK_TIMEOUT,
    HTTP_CLIENT_ERROR_THRESHOLD,
    MILLISECONDS_PER_SECOND,
)
from src.logger import get_logger

if TYPE_CHECKING:
    from ...application.services.fallback_orchestrator import FallbackOrchestrator

logger = get_logger(__name__)


class FallbackStrategy(Enum):
    """Enumeration of available fallback strategies."""

    PLAYWRIGHT_OPTIMIZED = "playwright_optimized"
    REQUESTS_FALLBACK = "requests_fallback"
    ALL_FAILED = "all_failed"


class ScrapingError(Exception):
    """Base exception for scraping errors."""

    pass


class PageCrashedError(ScrapingError):
    """Exception raised when Playwright page crashes."""

    pass


@dataclass(frozen=True)
class FallbackConfig:
    """Configuration for the intelligent fallback scraper."""

    playwright_timeout: int = DEFAULT_CONFIG_TIMEOUT
    requests_timeout: int = DEFAULT_FALLBACK_TIMEOUT
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery_seconds: int = 30
    enable_resource_blocking: bool = True
    blocked_resource_types: List[str] = field(
        default_factory=lambda: ["image", "stylesheet", "font", "media", "websocket"]
    )

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.playwright_timeout < 0:
            raise ValueError("playwright_timeout must be non-negative")
        if self.requests_timeout < 0:
            raise ValueError("requests_timeout must be non-negative")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.circuit_breaker_threshold < 1:
            raise ValueError("circuit_breaker_threshold must be positive")
        if self.circuit_breaker_recovery_seconds < 1:
            raise ValueError("circuit_breaker_recovery_seconds must be positive")


@dataclass
class ScrapingResult:
    """Result of a scraping operation with detailed metadata."""

    success: bool
    content: Optional[str]
    strategy_used: FallbackStrategy
    attempts: int
    error: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None
    final_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass to a dictionary."""
        return asdict(self)


class IntelligentFallbackScraper:
    """
    Orchestrates web scraping with an intelligent fallback mechanism.
    This class is the main entry point for the scraping logic.

    REFATORADO: Agora delega para FallbackOrchestrator seguindo SRP
    """

    def __init__(
        self,
        config: Optional[FallbackConfig] = None,
        orchestrator: Optional["FallbackOrchestrator"] = None,
        injector: Optional[Injector] = None,
    ):
        """
        Initializes the scraper, either with an explicit orchestrator or by
        fetching one from the dependency injection container.
        """
        self.config = config or FallbackConfig()
        self.logger = logger
        self.performance_metrics: Dict[str, float] = {}

        if orchestrator:
            self._orchestrator = orchestrator
        elif injector:
            from ...application.services.fallback_orchestrator import (
                FallbackOrchestrator,
            )
            self._orchestrator = injector.get(FallbackOrchestrator)
        else:
            # This logic branch is for when an injector is not available,
            # allowing the creation of a default orchestrator.
            # This is useful for tests or standalone usage.
            from ...application.services.fallback_orchestrator import (
                FallbackOrchestrator,
            )
            self._orchestrator = FallbackOrchestrator(self.config)

        # Maintain backward compatibility for the circuit_breaker property
        self.circuit_breaker = self._orchestrator.circuit_breaker

    async def scrape_url(
        self, url: str, custom_headers: Optional[Dict[str, Any]] = None
    ) -> ScrapingResult:
        """
        Scrapes a URL by delegating the request to the configured orchestrator.

        This method ensures that the scraper's public interface remains consistent
        while correctly delegating the core logic to the orchestrator.
        """
        # Import locally to prevent circular dependencies at startup
        from ...application.services.scraping_request import ScrapingRequest

        # Construct the request object for the orchestrator
        user_agent = custom_headers.get("User-Agent") if custom_headers else None
        request = ScrapingRequest(url=url, user_agent=user_agent)

        # Delegate the actual scraping task to the orchestrator
        result = await self._orchestrator.scrape_url(request)

        # Correctly update performance metrics from the result for this specific scrape
        self.performance_metrics = result.performance_metrics or {}

        return result
