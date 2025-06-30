"""
Intelligent Fallback Scraper Implementation.

This module implements a robust web scraping system with intelligent fallback:
1. Primary: Optimized Playwright with resource blocking
2. Fallback: Pure HTTP requests with httpx
3. Circuit breaker pattern for reliability
4. Exponential backoff retry mechanism
5. Performance metrics collection

Based on validated research from official Playwright documentation and real-world implementations.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    Page,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from src.core.constants import (
    DEFAULT_CONFIG_TIMEOUT,
    DEFAULT_FALLBACK_TIMEOUT,
    HTTP_CLIENT_ERROR_THRESHOLD,
    MILLISECONDS_PER_SECOND,
)
from src.logger import Logger

logger = Logger(__name__)


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


class IntelligentFallbackScraper:
    """
    Orchestrates web scraping with an intelligent fallback mechanism.
    This class is the main entry point for the scraping logic.

    REFATORADO: Agora delega para FallbackOrchestrator seguindo SRP
    """

    def __init__(self, config: FallbackConfig):
        self.config = config
        self.logger = Logger(__name__)
        self.performance_metrics: Dict[str, float] = {}

        # Delegação para orquestrador refatorado
        from ...application.services.fallback_orchestrator import FallbackOrchestrator

        self._orchestrator = FallbackOrchestrator(config=config)

        # Mantém compatibilidade com propriedades antigas
        self.circuit_breaker = self._orchestrator.circuit_breaker

    async def scrape_url(
        self, url: str, custom_headers: Optional[Dict[str, Any]] = None
    ) -> ScrapingResult:
        """
        Faz scraping de URL usando orquestrador refatorado
        Mantém compatibilidade total com interface original
        """
        # Delega para orquestrador refatorado
        result = await self._orchestrator.scrape_url(url, custom_headers)

        # Atualiza métricas de performance para compatibilidade
        if result.performance_metrics:
            self.performance_metrics.update(result.performance_metrics)

        return result

    async def _scrape_with_playwright(
        self, url: str, headers: Optional[Dict[str, Any]]
    ) -> str:
        """
        Scrape URL using optimized Playwright with resource blocking.

        Args:
            url: URL to scrape
            headers: Optional custom headers for requests

        Returns:
            HTML content as string

        Raises:
            PageCrashedError: If page crashes
            PlaywrightError: For other Playwright errors
        """
        async with async_playwright() as p:
            # Launch browser with optimized settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                ],
            )

            try:
                context = await browser.new_context()
                page = await context.new_page()

                # Configure resource blocking if enabled
                if self.config.enable_resource_blocking:
                    await self._setup_resource_blocking(page)

                # Navigate with retries and exponential backoff
                content = await self._navigate_with_retries(page, url)

                # Clean and extract content
                cleaned_content = self._clean_html_content(content)

                return cleaned_content

            finally:
                await browser.close()

    async def _setup_resource_blocking(self, page: Page) -> None:
        """Setup aggressive resource blocking for performance."""

        async def handle_route(route):
            resource_type = route.request.resource_type
            if resource_type in self.config.blocked_resource_types:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", handle_route)

    async def _navigate_with_retries(self, page: Page, url: str) -> str:
        """Navigate to URL with exponential backoff retries."""
        for attempt in range(self.config.max_retries):
            try:
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.config.playwright_timeout
                    * MILLISECONDS_PER_SECOND,  # Use named constant instead of magic number 1000
                )

                if (
                    not response or response.status >= HTTP_CLIENT_ERROR_THRESHOLD
                ):  # Use named constant instead of magic number 400
                    raise PlaywrightError(
                        f"HTTP {response.status if response else 'Unknown'}"
                    )

                return await page.content()

            except (PlaywrightTimeoutError, PlaywrightError) as e:
                if "Page crashed" in str(e):
                    raise PageCrashedError(f"Page crashed during navigation: {e}")

                if attempt < self.config.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, etc.
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise e

    async def _scrape_with_requests(
        self, url: str, headers: Optional[Dict[str, Any]]
    ) -> str:
        """
        Scrape URL using pure HTTP requests as fallback.

        Args:
            url: URL to scrape
            headers: Optional custom headers

        Returns:
            HTML content as string
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; IntelligentScraper/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        if headers:
            headers.update(headers)

        async with httpx.AsyncClient(timeout=self.config.requests_timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            # Clean and extract content
            cleaned_content = self._clean_html_content(response.text)
            return cleaned_content

    def _clean_html_content(self, html_content: str) -> str:
        """
        Clean HTML content by removing unwanted elements.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned HTML content
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        unwanted_tags = [
            "script",
            "style",
            "nav",
            "footer",
            "aside",
            "header",
            "form",
            "button",
            "input",
            "select",
            "textarea",
            "label",
            "iframe",
        ]

        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        return str(soup)

    def _clean_html(self, html_content: str) -> str:
        """Removes unwanted tags from HTML content."""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "lxml")
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()
        # Optional: Add more cleaning logic here if needed
        return str(soup)
