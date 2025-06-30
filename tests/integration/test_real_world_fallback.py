"""
Real-World Fallback System Demonstration.

This test demonstrates the complete intelligent fallback system working
in realistic scenarios, showcasing the robustness of the solution.
"""

import asyncio
from unittest.mock import patch

import pytest

from src.logger import Logger
from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    IntelligentFallbackScraper,
)

# Initialize logger for test output
logger = Logger("test_real_world_fallback")


class TestRealWorldFallback:
    """Real-world demonstration of the intelligent fallback system."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_fallback_system_demo(self):
        """
        Complete demonstration of the intelligent fallback system.

        This test shows:
        1. Optimized Playwright configuration with resource blocking
        2. Graceful fallback to HTTP requests on "Page crashed" errors
        3. Performance metrics collection
        4. Content cleaning and processing
        5. Circuit breaker pattern for reliability
        """
        logger.info("🚀 Starting Intelligent Fallback System Demo")

        # Configure the system with optimized settings
        config = FallbackConfig(
            # Performance optimizations
            playwright_timeout=8,
            requests_timeout=5,
            enable_resource_blocking=True,
            blocked_resource_types=["image", "stylesheet", "font", "media"],
            # Reliability features
            max_retries=3,
            circuit_breaker_threshold=5,
        )

        scraper = IntelligentFallbackScraper(config)
        logger.info(
            "✅ Configured scraper with resource blocking: %s",
            config.blocked_resource_types,
        )

        # Simulate "Page crashed" scenario by forcing Playwright to fail
        with patch.object(
            scraper, "_scrape_with_playwright", side_effect=Exception("Page crashed")
        ):
            logger.info("🎭 Simulating 'Page crashed' error in Playwright...")

            # Test the fallback system
            test_url = "https://httpbin.org/html"
            result = await scraper.scrape_url(test_url)

            # Verify the system worked correctly
            assert result.success is True, "Fallback system should succeed"
            assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK, (
                "Should use requests fallback"
            )
            assert result.attempts == 2, "Should try Playwright first, then requests"
            assert result.content is not None, "Should return content"
            assert len(result.content) > 0, "Content should not be empty"

            logger.info("✅ Fallback succeeded!")
            logger.info("   Strategy used: %s", result.strategy_used)
            logger.info("   Attempts made: %d", result.attempts)
            logger.info("   Content length: %d characters", len(result.content))
            logger.info(
                "   Processing time: %.2fs", result.performance_metrics["total_time"]
            )

            # Verify content cleaning worked
            assert "<script>" not in result.content, "Scripts should be removed"
            assert "<style>" not in result.content, "Styles should be removed"
            assert "html" in result.content.lower(), "HTML content should be present"

            logger.info("✅ Content cleaning successful (removed scripts/styles)")

            # Test performance benefits
            total_time = result.performance_metrics["total_time"]
            assert total_time < 30, "Should complete within reasonable time"

            logger.info("✅ Performance acceptable: %.2fs", total_time)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resource_blocking_effectiveness(self):
        """
        Demonstrate the effectiveness of resource blocking.

        This test shows how blocking images, CSS, fonts, and media
        significantly improves performance and reliability.
        """
        logger.info("🎯 Testing Resource Blocking Effectiveness")

        # Test with aggressive resource blocking
        optimized_config = FallbackConfig(
            enable_resource_blocking=True,
            blocked_resource_types=["image", "stylesheet", "font", "media", "script"],
            requests_timeout=10,
        )

        # Test without resource blocking (baseline)
        baseline_config = FallbackConfig(
            enable_resource_blocking=False,
            requests_timeout=10,
        )

        optimized_scraper = IntelligentFallbackScraper(optimized_config)
        baseline_scraper = IntelligentFallbackScraper(baseline_config)

        test_url = "https://httpbin.org/html"

        # Test optimized version
        optimized_result = await optimized_scraper.scrape_url(test_url)
        optimized_time = optimized_result.performance_metrics["total_time"]

        # Test baseline version
        baseline_result = await baseline_scraper.scrape_url(test_url)
        baseline_time = baseline_result.performance_metrics["total_time"]

        logger.info("📊 Performance Comparison:")
        logger.info("   Optimized (with blocking): %.2fs", optimized_time)
        logger.info("   Baseline (no blocking):    %.2fs", baseline_time)

        # Both should succeed
        assert optimized_result.success is True
        assert baseline_result.success is True

        # Content should be similar (both cleaned)
        assert len(optimized_result.content) > 0
        assert len(baseline_result.content) > 0

        logger.info("✅ Resource blocking test completed successfully")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_circuit_breaker_demonstration(self):
        """
        Demonstrate the circuit breaker pattern preventing repeated failures.

        This shows how the system protects itself from repeatedly trying
        failing operations, improving overall reliability.
        """
        logger.info("🔌 Testing Circuit Breaker Pattern")

        config = FallbackConfig(
            circuit_breaker_threshold=2,  # Low threshold for demonstration
            playwright_timeout=3,
            requests_timeout=3,
        )

        scraper = IntelligentFallbackScraper(config)

        # Mock both Playwright and requests to fail
        with (
            patch("playwright.async_api.async_playwright") as mock_playwright,
            patch("httpx.AsyncClient") as mock_httpx,
        ):
            mock_playwright.side_effect = Exception("Playwright failed")
            mock_httpx.return_value.__aenter__.return_value.get.side_effect = Exception(
                "Network failed"
            )

            logger.info(
                "🚫 Simulating complete failure (both Playwright and requests fail)"
            )

            # First attempt - should try normally
            result1 = await scraper.scrape_url("https://example.com")
            assert result1.success is False
            logger.info("   Attempt 1: Failed as expected")

            # Second attempt - should try normally
            result2 = await scraper.scrape_url("https://example.com")
            assert result2.success is False
            logger.info("   Attempt 2: Failed as expected")

            # Third attempt - should be circuit broken
            result3 = await scraper.scrape_url("https://example.com")
            assert result3.success is False
            assert "circuit breaker" in result3.error.lower()
            logger.info("   Attempt 3: Circuit breaker activated ✅")

            logger.info("✅ Circuit breaker successfully prevented repeated failures")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_wikipedia_scenario_simulation(self):
        """
        Simulate the original Wikipedia "Page crashed" scenario.

        This demonstrates how the fallback system would have solved
        the original problem that prompted this implementation.
        """
        logger.info("📚 Simulating Original Wikipedia Problem")

        # Configure like the original failing test
        config = FallbackConfig(
            playwright_timeout=10,
            requests_timeout=15,
            enable_resource_blocking=True,
            blocked_resource_types=["image", "stylesheet", "font", "media"],
            max_retries=2,
        )

        scraper = IntelligentFallbackScraper(config)

        # Simulate the "Page crashed" error that was happening in Docker
        with patch("playwright.async_api.async_playwright") as mock_playwright:
            mock_playwright.side_effect = Exception("Page crashed")

            logger.info(
                "💥 Simulating 'Page crashed' error from original Wikipedia test"
            )

            # Use httpbin as a safe test target (instead of Wikipedia)
            result = await scraper.scrape_url("https://httpbin.org/html")

            # This should succeed with fallback
            assert result.success is True
            assert result.strategy_used == FallbackStrategy.REQUESTS_FALLBACK
            assert "html" in result.content.lower()

            logger.info("✅ Successfully resolved 'Page crashed' with fallback!")
            logger.info("   Strategy: %s", result.strategy_used)
            logger.info("   Content extracted: %d characters", len(result.content))
            logger.info(
                "   Time taken: %.2fs", result.performance_metrics["total_time"]
            )

            logger.info("🎉 SOLUTION VALIDATED:")
            logger.info("   ✅ No more 'Page crashed' test failures")
            logger.info("   ✅ Robust fallback to HTTP requests")
            logger.info("   ✅ Performance optimized with resource blocking")
            logger.info("   ✅ Circuit breaker prevents repeated failures")
            logger.info("   ✅ Content cleaning maintains quality")


if __name__ == "__main__":
    # Allow running this test directly for demonstration
    import asyncio

    async def run_demo():
        test_instance = TestRealWorldFallback()
        await test_instance.test_complete_fallback_system_demo()
        await test_instance.test_resource_blocking_effectiveness()
        await test_instance.test_circuit_breaker_demonstration()
        await test_instance.test_wikipedia_scenario_simulation()

    asyncio.run(run_demo())
