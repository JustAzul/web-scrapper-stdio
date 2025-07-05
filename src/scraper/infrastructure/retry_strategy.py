"""
RetryStrategy - Single Responsibility: Implementation of retry with
exponential backoff
"""

import asyncio
from typing import Awaitable, Callable, TypeVar

from src.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class RetryStrategy:
    """Implements retry strategy with exponential backoff following SRP."""

    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        """
        Initializes the retry strategy.
        Args:
            max_retries: Maximum number of attempts.
            initial_delay: Initial delay in seconds.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.logger = logger

    async def execute_async(
        self, async_func: Callable[..., Awaitable[T]], *args, **kwargs
    ) -> T:
        """
        Executes an asynchronous function with the retry strategy.
        Raises:
            Exception: The last exception if all attempts fail.
        """
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Attempt {attempt + 1}/{self.max_retries + 1}")
                return await async_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt >= self.max_retries:
                    self.logger.error(f"Final attempt {attempt + 1} failed: {e}")
                    break
                delay = self.initial_delay * (2**attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        raise Exception(
            f"All {self.max_retries + 1} attempts failed. Last error: {last_exception}"
        ) from last_exception

    def get_max_retries(self) -> int:
        """Returns the configured maximum number of attempts."""
        return self.max_retries

    def get_initial_delay(self) -> float:
        """Returns the configured initial delay."""
        return self.initial_delay

    def calculate_total_max_time(self) -> float:
        """Calculates the maximum total time considering all delays."""
        total_time = 0.0
        for attempt in range(self.max_retries):
            total_time += self.initial_delay * (2**attempt)
        return total_time

    def __repr__(self) -> str:
        """String representation of the retry strategy."""
        return (
            f"RetryStrategy(max_retries={self.max_retries}, "
            f"initial_delay={self.initial_delay}s, "
            f"max_total_time={self.calculate_total_max_time():.1f}s)"
        )
