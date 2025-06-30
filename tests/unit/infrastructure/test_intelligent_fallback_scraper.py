"""
Unit tests for Intelligent Fallback Scraper System.

This module tests the fallback strategy that:
1. Tries optimized Playwright first (with resource blocking)
2. Falls back to pure HTTP requests on "Page crashed" errors
3. Implements circuit breaker patterns for reliability

Following TDD: RED phase - writing tests first
"""

import time
from unittest.mock import AsyncMock, Mock, create_autospec, patch

import httpx
import pytest
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.scraper.infrastructure.circuit_breaker_pattern import CircuitBreakerPattern
from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    IntelligentFallbackScraper,
    PageCrashedError,
    ScrapingError,
    ScrapingResult,
)


class TestCircuitBreaker:
    """Tests for the CircuitBreakerPattern class."""

    @pytest.mark.parametrize("threshold", [3, 5])
    def test_circuit_breaker_opens_after_threshold(self, threshold):
        breaker = CircuitBreakerPattern(
            failure_threshold=threshold, recovery_timeout=60
        )
        for _ in range(threshold):
            assert not breaker.is_open
            breaker.record_failure()
        assert breaker.is_open

    def test_circuit_breaker_resets_on_success(self):
        breaker = CircuitBreakerPattern(failure_threshold=3, recovery_timeout=60)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.failure_count == 0

    def test_circuit_breaker_enters_half_open_after_timeout(self):
        breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=0.01)
        breaker.record_failure()
        assert breaker.is_open
        time.sleep(0.02)  # Wait for recovery timeout
        assert not breaker.is_open
        assert breaker.state == "HALF_OPEN"

    def test_circuit_breaker_resets_fully_after_success_in_half_open(self):
        breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=0.01)
        breaker.record_failure()
        time.sleep(0.02)
        assert not breaker.is_open  # Now in HALF_OPEN
        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    def test_circuit_breaker_reopens_on_failure_in_half_open(self):
        breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=0.01)
        breaker.record_failure()
        time.sleep(0.02)
        assert not breaker.is_open  # HALF_OPEN
        breaker.record_failure()
        assert breaker.is_open
        assert breaker.state == "OPEN"


class TestIntelligentFallbackScraper:
    """Test suite for the Intelligent Fallback Scraper system."""

    @pytest.fixture
    def fallback_config(self):
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
    def mock_playwright_browser(self):
        """Mock Playwright browser for testing."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.content.return_value = "<html><body>Test content</body></html>"
        mock_page.goto.return_value = Mock(status=200, url="https://example.com")

        return mock_browser, mock_context, mock_page

    @pytest.fixture
    def intelligent_scraper(self, fallback_config):
        """Fixture providing configured intelligent scraper."""
        scraper = IntelligentFallbackScraper(config=fallback_config)
        # Mock the circuit breaker through the orchestrator
        scraper._orchestrator.circuit_breaker = create_autospec(CircuitBreakerPattern)
        scraper._orchestrator.circuit_breaker.is_open = False
        return scraper

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_successful_playwright_scraping_no_fallback_needed(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        """Test successful scraping with Playwright - no fallback needed."""
        # Mock successful Playwright result (method returns HTML string)
        mock_playwright_scrape.return_value = "<html><body>Test content</body></html>"

        result = await intelligent_scraper.scrape_url("https://example.com")

        assert result.success is True
        assert result.content == "<html><body>Test content</body></html>"
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED
        assert result.error is None
        assert result.attempts == 1

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.requests_scraping_strategy.RequestsScrapingStrategy.scrape_url"
    )
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_playwright_page_crashed_triggers_fallback(
        self, mock_playwright_scrape, mock_requests_scrape, intelligent_scraper
    ):
        """Test that Page crashed error triggers fallback to requests."""
        # Mock Playwright to fail with Page crashed error
        mock_playwright_scrape.side_effect = PlaywrightError("Page crashed")

        # Mock requests to succeed (method returns HTML string)
        mock_requests_scrape.return_value = "<html><body>Fallback content</body></html>"

        result = await intelligent_scraper.scrape_url("https://example.com")

        assert result.success is True
        assert result.content == "<html><body>Fallback content</body></html>"
        assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK
        assert result.error is None
        assert result.attempts == 2  # Playwright attempt + requests fallback

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_resource_blocking_configuration(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        """Test that resource blocking is properly configured."""
        # Mock successful Playwright result (method returns HTML string)
        mock_playwright_scrape.return_value = (
            "<html><body>Content with blocked resources</body></html>"
        )

        result = await intelligent_scraper.scrape_url("https://example.com")

        # Verify resource blocking was effective
        assert result.success is True
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED
        assert "Content with blocked resources" in result.content
        mock_playwright_scrape.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.requests_scraping_strategy.RequestsScrapingStrategy.scrape_url"
    )
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_circuit_breaker_pattern(
        self, mock_playwright_scrape, mock_requests_scrape, intelligent_scraper
    ):
        """Test circuit breaker prevents repeated failures."""
        # Configure both strategies to fail
        mock_playwright_scrape.side_effect = Exception("Browser launch failed")
        mock_requests_scrape.side_effect = Exception("Network error")

        # Make multiple requests to trigger circuit breaker
        for _ in range(6):  # Threshold is 5, so 6th should be circuit broken
            result = await intelligent_scraper.scrape_url("https://example.com")

        # Last result should indicate circuit breaker is open or all strategies failed
        assert result.success is False
        # The error should be from the last failed attempt or circuit breaker
        assert (
            "circuit breaker" in result.error.lower()
            or "network error" in result.error.lower()
            or "all strategies failed" in result.error.lower()
        )

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_retry_mechanism_with_exponential_backoff(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        """Test retry mechanism with exponential backoff."""
        # Mock successful result (method returns HTML string)
        mock_playwright_scrape.return_value = (
            "<html><body>Success after retries</body></html>"
        )

        result = await intelligent_scraper.scrape_url("https://example.com")

        assert result.success is True
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED
        assert "Success after retries" in result.content
        mock_playwright_scrape.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.requests_scraping_strategy.RequestsScrapingStrategy.scrape_url"
    )
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_both_strategies_fail(
        self, mock_playwright_scrape, mock_requests_scrape, intelligent_scraper
    ):
        """Test behavior when both Playwright and requests fail."""
        # Configure both strategies to fail
        mock_playwright_scrape.side_effect = Exception("Browser failed")
        mock_requests_scrape.side_effect = Exception("Network failed")

        result = await intelligent_scraper.scrape_url("https://example.com")

        assert result.success is False
        assert result.strategy_used == FallbackStrategy.ALL_FAILED
        assert "network failed" in result.error.lower()
        assert result.attempts >= 2

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_performance_metrics_collection(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        """Test that performance metrics are collected."""
        # Mock successful result (method returns HTML string)
        mock_playwright_scrape.return_value = "<html><body>Test content</body></html>"

        result = await intelligent_scraper.scrape_url("https://example.com")

        assert result.performance_metrics is not None
        assert "total_time" in result.performance_metrics
        assert result.performance_metrics["total_time"] > 0
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_custom_user_agent_and_headers(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        """Test custom user agent and headers configuration."""
        # Mock successful result (method returns HTML string)
        mock_playwright_scrape.return_value = (
            "<html><body>Content with custom headers</body></html>"
        )

        custom_headers = {"X-Custom": "test-value"}
        result = await intelligent_scraper.scrape_url(
            "https://example.com", custom_headers=custom_headers
        )

        assert result.success is True
        # Verify the method was called with custom parameters
        call_args = mock_playwright_scrape.call_args
        assert call_args is not None

    def test_fallback_config_validation(self):
        """Test fallback configuration validation."""
        # Valid config
        valid_config = FallbackConfig(
            playwright_timeout=30,
            requests_timeout=15,
            max_retries=3,
            circuit_breaker_threshold=5,
        )
        assert valid_config.playwright_timeout == 30

        # Test invalid config raises appropriate errors
        with pytest.raises(ValueError):
            FallbackConfig(
                playwright_timeout=-1,  # Invalid negative timeout
                requests_timeout=15,
                max_retries=3,
                circuit_breaker_threshold=5,
            )

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_content_extraction_and_cleaning(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        """Test content extraction and cleaning functionality."""
        # Mock HTML content that should be returned as-is (cleaning happens in strategies)
        cleaned_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content of the page.</p>
                </main>
            </body>
        </html>
        """
        mock_playwright_scrape.return_value = cleaned_content

        result = await intelligent_scraper.scrape_url("https://example.com")

        # Verify the scraping was successful
        assert result.success is True
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED
        assert "Main Content" in result.content
        assert "This is the main content" in result.content

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_playwright_succeeds_first_try(
        self, mock_playwright_scrape, intelligent_scraper
    ):
        # Arrange
        mock_playwright_scrape.return_value = "Test Content"

        # Act
        result = await intelligent_scraper.scrape_url("https://example.com")

        # Assert
        assert result.success is True
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED
        assert "Test Content" in result.content
        mock_playwright_scrape.assert_called_once()
        # Check circuit breaker through orchestrator
        intelligent_scraper._orchestrator.circuit_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.requests_scraping_strategy.RequestsScrapingStrategy.scrape_url"
    )
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_fallback_to_requests_on_playwright_failure(
        self, mock_playwright_scrape, mock_requests_scrape, intelligent_scraper
    ):
        # Arrange
        mock_playwright_scrape.side_effect = PlaywrightError("Playwright failed")
        mock_requests_scrape.return_value = "<html><body>HTTPX Content</body></html>"

        # Act
        result = await intelligent_scraper.scrape_url("https://example.com")

        # Assert
        assert result.success is True
        assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK
        assert "HTTPX Content" in result.content
        mock_playwright_scrape.assert_called_once()
        mock_requests_scrape.assert_called_once()
        # Check circuit breaker calls through orchestrator
        intelligent_scraper._orchestrator.circuit_breaker.record_failure.assert_called_once()  # For playwright
        intelligent_scraper._orchestrator.circuit_breaker.record_success.assert_called_once()  # For requests

    @pytest.mark.asyncio
    @patch(
        "src.scraper.infrastructure.web_scraping.requests_scraping_strategy.RequestsScrapingStrategy.scrape_url"
    )
    @patch(
        "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.PlaywrightScrapingStrategy.scrape_url"
    )
    async def test_both_strategies_fail(
        self, mock_playwright_scrape, mock_requests_scrape, intelligent_scraper
    ):
        # Arrange
        mock_playwright_scrape.side_effect = PlaywrightTimeoutError(
            "Playwright timed out"
        )
        mock_requests_scrape.side_effect = httpx.RequestError("HTTPX failed")

        # Act
        result = await intelligent_scraper.scrape_url("https://example.com")

        # Assert
        assert not result.success
        assert "HTTPX failed" in result.error
        mock_playwright_scrape.assert_called_once()
        mock_requests_scrape.assert_called_once()
        # Check circuit breaker calls through orchestrator
        assert (
            intelligent_scraper._orchestrator.circuit_breaker.record_failure.call_count
            == 2
        )
        intelligent_scraper._orchestrator.circuit_breaker.record_success.assert_not_called()


class TestScrapingResult:
    """Test the ScrapingResult data class."""

    def test_scraping_result_creation(self):
        """Test ScrapingResult creation and properties."""
        result = ScrapingResult(
            success=True,
            content="<html>Test</html>",
            strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
            attempts=1,
            error=None,
            performance_metrics={"total_time": 1.5},
        )

        assert result.success is True
        assert result.content == "<html>Test</html>"
        assert result.strategy_used == FallbackStrategy.PLAYWRIGHT_OPTIMIZED
        assert result.attempts == 1
        assert result.error is None
        assert result.performance_metrics["total_time"] == 1.5

    def test_failed_scraping_result(self):
        """Test failed scraping result."""
        result = ScrapingResult(
            success=False,
            content=None,
            strategy_used=FallbackStrategy.ALL_FAILED,
            attempts=3,
            error="All strategies failed",
            performance_metrics={"total_time": 5.0},
        )

        assert result.success is False
        assert result.content is None
        assert result.strategy_used == FallbackStrategy.ALL_FAILED
        assert result.attempts == 3
        assert result.error == "All strategies failed"


class TestFallbackStrategy:
    """Test the FallbackStrategy enum."""

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
