"""
FallbackOrchestrator - Orchestration of fallback scraping responsibilities
Part of refactoring T003 - Break up IntelligentFallbackScraper following SRP
"""

import time
from typing import Any, Dict, Optional

import httpx
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.logger import get_logger

from ...infrastructure.circuit_breaker_pattern import CircuitBreakerPattern
from ...infrastructure.monitoring.scraping_metrics_collector import (
    ScrapingMetricsCollector,
)
from ...infrastructure.retry_strategy_pattern import RetryStrategyPattern
from ...infrastructure.web_scraping.fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    ScrapingResult,
)
from ...infrastructure.web_scraping.playwright_scraping_strategy import (
    PlaywrightScrapingStrategy,
)
from ...infrastructure.web_scraping.requests_scraping_strategy import (
    RequestsScrapingStrategy,
)
from .scraping_request import ScrapingRequest
from injector import inject

logger = get_logger(__name__)


@inject
class FallbackOrchestrator:
    """
    Orchestrates scraping attempts with a fallback mechanism between different
    strategies.
    """

    @inject
    def __init__(
        self,
        playwright_strategy: PlaywrightScrapingStrategy,
        requests_strategy: RequestsScrapingStrategy,
        circuit_breaker: CircuitBreakerPattern,
        metrics_collector: ScrapingMetricsCollector,
    ):
        """Initializes the orchestrator with scraping strategies and helpers."""
        self.playwright_strategy = playwright_strategy
        self.requests_strategy = requests_strategy
        self.circuit_breaker = circuit_breaker
        self.metrics_collector = metrics_collector

    async def scrape_url(self, request: ScrapingRequest) -> ScrapingResult:
        """
        Executes scraping with intelligent fallback

        Args:
            request: Object with all request parameters

        Returns:
            Scraping result with metadata
        """
        start_time = self.metrics_collector.start_operation()
        attempts = 0

        # Build headers from the request
        custom_headers = {}
        if request.user_agent:
            custom_headers["User-Agent"] = request.user_agent

        # Check circuit breaker
        if self.circuit_breaker.is_open:
            error_msg = "Circuit breaker is open. Service is temporarily unavailable."

            self.metrics_collector.record_scraping_failure(
                start_time=start_time, error_message=error_msg, attempts=attempts
            )

            return ScrapingResult(
                success=False,
                content=None,
                strategy_used=FallbackStrategy.ALL_FAILED,
                attempts=attempts,
                error=error_msg,
                performance_metrics={"total_time": time.time() - start_time},
            )

        # Strategy 1: Playwright
        try:
            attempts += 1
            content = await self.playwright_strategy.scrape_url(request, custom_headers)
            self.circuit_breaker.record_success()

            self.metrics_collector.record_scraping_success(
                start_time=start_time,
                strategy_used="playwright_optimized",
                attempts=attempts,
                final_url=request.url,
                content_size=len(content) if content else 0,
            )

            return ScrapingResult(
                success=True,
                content=content,
                strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
                attempts=attempts,
                performance_metrics={"total_time": time.time() - start_time},
                final_url=request.url,
            )

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            logger.warning(f"Playwright strategy failed for {request.url}: {e}")
            self.circuit_breaker.record_failure()
        except ImportError as e:
            logger.error(f"Playwright not available: {e}")
            self.circuit_breaker.record_failure()
        except Exception as e:
            logger.error(
                f"Unexpected error in Playwright strategy for {request.url}: {e}"
            )
            self.circuit_breaker.record_failure()

        # Strategy 2: Fallback to requests
        try:
            attempts += 1
            content = await self.requests_strategy.scrape_url(
                request.url, custom_headers
            )
            self.circuit_breaker.record_success()

            self.metrics_collector.record_scraping_success(
                start_time=start_time,
                strategy_used="requests_fallback",
                attempts=attempts,
                final_url=request.url,
                content_size=len(content) if content else 0,
            )

            return ScrapingResult(
                success=True,
                content=content,
                strategy_used=FallbackStrategy.REQUESTS_FALLBACK,
                attempts=attempts,
                performance_metrics={"total_time": time.time() - start_time},
                final_url=request.url,
            )
        except httpx.HTTPStatusError as e:
            self.circuit_breaker.record_failure()
            error_msg = f"HTTP error {e.response.status_code} for url {e.request.url}"
            logger.warning(error_msg)
            return ScrapingResult(
                success=False,
                content=None,
                strategy_used=FallbackStrategy.ALL_FAILED,
                attempts=attempts,
                error=error_msg,
                performance_metrics={"total_time": time.time() - start_time},
            )

        except Exception as e:
            self.circuit_breaker.record_failure()
            error_msg = str(e)

            self.metrics_collector.record_scraping_failure(
                start_time=start_time, error_message=error_msg, attempts=attempts
            )

            return ScrapingResult(
                success=False,
                content=None,
                strategy_used=FallbackStrategy.ALL_FAILED,
                attempts=attempts,
                error=error_msg,
                performance_metrics={"total_time": time.time() - start_time},
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Returns metrics from the last operation"""
        return self.metrics_collector.get_last_metrics()

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Returns the status of the circuit breaker"""
        return {
            "state": self.circuit_breaker.get_state(),
            "failure_count": self.circuit_breaker.get_failure_count(),
            "is_open": self.circuit_breaker.is_open,
        }
