"""
AsyncRateLimiter - Fully async rate limiting implementation

This provides a fully async interface for rate limiting operations,
eliminating any sync/async inconsistencies in the rate limiting system.
Part of T013 - Async/Await Standardization.
"""

import asyncio
import time
from typing import Dict, Optional
from urllib.parse import urlparse

from src.logger import get_logger
from src.settings import DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS

logger = get_logger(__name__)


class AsyncRateLimiter:
    """
    Fully async rate limiter that provides consistent async interface.

    This class standardizes rate limiting operations to be fully async,
    eliminating the mixed sync/async patterns found in the original
    rate limiting implementation.

    Benefits:
    - Consistent async-only API
    - Better integration with async codebases
    - Proper async resource management
    - No blocking operations
    """

    def __init__(self, min_seconds_between_requests: float = None):
        """
        Initialize async rate limiter.

        Args:
            min_seconds_between_requests: Minimum seconds between requests to same domain
        """
        self.min_seconds_between_requests = (
            min_seconds_between_requests or DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS
        )
        self._domain_access_times: Dict[str, float] = {}
        self._domain_lock = asyncio.Lock()
        self.logger = logger

    async def get_domain_from_url_async(self, url: str) -> Optional[str]:
        """
        Extract domain from URL asynchronously.

        Args:
            url: URL to extract domain from

        Returns:
            Domain string or None if parsing fails
        """
        try:
            # URL parsing is CPU-bound but fast, so we can do it directly
            # In a real-world scenario with heavy URL processing, we might
            # want to use run_in_executor for this
            parsed = urlparse(url)
            domain = parsed.netloc

            if not domain:
                return None

            # Remove www. prefix
            domain = domain.replace("www.", "")
            return domain

        except ValueError:
            self.logger.warning(f"Could not parse domain from URL: {url}")
            return None

    async def apply_rate_limiting(self, url: str) -> None:
        """
        Apply rate limiting for the given URL asynchronously.

        Args:
            url: URL to apply rate limiting for
        """
        domain = await self.get_domain_from_url_async(url)

        if not domain:
            self.logger.warning(f"No valid domain for rate limiting: {url}")
            return

        async with self._domain_lock:
            current_time = time.time()
            last_access_time = self._domain_access_times.get(domain)

            if last_access_time:
                time_since_last = current_time - last_access_time

                if time_since_last < self.min_seconds_between_requests:
                    sleep_duration = self.min_seconds_between_requests - time_since_last

                    self.logger.warning(
                        f"Rate limiting {domain}: Sleeping for {sleep_duration:.2f}s"
                    )
                    await asyncio.sleep(sleep_duration)
                    current_time = time.time()

            self._domain_access_times[domain] = current_time

    async def get_last_access_time(self, url: str) -> Optional[float]:
        """
        Get the last access time for a domain asynchronously.

        Args:
            url: URL to check last access time for

        Returns:
            Last access time as timestamp or None if never accessed
        """
        domain = await self.get_domain_from_url_async(url)
        if not domain:
            return None

        async with self._domain_lock:
            return self._domain_access_times.get(domain)

    async def reset_domain_access(self, url: str) -> None:
        """
        Reset access time for a domain asynchronously.

        Args:
            url: URL whose domain access time should be reset
        """
        domain = await self.get_domain_from_url_async(url)
        if not domain:
            return

        async with self._domain_lock:
            if domain in self._domain_access_times:
                del self._domain_access_times[domain]

    async def get_time_until_next_request(self, url: str) -> float:
        """
        Get time until next request is allowed for a domain.

        Args:
            url: URL to check

        Returns:
            Seconds until next request is allowed (0 if can request now)
        """
        domain = await self.get_domain_from_url_async(url)
        if not domain:
            return 0.0

        async with self._domain_lock:
            last_access_time = self._domain_access_times.get(domain)
            if not last_access_time:
                return 0.0

            current_time = time.time()
            time_since_last = current_time - last_access_time

            if time_since_last >= self.min_seconds_between_requests:
                return 0.0
            else:
                return self.min_seconds_between_requests - time_since_last

    async def cleanup(self) -> None:
        """
        Cleanup rate limiter resources.

        Clears all domain access times.
        """
        async with self._domain_lock:
            self._domain_access_times.clear()

    def get_min_seconds_between_requests(self) -> float:
        """
        Get the configured minimum seconds between requests.

        Returns:
            Minimum seconds between requests
        """
        return self.min_seconds_between_requests

    def get_tracked_domains_count(self) -> int:
        """
        Get the number of domains currently being tracked.

        Returns:
            Number of tracked domains
        """
        return len(self._domain_access_times)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the async rate limiter."""
        return (
            f"AsyncRateLimiter(min_seconds={self.min_seconds_between_requests}, "
            f"tracked_domains={self.get_tracked_domains_count()})"
        )
