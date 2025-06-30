"""
Pydantic Settings Implementation for Web Scrapper MCP.

This module replaces the manual config.py with a robust Pydantic Settings system
that provides type validation, environment variable loading, and documentation.

TDD Implementation: GREEN phase - minimum code to pass tests.
"""

from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    """
    Application settings using Pydantic for validation and environment loading.

    This class replaces the manual config.py with proper type validation,
    environment variable loading, and comprehensive documentation.
    """

    # Timeout settings
    default_timeout_seconds: int = Field(
        default=30,
        description="Timeout for page loads and navigation (in seconds)",
        gt=0,
    )

    # Content length settings
    default_min_content_length: int = Field(
        default=100,
        description="Minimum content length required for extracted text (in characters)",
        gt=0,
    )

    default_min_content_length_search_app: int = Field(
        default=30,
        description="Lower minimum content length for search.app domains (in characters)",
        ge=0,
    )

    # Rate limiting settings
    default_min_seconds_between_requests: float = Field(
        default=2.0,
        description="Minimum delay between requests to the same domain (in seconds)",
        ge=0.0,
    )

    # Test settings
    default_test_request_timeout: int = Field(
        default=10, description="Timeout for test requests (in seconds)", gt=0
    )

    default_test_no_delay_threshold: float = Field(
        default=0.5,
        description="Threshold for skipping artificial delays in tests (in seconds)",
        ge=0.0,
    )

    # Debug settings
    debug_logs_enabled: bool = Field(
        default=False, description="Enable debug logging output"
    )

    class Config:
        # Environment variable settings
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # Support both prefixed and non-prefixed environment variables
        env_prefix = ""

        # Allow validation of assignment
        validate_assignment = True

        # Use enum values for serialization
        use_enum_values = True

    @validator("debug_logs_enabled", pre=True)
    def parse_debug_logs(cls, v):
        """Parse debug logs from various string formats with strict validation"""
        if isinstance(v, str):
            lower_v = v.lower()
            if lower_v in ("true", "1", "yes", "on"):
                return True
            elif lower_v in ("false", "0", "no", "off"):
                return False
            else:
                raise ValueError(
                    f"Invalid boolean value: '{v}'. Must be one of: true, false, 1, 0, yes, no, on, off"
                )
        return bool(v)


# Singleton pattern for global settings access
@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings instance (singleton pattern).

    Returns:
        Settings: The application settings instance
    """
    return Settings()


def reload_settings():
    """
    Reload settings by clearing the cache.
    Useful for testing and dynamic configuration changes.
    """
    get_settings.cache_clear()


# Create global settings instance
_settings = get_settings()

# Backward compatibility exports - maintain the same interface as config.py
DEFAULT_TIMEOUT_SECONDS = _settings.default_timeout_seconds
DEFAULT_MIN_CONTENT_LENGTH = _settings.default_min_content_length
DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP = _settings.default_min_content_length_search_app
DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = _settings.default_min_seconds_between_requests
DEFAULT_TEST_REQUEST_TIMEOUT = _settings.default_test_request_timeout
DEFAULT_TEST_NO_DELAY_THRESHOLD = _settings.default_test_no_delay_threshold
DEBUG_LOGS_ENABLED = _settings.debug_logs_enabled
