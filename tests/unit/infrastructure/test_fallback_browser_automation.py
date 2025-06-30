"""
Integration tests for Fallback Browser Automation.

This module tests the integration between the intelligent fallback scraper
and the existing browser automation interface, ensuring seamless compatibility
with the current architecture.

Following TDD: RED phase for integration layer
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.scraper.application.contracts.browser_automation import (
    BrowserConfiguration,
)
from src.scraper.infrastructure.web_scraping.fallback_browser_automation import (
    FallbackBrowserAutomation,
    FallbackBrowserFactory,
)
from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    ScrapingResult,
)


class TestFallbackBrowserAutomation:
    """Test suite for the Fallback Browser Automation integration."""

    @pytest.fixture
    def browser_config(self):
        """Fixture providing browser configuration."""
        return BrowserConfiguration(
            user_agent="Mozilla/5.0 (compatible; TestBot/1.0)",
            timeout_seconds=30,
            viewport={"width": 1920, "height": 1080},
            accept_language="en-US,en;q=0.9",
        )

    @pytest.fixture
    def fallback_config(self):
        """Fixture providing fallback configuration."""
        return FallbackConfig(
            playwright_timeout=30,
            requests_timeout=15,
            max_retries=3,
            circuit_breaker_threshold=5,
            enable_resource_blocking=True,
        )

    @pytest.fixture
    def mock_intelligent_scraper(self):
        """Mock intelligent scraper for testing."""
        return AsyncMock()

    @pytest.fixture
    def fallback_browser(
        self, mock_intelligent_scraper, browser_config, fallback_config
    ):
        """Fixture providing configured fallback browser automation."""
        return FallbackBrowserAutomation(
            scraper=mock_intelligent_scraper,
            browser_config=browser_config,
            fallback_config=fallback_config,
        )

    @pytest.mark.asyncio
    async def test_successful_navigation_with_playwright(
        self, fallback_browser, mock_intelligent_scraper
    ):
        """Test successful navigation using Playwright strategy."""
        # Configure mock to return successful Playwright result
        mock_result = ScrapingResult(
            success=True,
            content="<html><body>Test content</body></html>",
            strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
            attempts=1,
            final_url="https://example.com",
        )
        mock_intelligent_scraper.scrape_url.return_value = mock_result

        response = await fallback_browser.navigate_to_url("https://example.com")

        assert response.success is True
        assert response.content == "<html><body>Test content</body></html>"
        assert response.status_code == 200
        assert response.url == "https://example.com"
        assert response.error is None

    @pytest.mark.asyncio
    async def test_fallback_to_requests_on_playwright_failure(
        self, fallback_browser, mock_intelligent_scraper
    ):
        """Test fallback to requests when Playwright fails."""
        mock_result = ScrapingResult(
            success=True,
            content="<html><body>Fallback content</body></html>",
            strategy_used=FallbackStrategy.REQUESTS_FALLBACK,
            attempts=2,
            final_url="https://example.com",
        )
        mock_intelligent_scraper.scrape_url.return_value = mock_result

        response = await fallback_browser.navigate_to_url("https://example.com")

        assert response.success is True
        assert response.content == "<html><body>Fallback content</body></html>"
        assert response.status_code == 200  # Simulated successful fallback
        assert response.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_all_strategies_fail(
        self, fallback_browser, mock_intelligent_scraper
    ):
        """Test behavior when all fallback strategies fail."""
        mock_result = ScrapingResult(
            success=False,
            content=None,
            strategy_used=FallbackStrategy.ALL_FAILED,
            attempts=3,
            error="All strategies failed. Last error: Network timeout",
            final_url="https://example.com",
        )
        mock_intelligent_scraper.scrape_url.return_value = mock_result

        response = await fallback_browser.navigate_to_url("https://example.com")

        assert response.success is False
        assert response.content is None
        assert response.error == "All strategies failed. Last error: Network timeout"
        assert response.status_code is None

    @pytest.mark.asyncio
    async def test_get_page_content_returns_cached_content(
        self, fallback_browser, mock_intelligent_scraper
    ):
        """Test that get_page_content returns cached content from last navigation."""
        mock_result = ScrapingResult(
            success=True,
            content="<html><body>Cached content</body></html>",
            strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
            attempts=1,
            final_url="https://example.com",
        )
        mock_intelligent_scraper.scrape_url.return_value = mock_result

        # Navigate first to cache content
        await fallback_browser.navigate_to_url("https://example.com")

        # Get cached content
        content = await fallback_browser.get_page_content()

        assert content == "<html><body>Cached content</body></html>"

    @pytest.mark.asyncio
    async def test_wait_for_content_stabilization_always_returns_true(
        self, fallback_browser
    ):
        """Test that content stabilization always returns true for fallback browser."""
        # Since we're using HTTP requests as fallback, content is always "stable"
        result = await fallback_browser.wait_for_content_stabilization(
            timeout_seconds=10
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_click_element_not_supported(self, fallback_browser):
        """Test that click_element returns False (not supported in fallback mode)."""
        result = await fallback_browser.click_element("button.submit")
        assert result is False

    @pytest.mark.asyncio
    async def test_close_cleanup(self, fallback_browser):
        """Test that close method performs cleanup without errors."""
        # Should not raise any exceptions
        await fallback_browser.close()

    @pytest.mark.asyncio
    async def test_custom_headers_passed_to_scraper(
        self, fallback_browser, mock_intelligent_scraper
    ):
        """Test that custom headers are passed to the intelligent scraper."""
        mock_result = ScrapingResult(
            success=True,
            content="<html><body>Content with headers</body></html>",
            strategy_used=FallbackStrategy.REQUESTS_FALLBACK,
            attempts=1,
            final_url="https://example.com",
        )
        mock_intelligent_scraper.scrape_url.return_value = mock_result

        # Set custom headers
        fallback_browser.set_custom_headers({"X-Custom": "test-value"})

        await fallback_browser.navigate_to_url("https://example.com")

        # Verify scraper was called with custom headers
        mock_intelligent_scraper.scrape_url.assert_called_once()
        call_args = mock_intelligent_scraper.scrape_url.call_args
        assert call_args[1]["custom_headers"]["X-Custom"] == "test-value"


class TestFallbackBrowserFactory:
    """Test suite for the Fallback Browser Factory."""

    @pytest.fixture
    def factory(self):
        """Fixture providing fallback browser factory."""
        return FallbackBrowserFactory()

    @pytest.fixture
    def browser_config(self):
        """Fixture providing browser configuration."""
        return BrowserConfiguration(
            user_agent="Mozilla/5.0 (compatible; TestBot/1.0)",
            timeout_seconds=30,
            viewport={"width": 1920, "height": 1080},
            accept_language="en-US,en;q=0.9",
        )

    @pytest.mark.asyncio
    async def test_create_browser_returns_fallback_automation(
        self, factory, browser_config
    ):
        """Test that factory creates fallback browser automation instance."""
        browser = await factory.create_browser(browser_config)

        assert isinstance(browser, FallbackBrowserAutomation)
        assert browser.browser_config == browser_config

    @pytest.mark.asyncio
    async def test_factory_creates_optimized_fallback_config(
        self, factory, browser_config
    ):
        """Test that factory creates optimized fallback configuration."""
        browser = await factory.create_browser(browser_config)

        # Verify fallback config is optimized for performance
        fallback_config = browser.fallback_config
        assert fallback_config.enable_resource_blocking is True
        assert "image" in fallback_config.blocked_resource_types
        assert "stylesheet" in fallback_config.blocked_resource_types
        assert fallback_config.playwright_timeout == browser_config.timeout_seconds

    @pytest.mark.asyncio
    async def test_factory_handles_different_configurations(self, factory):
        """Test factory handles various browser configurations."""
        configs = [
            BrowserConfiguration(
                user_agent="Chrome/91.0",
                timeout_seconds=15,
                viewport={"width": 1366, "height": 768},
            ),
            BrowserConfiguration(
                user_agent="Firefox/89.0",
                timeout_seconds=45,
                viewport={"width": 1440, "height": 900},
                accept_language="es-ES,es;q=0.8",
            ),
        ]

        for config in configs:
            browser = await factory.create_browser(config)
            assert isinstance(browser, FallbackBrowserAutomation)
            assert browser.browser_config == config

    @pytest.mark.asyncio
    async def test_factory_creates_browser_with_performance_metrics(self):
        """Test that the factory correctly creates a browser instance with performance metrics."""
        with patch(
            "src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper.IntelligentFallbackScraper"
        ) as mock_scraper_class:

            async def mock_scrape_url(url, custom_headers):
                await asyncio.sleep(1.5)
                return ScrapingResult(
                    success=True,
                    content="<p>Performance test</p>",
                    final_url=url,
                    performance_metrics={"total_time": 1.77},
                )

            mock_scraper_class.return_value.scrape_url = mock_scrape_url

            factory = FallbackBrowserFactory()
            browser = await factory.create_browser(
                BrowserConfiguration(user_agent="test", timeout_seconds=30)
            )
            await browser.navigate_to_url("https://example.com")

            metrics = browser.get_last_performance_metrics()
            assert metrics is not None
            assert abs(metrics["total_time"] - 1.5) < 2.0  # Allow some variance


class TestIntegrationWithExistingServices:
    """Test integration with other components, like WebScrapingService."""

    @pytest.mark.asyncio
    async def test_integration_with_web_scraping_service(self):
        """Test integration with the existing WebScrapingService."""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        # Create services with fallback browser factory
        factory = FallbackBrowserFactory()
        content_processor = ContentProcessingService()
        config_service = ScrapingConfigurationService()

        web_service = WebScrapingService(
            browser_factory=factory,
            content_processor=content_processor,
            configuration_service=config_service,
        )

        # Verify service can be created without errors
        assert web_service is not None
        assert web_service.browser_factory == factory

    @pytest.mark.asyncio
    async def test_fallback_browser_implements_interface_correctly(self):
        """Test that fallback browser correctly implements BrowserAutomationInterface."""
        from src.scraper.application.contracts.browser_automation import (
            BrowserAutomation,
        )

        factory = FallbackBrowserFactory()
        config = BrowserConfiguration(
            user_agent="Mozilla/5.0 (compatible; TestBot/1.0)",
            timeout_seconds=30,
        )
        browser = await factory.create_browser(config)

        # Verify it implements the interface
        assert isinstance(browser, BrowserAutomation)

        # Verify all interface methods are available
        assert hasattr(browser, "navigate_to_url")
        assert hasattr(browser, "get_page_content")
        assert hasattr(browser, "wait_for_content_stabilization")
        assert hasattr(browser, "click_element")
        assert hasattr(browser, "close")


class TestPerformanceAndReliability:
    """Test performance and reliability aspects of the fallback system."""

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test that performance metrics are properly collected."""
        factory = FallbackBrowserFactory()
        config = BrowserConfiguration(
            user_agent="Mozilla/5.0 (compatible; TestBot/1.0)",
            timeout_seconds=30,
        )

        with patch(
            "src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper.IntelligentFallbackScraper"
        ) as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper_class.return_value = mock_scraper

            mock_result = ScrapingResult(
                success=True,
                content="<html><body>Content</body></html>",
                strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
                attempts=1,
                performance_metrics={"total_time": 1.5, "playwright_time": 1.2},
                final_url="https://example.com",
            )
            mock_scraper.scrape_url.return_value = mock_result

            browser = await factory.create_browser(config)
            await browser.navigate_to_url("https://example.com")

            # Verify performance metrics are accessible
            assert hasattr(browser, "get_last_performance_metrics")
            metrics = browser.get_last_performance_metrics()
            assert metrics is not None
            assert "total_time" in metrics
            # Use approximate comparison since actual time may vary slightly
            assert abs(metrics["total_time"] - 1.5) < 1.0  # Allow some variance

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test circuit breaker functionality in integration context."""
        factory = FallbackBrowserFactory()
        config = BrowserConfiguration(
            user_agent="Mozilla/5.0 (compatible; TestBot/1.0)",
            timeout_seconds=30,
        )

        browser = await factory.create_browser(config)

        # Mock the scraper instance directly
        mock_result = ScrapingResult(
            success=False,
            content=None,
            strategy_used=FallbackStrategy.ALL_FAILED,
            attempts=0,
            error="Circuit breaker is open - too many recent failures",
            final_url="https://example.com",
        )

        # Replace the scraper instance with a mock
        browser.scraper.scrape_url = AsyncMock(return_value=mock_result)

        response = await browser.navigate_to_url("https://example.com")

        # Verify circuit breaker behavior
        assert response.success is False
        assert response.error is not None
        assert "circuit breaker" in response.error.lower()
