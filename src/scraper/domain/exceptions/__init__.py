"""
Standardized Exception Hierarchy for Web Scraper MCP.

This module implements an exception hierarchy following best practices:
1. Base exception with error codes and context
2. Specific exception types for different error scenarios
3. Consistent error handling patterns
4. Detailed error context for debugging
"""

from typing import Any, Dict, Optional


class ScraperError(Exception):
    """
    Base exception for all scraper-related errors.

    Provides a standardized interface with error codes, context, and recovery hints.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        retry_after: Optional[float] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.original_exception = original_exception

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "original_exception": (
                str(self.original_exception) if self.original_exception else None
            ),
        }


# Navigation and Browser Errors
class NavigationError(ScraperError):
    """Raised when navigation to a URL fails."""

    def __init__(self, url: str, message: str, **kwargs):
        super().__init__(
            message=f"Navigation failed for {url}: {message}",
            error_code="NAV_FAILED",
            context={"url": url},
            recoverable=True,
            **kwargs,
        )


class TimeoutError(ScraperError):
    """Raised when operations exceed timeout limits."""

    def __init__(self, operation: str, timeout: float, **kwargs):
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout}s",
            error_code="TIMEOUT",
            context={"operation": operation, "timeout": timeout},
            recoverable=True,
            retry_after=timeout * 1.5,
            **kwargs,
        )


class BrowserError(ScraperError):
    """Raised when browser operations fail."""

    def __init__(self, message: str, browser_type: str = "unknown", **kwargs):
        super().__init__(
            message=f"Browser error ({browser_type}): {message}",
            error_code="BROWSER_ERROR",
            context={"browser_type": browser_type},
            recoverable=False,
            **kwargs,
        )


# Content Processing Errors
class ContentExtractionError(ScraperError):
    """Raised when content extraction fails."""

    def __init__(self, message: str, url: str, extraction_type: str = "html", **kwargs):
        super().__init__(
            message=f"Content extraction failed for {url}: {message}",
            error_code="CONTENT_EXTRACTION_FAILED",
            context={"url": url, "extraction_type": extraction_type},
            recoverable=True,
            **kwargs,
        )


class ParsingError(ScraperError):
    """Raised when HTML/content parsing fails."""

    def __init__(self, message: str, parser: str = "unknown", **kwargs):
        super().__init__(
            message=f"Parsing failed ({parser}): {message}",
            error_code="PARSING_FAILED",
            context={"parser": parser},
            recoverable=True,
            **kwargs,
        )


class ContentValidationError(ScraperError):
    """Raised when extracted content fails validation."""

    def __init__(self, message: str, validation_rule: str, **kwargs):
        super().__init__(
            message=f"Content validation failed ({validation_rule}): {message}",
            error_code="CONTENT_INVALID",
            context={"validation_rule": validation_rule},
            recoverable=False,
            **kwargs,
        )


# Network and Rate Limiting Errors
class NetworkError(ScraperError):
    """Raised when network operations fail."""

    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(
            message=f"Network error: {message}",
            error_code="NETWORK_ERROR",
            context={"status_code": status_code},
            recoverable=True,
            retry_after=5.0,
            **kwargs,
        )


class RateLimitError(ScraperError):
    """Raised when rate limiting is triggered."""

    def __init__(self, domain: str, retry_after: float = 60.0, **kwargs):
        super().__init__(
            message=f"Rate limit exceeded for domain {domain}",
            error_code="RATE_LIMIT_EXCEEDED",
            context={"domain": domain},
            recoverable=True,
            retry_after=retry_after,
            **kwargs,
        )


class CloudflareBlockError(ScraperError):
    """Raised when Cloudflare or similar protection blocks access."""

    def __init__(self, url: str, protection_type: str = "cloudflare", **kwargs):
        super().__init__(
            message=f"Access blocked by {protection_type} for {url}",
            error_code="ACCESS_BLOCKED",
            context={"url": url, "protection_type": protection_type},
            recoverable=True,
            retry_after=30.0,
            **kwargs,
        )


# Configuration and System Errors
class ConfigurationError(ScraperError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: str, **kwargs):
        super().__init__(
            message=f"Configuration error for '{config_key}': {message}",
            error_code="CONFIG_ERROR",
            context={"config_key": config_key},
            recoverable=False,
            **kwargs,
        )


class ResourceError(ScraperError):
    """Raised when system resources are exhausted."""

    def __init__(self, resource_type: str, message: str, **kwargs):
        # Pop the context from kwargs to merge it
        incoming_context = kwargs.pop("context", {})

        # Create the base context and update it with the incoming context
        base_context = {"resource_type": resource_type}
        base_context.update(incoming_context)

        super().__init__(
            message=f"Resource exhausted ({resource_type}): {message}",
            error_code="RESOURCE_EXHAUSTED",
            context=base_context,
            recoverable=True,
            retry_after=10.0,
            **kwargs,
        )


class MemoryError(ResourceError):
    """Raised when memory limits are exceeded."""

    def __init__(self, memory_usage_mb: float, limit_mb: float, **kwargs):
        super().__init__(
            resource_type="memory",
            message=(
                f"Memory usage {memory_usage_mb:.1f}MB exceeds limit {limit_mb:.1f}MB"
            ),
            context={"memory_usage_mb": memory_usage_mb, "limit_mb": limit_mb},
            **kwargs,
        )


# Validation and Input Errors
class ValidationError(ScraperError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: Any, message: str, **kwargs):
        super().__init__(
            message=f"Validation failed for '{field}': {message}",
            error_code="VALIDATION_ERROR",
            context={"field": field, "value": str(value)},
            recoverable=False,
            **kwargs,
        )


class URLValidationError(ValidationError):
    """Raised when URL validation fails."""

    def __init__(self, url: str, reason: str, **kwargs):
        super().__init__(
            field="url", value=url, message=f"Invalid URL: {reason}", **kwargs
        )


# Utility functions for error handling
def wrap_exception(
    original_exception: Exception,
    error_code: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    recoverable: bool = True,
) -> ScraperError:
    """
    Wrap a generic exception in a ScraperError.

    Args:
        original_exception: The original exception to wrap
        error_code: Error code for the new exception
        message: Human-readable error message
        context: Additional context information
        recoverable: Whether the error is recoverable

    Returns:
        ScraperError: Wrapped exception with standardized interface
    """
    return ScraperError(
        message=message,
        error_code=error_code,
        context=context,
        recoverable=recoverable,
        original_exception=original_exception,
    )


def is_recoverable_error(exception: Exception) -> bool:
    """
    Check if an exception is recoverable.

    Args:
        exception: Exception to check

    Returns:
        bool: True if the exception is recoverable
    """
    if isinstance(exception, ScraperError):
        return exception.recoverable

    # Default heuristics for non-ScraperError exceptions
    recoverable_types = (
        ConnectionError,
        TimeoutError,
        OSError,
    )

    return isinstance(exception, recoverable_types)


def get_retry_delay(exception: Exception) -> Optional[float]:
    """
    Get the recommended retry delay for an exception.

    Args:
        exception: Exception to analyze

    Returns:
        Optional[float]: Recommended retry delay in seconds, or None if no retry
        recommended
    """
    if isinstance(exception, ScraperError):
        return exception.retry_after

    # Default retry delays for common exceptions
    if isinstance(exception, (ConnectionError, OSError)):
        return 5.0
    elif isinstance(exception, TimeoutError):
        return 10.0

    return None


def get_recommended_retry_delay(
    exception: Exception,
    retry_config: Optional[Dict[str, Any]] = None,
    current_attempt: int = 0,
) -> Optional[float]:
    """
    Determines the recommended retry delay based on exception type and retry config.

    Returns:
        Optional[float]: Recommended retry delay in seconds, or None if
        no retry recommended
    """
    if isinstance(exception, ScraperError):
        if exception.retryable:
            # Simple exponential backoff for now
            return 2**current_attempt * get_retry_delay(exception)

    return None


# Export all exception classes and utilities
__all__ = [
    # Base exception
    "ScraperError",
    # Navigation and browser errors
    "NavigationError",
    "TimeoutError",
    "BrowserError",
    # Content processing errors
    "ContentExtractionError",
    "ParsingError",
    "ContentValidationError",
    # Network and rate limiting errors
    "NetworkError",
    "RateLimitError",
    "CloudflareBlockError",
    # Configuration and system errors
    "ConfigurationError",
    "ResourceError",
    "MemoryError",
    # Validation and input errors
    "ValidationError",
    "URLValidationError",
    # Utility functions
    "wrap_exception",
    "is_recoverable_error",
    "get_retry_delay",
    "get_recommended_retry_delay",
]
