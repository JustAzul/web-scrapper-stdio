"""
RetryStrategyFactory - Async-only retry strategy pattern

This is the standardized version of RetryStrategy that eliminates
the sync/async inconsistency by providing only async methods.
Part of T013 - Async/Await Standardization.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

from src.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryStrategyFactory:
    """
    Retry strategy factory that uses only async patterns.

    This class eliminates the async/sync inconsistency found in the original
    RetryStrategy by providing only async methods and adapting sync
    functions to async when needed.

    Benefits:
    - Consistent async-only API
    - Better integration with async codebases
    - Proper resource management with asyncio
    - No blocking operations in async context
    """

    def __init__(self, max_retries: int, initial_delay: float = 1.0):
        """
        Initialize retry strategy factory.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.logger = logger
        self._executor = None  # Lazy initialization

    async def execute(self, async_func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute async function with retry and exponential backoff.

        Args:
            async_func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Named arguments for the function

        Returns:
            Result of the function executed successfully

        Raises:
            Exception: The last exception if all attempts fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Async attempt {attempt + 1}/{self.max_retries + 1}")
                return await async_func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if attempt >= self.max_retries:
                    self.logger.error(f"Final async attempt {attempt + 1} failed: {e}")
                    break

                # Calculate exponential delay: 1s, 2s, 4s, 8s, etc.
                delay = self.initial_delay * (2**attempt)
                self.logger.warning(
                    f"Async attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)  # Always use async sleep

        # If we reach here, all attempts failed
        raise last_exception

    async def execute_sync_as_async(
        self, sync_func: Callable[..., T], *args, **kwargs
    ) -> T:
        """
        Execute sync function as async using thread pool, with retry and
        exponential backoff.

        This method adapts synchronous functions to work in async context,
        eliminating the need for a separate sync execution method.

        Args:
            sync_func: Sync function to execute
            *args: Positional arguments for the function
            **kwargs: Named arguments for the function

        Returns:
            Result of the function executed successfully

        Raises:
            Exception: The last exception if all attempts fail
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(
                    f"Sync-as-async attempt {attempt + 1}/{self.max_retries + 1}"
                )

                # Execute sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor, lambda: sync_func(*args, **kwargs)
                )
                return result

            except Exception as e:
                last_exception = e

                if attempt >= self.max_retries:
                    self.logger.error(
                        f"Final sync-as-async attempt {attempt + 1} failed: {e}"
                    )
                    break

                # Calculate exponential delay
                delay = self.initial_delay * (2**attempt)
                self.logger.warning(
                    f"Sync-as-async attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)  # Always use async sleep

        # If we reach here, all attempts failed
        raise last_exception

    def get_max_retries(self) -> int:
        """
        Get maximum number of retries configured.

        Returns:
            Maximum number of retries
        """
        return self.max_retries

    def get_initial_delay(self) -> float:
        """
        Get initial delay configured.

        Returns:
            Initial delay in seconds
        """
        return self.initial_delay

    def calculate_total_max_time(self) -> float:
        """
        Calculate maximum total time considering all delays.

        Returns:
            Maximum total time in seconds
        """
        total_time = 0.0
        for attempt in range(self.max_retries):
            total_time += self.initial_delay * (2**attempt)
        return total_time

    async def cleanup(self):
        """
        Cleanup resources (thread pool executor).

        Should be called when the retry strategy is no longer needed.
        """
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the retry strategy factory."""
        return (
            f"RetryStrategyFactory(max_retries={self.max_retries}, "
            f"initial_delay={self.initial_delay}s, "
            f"max_total_time={self.calculate_total_max_time():.1f}s)"
        )
