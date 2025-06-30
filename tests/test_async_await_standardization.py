"""
TDD Tests for T013 - Async/Await Standardization
Tests for standardizing asynchronous patterns throughout the codebase
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestRetryStrategyPatternAsyncStandardization:
    """TDD Tests for making RetryStrategyPattern fully async"""

    def test_retry_strategy_execute_sync_should_be_deprecated(self):
        """Test that execute_sync method should be deprecated in favor of async version"""
        # This test will fail initially (RED phase)
        from src.scraper.infrastructure.standardized_retry_strategy import (
            StandardizedRetryStrategy,
        )

        retry_strategy = StandardizedRetryStrategy(max_retries=3)

        # The new standardized version should not have execute_sync method
        assert not hasattr(retry_strategy, "execute_sync")

        # Should only have async execute method
        assert hasattr(retry_strategy, "execute")
        assert asyncio.iscoroutinefunction(retry_strategy.execute)

    @pytest.mark.asyncio
    async def test_standardized_retry_strategy_async_execution(self):
        """Test that standardized retry strategy works with async functions"""
        from src.scraper.infrastructure.standardized_retry_strategy import (
            StandardizedRetryStrategy,
        )

        retry_strategy = StandardizedRetryStrategy(max_retries=2, initial_delay=0.01)

        # Mock async function that fails once then succeeds
        call_count = 0

        async def mock_async_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First attempt fails")
            return "success"

        result = await retry_strategy.execute(mock_async_func)

        assert result == "success"
        assert call_count == 2  # Failed once, succeeded on second attempt

    @pytest.mark.asyncio
    async def test_standardized_retry_strategy_sync_function_adapter(self):
        """Test that standardized retry strategy can adapt sync functions to async"""
        from src.scraper.infrastructure.standardized_retry_strategy import (
            StandardizedRetryStrategy,
        )

        retry_strategy = StandardizedRetryStrategy(max_retries=2, initial_delay=0.01)

        # Mock sync function
        call_count = 0

        def mock_sync_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First attempt fails")
            return "sync_success"

        # Should be able to execute sync function via async adapter
        result = await retry_strategy.execute_sync_as_async(mock_sync_func)

        assert result == "sync_success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_standardized_retry_uses_async_sleep(self):
        """Test that standardized retry uses asyncio.sleep instead of time.sleep"""
        from src.scraper.infrastructure.standardized_retry_strategy import (
            StandardizedRetryStrategy,
        )

        retry_strategy = StandardizedRetryStrategy(max_retries=1, initial_delay=0.01)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_async_sleep:
            with patch("time.sleep") as mock_time_sleep:

                async def failing_func():
                    raise ValueError("Always fails")

                with pytest.raises(ValueError):
                    await retry_strategy.execute(failing_func)

                # Should use asyncio.sleep, not time.sleep
                mock_async_sleep.assert_called_once()
                mock_time_sleep.assert_not_called()


class TestAsyncHTTPOperations:
    """TDD Tests for ensuring all HTTP operations are async"""

    @pytest.mark.asyncio
    async def test_rate_limiting_is_fully_async(self):
        """Test that rate limiting operations are fully asynchronous"""
        from src.scraper.infrastructure.external.async_rate_limiting import (
            AsyncRateLimiter,
        )

        rate_limiter = AsyncRateLimiter()

        # Should be async method
        assert asyncio.iscoroutinefunction(rate_limiter.apply_rate_limiting)

        # Should work with async context
        start_time = asyncio.get_event_loop().time()
        await rate_limiter.apply_rate_limiting("https://example.com")
        await rate_limiter.apply_rate_limiting(
            "https://example.com"
        )  # Should be rate limited
        end_time = asyncio.get_event_loop().time()

        # Second call should have been delayed
        assert end_time - start_time >= 0.5  # Minimum delay

    @pytest.mark.asyncio
    async def test_domain_extraction_async_compatible(self):
        """Test that domain extraction is async-compatible"""
        from src.scraper.infrastructure.external.async_rate_limiting import (
            AsyncRateLimiter,
        )

        rate_limiter = AsyncRateLimiter()

        # Should handle URL parsing asynchronously
        domain = await rate_limiter.get_domain_from_url_async(
            "https://example.com/path"
        )
        assert domain == "example.com"

        # Should handle invalid URLs gracefully
        domain = await rate_limiter.get_domain_from_url_async("invalid-url")
        assert domain is None


class TestAsyncErrorHandling:
    """TDD Tests for async error handling patterns"""

    @pytest.mark.asyncio
    async def test_cloudflare_detection_async(self):
        """Test that Cloudflare detection works in async context"""
        from src.scraper.infrastructure.external.async_errors import AsyncErrorHandler

        error_handler = AsyncErrorHandler()

        # Should be async method
        assert asyncio.iscoroutinefunction(
            error_handler.detect_cloudflare_challenge_async
        )

        cloudflare_html = "<html><body>Checking your browser...</body></html>"
        is_cloudflare = await error_handler.detect_cloudflare_challenge_async(
            cloudflare_html
        )
        assert is_cloudflare is True

        normal_html = "<html><body>Normal content</body></html>"
        is_cloudflare = await error_handler.detect_cloudflare_challenge_async(
            normal_html
        )
        assert is_cloudflare is False

    @pytest.mark.asyncio
    async def test_async_navigation_error_handling(self):
        """Test async navigation with proper error handling"""
        from src.scraper.infrastructure.external.async_errors import AsyncErrorHandler

        error_handler = AsyncErrorHandler()

        # Mock page object
        mock_page = AsyncMock()
        mock_page.goto.side_effect = Exception("Navigation failed")

        with pytest.raises(Exception):
            await error_handler.navigate_and_handle_errors_async(
                mock_page, "https://example.com", 30
            )

        # Should have attempted navigation
        mock_page.goto.assert_called_once()


class TestAsyncContentProcessing:
    """TDD Tests for async content processing patterns"""

    @pytest.mark.asyncio
    async def test_html_processing_async_pipeline(self):
        """Test that HTML processing can work in async pipeline"""
        from src.scraper.infrastructure.external.async_html_utils import (
            AsyncHTMLProcessor,
        )

        processor = AsyncHTMLProcessor()

        html_content = "<html><body><nav>Nav</nav><main>Content</main></body></html>"
        elements_to_remove = ["nav"]

        # Should process HTML asynchronously
        result = await processor.extract_and_clean_html_async(
            html_content, elements_to_remove
        )

        soup, target_element = result
        assert soup is not None
        assert target_element is not None
        assert "Nav" not in str(target_element)
        assert "Content" in str(target_element)

    @pytest.mark.asyncio
    async def test_async_content_extraction_pipeline(self):
        """Test async content extraction with proper pipeline"""
        from src.scraper.infrastructure.external.async_html_utils import (
            AsyncHTMLProcessor,
        )

        processor = AsyncHTMLProcessor()

        html_content = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>"

        # Should extract markdown and text asynchronously
        result = await processor.extract_markdown_and_text_async(html_content)

        # Result should be a string containing the text
        assert isinstance(result, (str, tuple))
        if isinstance(result, tuple):
            text_content = result[1]  # Get text part of tuple
        else:
            text_content = result
        assert "Title" in text_content
        assert "Paragraph" in text_content


class TestAsyncFileOperations:
    """TDD Tests for async file operations if any"""

    @pytest.mark.asyncio
    async def test_async_config_loading(self):
        """Test that configuration loading can be async if needed"""
        from src.async_config import AsyncConfigLoader

        config_loader = AsyncConfigLoader()

        # Should load configuration asynchronously
        config = await config_loader.load_config_async()

        assert config is not None
        assert hasattr(config, "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS")

    @pytest.mark.asyncio
    async def test_async_settings_reload(self):
        """Test that settings can be reloaded asynchronously"""
        from src.async_settings import AsyncSettings

        settings = AsyncSettings()

        # Should reload settings asynchronously
        await settings.reload_settings_async()

        # Should have loaded settings
        assert settings.is_loaded()


class TestAsyncConsistencyValidation:
    """TDD Tests for validating async consistency across the codebase"""

    def test_all_io_methods_are_async(self):
        """Test that all I/O methods in the codebase are async"""
        from src.scraper.infrastructure.external.async_validator import (
            AsyncConsistencyValidator,
        )

        validator = AsyncConsistencyValidator()

        # Should validate that all I/O methods are async
        violations = validator.find_sync_io_violations()

        # Should have no violations after standardization
        assert len(violations) == 0, f"Found sync I/O violations: {violations}"

    def test_no_mixed_async_sync_patterns(self):
        """Test that there are no mixed async/sync patterns"""
        from src.scraper.infrastructure.external.async_validator import (
            AsyncConsistencyValidator,
        )

        validator = AsyncConsistencyValidator()

        # Should find no mixed patterns
        mixed_patterns = validator.find_mixed_async_sync_patterns()

        assert len(mixed_patterns) == 0, f"Found mixed patterns: {mixed_patterns}"

    @pytest.mark.asyncio
    async def test_async_context_managers_work(self):
        """Test that async context managers work properly"""
        from src.scraper.infrastructure.external.async_context import (
            AsyncResourceManager,
        )

        async with AsyncResourceManager() as manager:
            # Should be able to use manager in async context
            assert manager.is_active()

            # Should be able to perform async operations
            result = await manager.perform_async_operation()
            assert result is not None

    @pytest.mark.asyncio
    async def test_backward_compatibility_maintained(self):
        """Test that async standardization maintains backward compatibility"""
        # Original functions should still work
        from src.scraper.infrastructure.web_scraping.rate_limiting import (
            apply_rate_limiting,
        )

        # Should still be async
        assert asyncio.iscoroutinefunction(apply_rate_limiting)

        # Should still work
        await apply_rate_limiting("https://example.com")


class TestAsyncPerformance:
    """TDD Tests for async performance patterns"""

    @pytest.mark.asyncio
    async def test_concurrent_operations_support(self):
        """Test that async operations support concurrency"""
        from src.scraper.infrastructure.external.async_rate_limiting import (
            AsyncRateLimiter,
        )

        rate_limiter = AsyncRateLimiter()

        # Should be able to handle concurrent operations
        tasks = [
            rate_limiter.apply_rate_limiting(f"https://example{i}.com")
            for i in range(3)
        ]

        # Should complete all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should not have exceptions
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_async_timeout_handling(self):
        """Test proper async timeout handling"""
        from src.scraper.infrastructure.external.async_timeouts import (
            AsyncTimeoutHandler,
        )

        timeout_handler = AsyncTimeoutHandler()

        async def slow_operation():
            await asyncio.sleep(1.0)
            return "completed"

        # Should timeout properly
        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_with_timeout(slow_operation(), timeout=0.1)

        # Should complete if within timeout
        result = await timeout_handler.execute_with_timeout(
            slow_operation(), timeout=2.0
        )
        assert result == "completed"
