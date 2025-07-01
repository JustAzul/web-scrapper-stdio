"""
Tests for problem fixes identified in codebase analysis.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.scraper.application.services.fallback_orchestrator import FallbackOrchestrator
from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
)


class TestProblemFixes:
    """Test class for verifying problem fixes."""

    @pytest.fixture
    def fallback_orchestrator(self):
        """Create FallbackOrchestrator instance for testing."""
        config = FallbackConfig()
        return FallbackOrchestrator(config=config)

    @pytest.mark.asyncio
    async def test_specific_playwright_exception_handling(self, fallback_orchestrator):
        """Test that specific Playwright exceptions are handled properly."""
        # Mock the strategies
        fallback_orchestrator.playwright_strategy = AsyncMock()
        fallback_orchestrator.requests_strategy = AsyncMock()

        # Mock Playwright strategy to raise PlaywrightTimeoutError
        fallback_orchestrator.playwright_strategy.scrape_url.side_effect = (
            PlaywrightTimeoutError("Navigation timeout")
        )

        # Mock requests strategy to succeed
        fallback_orchestrator.requests_strategy.scrape_url.return_value = (
            "<html><body>Fallback content</body></html>"
        )

        # Mock circuit breaker and metrics
        fallback_orchestrator.circuit_breaker = MagicMock()
        fallback_orchestrator.circuit_breaker.is_open = (
            False  # Circuit breaker is closed
        )
        fallback_orchestrator.metrics_collector = MagicMock()
        fallback_orchestrator.metrics_collector.start_operation.return_value = 123456789

        result = await fallback_orchestrator.scrape_url("https://example.com")

        # Verify fallback worked
        assert result.success is True
        assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK
        assert "Fallback content" in result.content
        assert result.attempts == 2  # Playwright failed, requests succeeded

        # Verify circuit breaker was called for failure and success
        assert fallback_orchestrator.circuit_breaker.record_failure.call_count == 1
        assert fallback_orchestrator.circuit_breaker.record_success.call_count == 1

    @pytest.mark.asyncio
    async def test_import_error_handling(self, fallback_orchestrator):
        """Test that ImportError is handled specifically."""
        # Mock the strategies
        fallback_orchestrator.playwright_strategy = AsyncMock()
        fallback_orchestrator.requests_strategy = AsyncMock()

        # Mock Playwright strategy to raise ImportError
        fallback_orchestrator.playwright_strategy.scrape_url.side_effect = ImportError(
            "Playwright not installed"
        )

        # Mock requests strategy to succeed
        fallback_orchestrator.requests_strategy.scrape_url.return_value = (
            "<html><body>Fallback content</body></html>"
        )

        # Mock circuit breaker and metrics
        fallback_orchestrator.circuit_breaker = MagicMock()
        fallback_orchestrator.circuit_breaker.is_open = (
            False  # Circuit breaker is closed
        )
        fallback_orchestrator.metrics_collector = MagicMock()
        fallback_orchestrator.metrics_collector.start_operation.return_value = 123456789

        result = await fallback_orchestrator.scrape_url("https://example.com")

        # Verify fallback worked
        assert result.success is True
        assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK

        # Verify circuit breaker recorded the failure
        assert fallback_orchestrator.circuit_breaker.record_failure.call_count == 1

    @pytest.mark.asyncio
    async def test_unexpected_exception_still_logged(self, fallback_orchestrator):
        """Test that unexpected exceptions are still caught and logged."""
        # Mock the strategies
        fallback_orchestrator.playwright_strategy = AsyncMock()
        fallback_orchestrator.requests_strategy = AsyncMock()

        # Mock Playwright strategy to raise unexpected exception
        fallback_orchestrator.playwright_strategy.scrape_url.side_effect = ValueError(
            "Unexpected error"
        )

        # Mock requests strategy to succeed
        fallback_orchestrator.requests_strategy.scrape_url.return_value = (
            "<html><body>Fallback content</body></html>"
        )

        # Mock circuit breaker and metrics
        fallback_orchestrator.circuit_breaker = MagicMock()
        fallback_orchestrator.circuit_breaker.is_open = (
            False  # Circuit breaker is closed
        )
        fallback_orchestrator.metrics_collector = MagicMock()
        fallback_orchestrator.metrics_collector.start_operation.return_value = 123456789

        with patch(
            "src.scraper.application.services.fallback_orchestrator.logger"
        ) as mock_logger:
            result = await fallback_orchestrator.scrape_url("https://example.com")

            # Verify fallback worked
            assert result.success is True
            assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK

            # Verify unexpected error was logged
            mock_logger.error.assert_called_once()
            assert "Unexpected error in Playwright strategy" in str(
                mock_logger.error.call_args
            )
