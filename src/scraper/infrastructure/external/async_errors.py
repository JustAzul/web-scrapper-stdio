"""
AsyncErrorHandler - Fully async error handling implementation

This provides a fully async interface for error handling operations,
eliminating any sync/async inconsistencies in the error handling system.
Part of T013 - Async/Await Standardization.
"""

import asyncio
import re
from typing import Any, Optional

from src.logger import get_logger

logger = get_logger(__name__)


class AsyncErrorHandler:
    """
    Fully async error handler that provides consistent async interface.

    This class standardizes error handling operations to be fully async,
    eliminating the mixed sync/async patterns found in the original
    error handling implementation.

    Benefits:
    - Consistent async-only API
    - Better integration with async codebases
    - Proper async resource management
    - No blocking operations
    """

    def __init__(self):
        """Initialize async error handler."""
        self.logger = logger

        # Cloudflare detection patterns
        self.cloudflare_patterns = [
            r"checking your browser",
            r"cloudflare",
            r"ray id",
            r"please wait",
            r"ddos protection",
            r"security check",
        ]

        # Compile patterns for better performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.cloudflare_patterns
        ]

    async def detect_cloudflare_challenge_async(self, html_content: str) -> bool:
        """
        Detect Cloudflare challenge asynchronously.

        Args:
            html_content: HTML content to check

        Returns:
            True if Cloudflare challenge detected, False otherwise
        """
        if not html_content:
            return False

        # Convert to lowercase for case-insensitive matching
        content_lower = html_content.lower()

        # Check for Cloudflare patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content_lower):
                self.logger.warning("Cloudflare challenge detected in content")
                return True

        return False

    async def navigate_and_handle_errors_async(
        self, page: Any, url: str, timeout_seconds: int
    ) -> str:
        """
        Navigate to URL with async error handling.

        Args:
            page: Playwright page object
            url: URL to navigate to
            timeout_seconds: Navigation timeout

        Returns:
            Final URL after navigation

        Raises:
            Exception: If navigation fails after error handling
        """
        try:
            self.logger.debug(f"Navigating to {url} with {timeout_seconds}s timeout")

            # Navigate with timeout
            response = await page.goto(
                url,
                timeout=timeout_seconds * 1000,  # Convert to milliseconds
                wait_until="domcontentloaded",
            )

            if response is None:
                raise Exception(f"Navigation to {url} returned None response")

            # Check response status
            if response.status >= 400:
                self.logger.warning(f"HTTP {response.status} response for {url}")

            # Get final URL after redirects
            final_url = page.url
            self.logger.debug(f"Navigation completed. Final URL: {final_url}")

            return final_url

        except asyncio.TimeoutError:
            error_msg = f"Navigation timeout after {timeout_seconds}s for {url}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Navigation failed for {url}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def handle_cloudflare_block_async(
        self, html_content: str, page_url: str
    ) -> Optional[str]:
        """
        Handle Cloudflare block asynchronously.

        Args:
            html_content: HTML content that might contain Cloudflare block
            page_url: URL of the page

        Returns:
            Error message if Cloudflare block detected, None otherwise
        """
        is_cloudflare = await self.detect_cloudflare_challenge_async(html_content)

        if is_cloudflare:
            error_msg = (
                f"Cloudflare challenge detected at {page_url}. "
                "This content cannot be extracted due to anti-bot protection."
            )
            self.logger.warning(error_msg)
            return error_msg

        return None

    async def handle_network_errors_async(
        self, error: Exception, url: str, retry_count: int = 0
    ) -> Optional[str]:
        """
        Handle network errors asynchronously with retry logic.

        Args:
            error: The network error that occurred
            url: URL that caused the error
            retry_count: Current retry attempt count

        Returns:
            Error message string if error should be reported, None if should retry
        """
        error_str = str(error)

        # Categorize network errors
        if "net::ERR_NAME_NOT_RESOLVED" in error_str:
            self.logger.error(f"DNS resolution failed for {url}: {error}")
            return f"Could not resolve host: {url}"

        elif "net::ERR_CONNECTION_REFUSED" in error_str:
            self.logger.error(f"Connection refused for {url}: {error}")
            return f"Could not connect to host: {url}"

        elif "net::ERR_CONNECTION_TIMED_OUT" in error_str:
            self.logger.warning(f"Connection timeout for {url}: {error}")
            if retry_count < 3:
                return None  # Signal retry
            return f"Connection timeout after {retry_count} retries: {url}"

        elif "Target closed" in error_str:
            self.logger.error(f"Browser tab closed unexpectedly for {url}: {error}")
            return "Browser tab closed unexpectedly during operation"

        else:
            self.logger.error(f"Unexpected network error for {url}: {error}")
            return f"Network error: {error_str}"

    async def handle_http_error_async(self, status_code: int, url: str) -> str:
        """
        Handle HTTP errors asynchronously.

        Args:
            status_code: HTTP status code
            url: URL that returned the error

        Returns:
            Formatted error message
        """
        if status_code == 404:
            error_msg = f"Page not found (404) at {url}"
        elif status_code == 403:
            error_msg = f"Access forbidden (403) at {url}"
        elif status_code == 500:
            error_msg = f"Server error (500) at {url}"
        elif status_code >= 400:
            error_msg = f"HTTP {status_code} error at {url}"
        else:
            error_msg = f"Unexpected HTTP status {status_code} at {url}"

        self.logger.warning(error_msg)
        return error_msg

    async def handle_parsing_error_async(
        self, error: Exception, content_type: str = "HTML"
    ) -> str:
        """
        Handle content parsing errors asynchronously.

        Args:
            error: Parsing error that occurred
            content_type: Type of content being parsed

        Returns:
            Formatted error message
        """
        error_msg = f"{content_type} parsing error: {str(error)}"
        self.logger.error(error_msg)
        return error_msg

    async def is_recoverable_error_async(self, error: Exception) -> bool:
        """
        Check if an error is recoverable asynchronously.

        Args:
            error: Error to check

        Returns:
            True if error is recoverable, False otherwise
        """
        error_str = str(error).lower()

        # Recoverable errors (can retry)
        recoverable_patterns = [
            "timeout",
            "connection reset",
            "temporary failure",
            "network unreachable",
            "502",  # Bad Gateway
            "503",  # Service Unavailable
            "504",  # Gateway Timeout
        ]

        for pattern in recoverable_patterns:
            if pattern in error_str:
                return True

        return False

    async def cleanup(self) -> None:
        """
        Cleanup error handler resources.

        Currently no resources to cleanup, but provided for consistency.
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the async error handler."""
        return f"AsyncErrorHandler(patterns={len(self.cloudflare_patterns)})"
