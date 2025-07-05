"""
Unit tests for Intelligent Fallback Scraper System.

This module tests the fallback strategy that:
1. Tries optimized Playwright first (with resource blocking)
2. Falls back to pure HTTP requests on "Page crashed" errors
3. Implements circuit breaker patterns for reliability

Following TDD: RED phase - writing tests first
"""
import logging
import time
from unittest.mock import AsyncMock, MagicMock, Mock, create_autospec, patch

import httpx
import pytest
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pytest_mock import MockerFixture
import asyncio

from src.scraper.application.services.fallback_orchestrator import FallbackOrchestrator
from src.scraper.infrastructure.circuit_breaker_pattern import CircuitBreakerPattern
from src.scraper.infrastructure.web_scraping.fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    IntelligentFallbackScraper,
    PageCrashedError,
    ScrapingError,
    ScrapingResult,
)
from src.scraper.infrastructure.web_scraping.playwright_scraping_strategy import (
    PlaywrightScrapingStrategy,
)
from src.scraper.infrastructure.web_scraping.requests_scraping_strategy import (
    RequestsScrapingStrategy,
)


# Reusable mock for a successful scraping result
def mock_success_result(content="<html>Success</html>", strategy="mock", attempts=1):
    return ScrapingResult(
        success=True,
        content=content,
        strategy_used=strategy,
        attempts=attempts,
        performance_metrics={"total_time": 0.1},
    )


# Reusable mock for a failed scraping result
def mock_failure_result(error="Test failure", strategy="mock", attempts=1):
    return ScrapingResult(
        success=False,
        content=None,
        strategy_used=strategy,
        attempts=attempts,
        error=error,
        performance_metrics={"total_time": 0.1},
    )


class TestIntelligentFallbackScraper:
    """Test suite for the Intelligent Fallback Scraper."""

    @pytest.fixture
    def config(self):
        """Fixture providing fallback configuration."""
        return FallbackConfig(
            playwright_timeout=30,
            requests_timeout=15,
            max_retries=3,
            circuit_breaker_threshold=5,
            enable_resource_blocking=True,
            blocked_resource_types=["image", "stylesheet", "font", "media"],
        )

    @pytest.fixture
    def scraper(self, config, mocker: MockerFixture):
        """Fixture providing an instance of the scraper with a mocked orchestrator."""
        # Use autospec to create a mock that has the same API as FallbackOrchestrator
        mock_orchestrator = mocker.create_autospec(
            FallbackOrchestrator, instance=True
        )

        # The mock's scrape_url needs to be an async function
        # that returns a valid ScrapingResult object.
        mock_orchestrator.scrape_url = AsyncMock(return_value=mock_success_result())

        # The IntelligentFallbackScraper reads the circuit_breaker from the orchestrator
        mock_orchestrator.circuit_breaker = mocker.create_autospec(
            CircuitBreakerPattern, instance=True
        )

        scraper = IntelligentFallbackScraper(
            config=config, orchestrator=mock_orchestrator
        )
        return scraper

    @pytest.mark.asyncio
    async def test_scrape_delegates_to_orchestrator(self, scraper):
        """
        Test that scrape_url correctly delegates to the orchestrator and
        returns its result.
        """
        # Arrange
        mock_result = mock_success_result()
        scraper._orchestrator.scrape_url.return_value = mock_result
        url = "http://example.com"
        headers = {"User-Agent": "test-agent"}

        # Act
        result = await scraper.scrape_url(url, custom_headers=headers)

        # Assert
        assert result == mock_result
        scraper._orchestrator.scrape_url.assert_called_once()
        call_args = scraper._orchestrator.scrape_url.call_args[0]
        request_obj = call_args[0]
        assert request_obj.url == url
        assert request_obj.user_agent == "test-agent"

    @pytest.mark.asyncio
    async def test_circuit_breaker_property(self, scraper):
        """Test that the circuit_breaker property correctly points to the orchestrator's circuit breaker."""
        # The scraper's circuit_breaker property should be the same object
        # as the one on the orchestrator it holds.
        assert scraper.circuit_breaker is scraper._orchestrator.circuit_breaker

    @pytest.mark.asyncio
    async def test_performance_metrics_are_updated(self, scraper):
        """Test that performance metrics are updated from the orchestrator's result."""
        # Arrange
        perf_metrics = {"total_time": 1.23, "specific_time": 0.8}
        mock_result = ScrapingResult(
            success=True,
            content="test",
            strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
            attempts=1,
            performance_metrics=perf_metrics,
        )
        scraper._orchestrator.scrape_url.return_value = mock_result

        # Act
        await scraper.scrape_url("http://example.com")

        # Assert
        assert scraper.performance_metrics == perf_metrics


class TestCircuitBreaker:
    """Test suite for the Circuit Breaker pattern."""

    @pytest.mark.parametrize("threshold", [3, 5])
    def test_circuit_breaker_opens_after_threshold(self, threshold):
        """Test that the circuit breaker opens after the failure threshold is met."""
        breaker = CircuitBreakerPattern(failure_threshold=threshold, recovery_timeout=10)
        for _ in range(threshold):
            breaker.record_failure()
        assert breaker.is_open is True

    def test_circuit_breaker_resets_on_success(self):
        """Test that the circuit breaker failure count resets after a success."""
        breaker = CircuitBreakerPattern(failure_threshold=3, recovery_timeout=10)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.get_failure_count() == 2
        breaker.record_success()
        assert breaker.get_failure_count() == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_enters_half_open_after_timeout(self):
        """Test that the circuit breaker goes into half-open state after the recovery timeout."""
        breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()
        assert breaker.is_open is True
        await asyncio.sleep(0.15)
        assert breaker.is_open is False  # Now in half-open state
        assert breaker.get_state() == "HALF-OPEN"

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_fully_after_success_in_half_open(self):
        """Test that a success in half-open state resets the circuit breaker."""
        breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()
        await asyncio.sleep(0.15)  # Let time pass for recovery

        # Explicitly trigger state transition before recording success
        assert breaker.get_state() == "HALF-OPEN"

        breaker.record_success()
        assert breaker.get_state() == "CLOSED"
        assert breaker.get_failure_count() == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_reopens_on_failure_in_half_open(self):
        """Test that a failure in half-open state re-opens the circuit breaker."""
        breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=0.1)
        breaker.record_failure()
        await asyncio.sleep(0.15)  # Enter half-open
        assert breaker.get_state() == "HALF-OPEN"
        breaker.record_failure()
        assert breaker.get_state() == "OPEN"


class TestScrapingResult:
    """Test suite for the ScrapingResult data class."""

    def test_scraping_result_creation(self):
        """Test successful creation of a ScrapingResult instance."""
        result = ScrapingResult(
            success=True,
            content="<p>Hello</p>",
            strategy_used="playwright",
            attempts=1,
            performance_metrics={"total_time": 0.5},
            final_url="https://final.url",
        )
        assert result.success is True
        assert result.content == "<p>Hello</p>"
        assert result.final_url == "https://final.url"

    def test_failed_scraping_result(self):
        """Test creation of a failed ScrapingResult instance."""
        result = ScrapingResult(
            success=False,
            content=None,
            error="Timeout",
            strategy_used="requests",
            attempts=3,
            performance_metrics={"total_time": 2.1},
        )
        assert result.success is False
        assert result.content is None
        assert result.error == "Timeout"
        assert result.attempts == 3


class TestFallbackStrategy:
    """Test suite for the FallbackStrategy enumeration."""

    def test_fallback_strategy_values(self):
        """Test FallbackStrategy enum values."""
        assert FallbackStrategy.PLAYWRIGHT_OPTIMIZED.value == "playwright_optimized"
        assert FallbackStrategy.REQUESTS_FALLBACK.value == "requests_fallback"
        assert FallbackStrategy.ALL_FAILED.value == "all_failed"


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_page_crashed_error(self):
        """Test PageCrashedError exception."""
        error = PageCrashedError("Page crashed during navigation")
        assert str(error) == "Page crashed during navigation"
        assert isinstance(error, ScrapingError)

    def test_scraping_error(self):
        """Test base ScrapingError exception."""
        error = ScrapingError("General scraping error")
        assert str(error) == "General scraping error"
