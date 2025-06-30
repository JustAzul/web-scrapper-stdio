"""
DEPRECATED: Configuration module for Web Scrapper MCP.

This module is deprecated in favor of the new Pydantic-based settings system.
Please migrate to using `from src.settings import get_settings` instead.

This module will be removed in a future version.
"""

import os
import warnings
from typing import Union

# Issue deprecation warning when this module is imported
warnings.warn(
    "src.config is deprecated. Please use 'from src.settings import get_settings' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


def _get_env_int(key: str, default: int) -> int:
    """Get integer environment variable with default."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_env_float(key: str, default: Union[int, float]) -> float:
    """Get float environment variable with default."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return float(default)


# Import from the new settings system for backward compatibility
try:
    from src.settings import get_settings

    _settings = get_settings()

    # Backward compatibility exports - redirect to new settings
    DEFAULT_TIMEOUT_SECONDS = _settings.default_timeout_seconds
    DEFAULT_MIN_CONTENT_LENGTH = _settings.default_min_content_length
    DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP = (
        _settings.default_min_content_length_search_app
    )
    DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = (
        _settings.default_min_seconds_between_requests
    )
    DEFAULT_TEST_REQUEST_TIMEOUT = _settings.default_test_request_timeout
    DEFAULT_TEST_NO_DELAY_THRESHOLD = _settings.default_test_no_delay_threshold
    DEBUG_LOGS_ENABLED = _settings.debug_logs_enabled

except ImportError:
    # Fallback to old implementation if settings module is not available
    warnings.warn(
        "Could not import new settings system. Using fallback configuration.",
        RuntimeWarning,
        stacklevel=2,
    )

    # Timeout for page loads and navigation (in seconds)
    DEFAULT_TIMEOUT_SECONDS = _get_env_int("DEFAULT_TIMEOUT_SECONDS", 30)
    # Minimum content length required for extracted text (in characters)
    DEFAULT_MIN_CONTENT_LENGTH = _get_env_int("DEFAULT_MIN_CONTENT_LENGTH", 100)
    # Lower minimum content length for search.app domains (in characters)
    DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP = 30
    # Minimum delay between requests to the same domain (in seconds)
    DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = _get_env_float(
        "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS", 2
    )
    # Timeout for test requests (in seconds)
    DEFAULT_TEST_REQUEST_TIMEOUT = _get_env_int("DEFAULT_TEST_REQUEST_TIMEOUT", 10)
    # Threshold for skipping artificial delays in tests (in seconds)
    DEFAULT_TEST_NO_DELAY_THRESHOLD = _get_env_float(
        "DEFAULT_TEST_NO_DELAY_THRESHOLD", 0.5
    )

    # Debug logging toggle
    DEBUG_LOGS_ENABLED = os.getenv("DEBUG_LOGS_ENABLED", "false").lower() == "true"
