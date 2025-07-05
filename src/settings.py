"""
Pydantic Settings Implementation for Web Scrapper MCP.

This module replaces the manual config.py with a Pydantic Settings system
that provides type validation, environment variable loading, and documentation.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

from src.core.constants import (
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    DEFAULT_TIMEOUT_SECONDS,
)


class Settings(PydanticBaseSettings):
    """
    Application settings using Pydantic for validation and environment loading.

    This class replaces the manual config.py with proper type validation,
    environment variable loading, and clear documentation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        validate_assignment=True,
        use_enum_values=True,
    )

    # Timeout settings
    default_timeout_seconds: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        description="Timeout for page loads and navigation (in seconds)",
        gt=0,
    )

    # Content length settings
    default_min_content_length: int = Field(
        default=100,
        description=(
            "Minimum content length required for extracted text (in characters)"
        ),
        gt=0,
    )

    default_min_content_length_search_app: int = Field(
        default=30,  # This is a content length, not a timeout - keep as is
        description=(
            "Lower minimum content length for search.app domains (in characters)"
        ),
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

    allow_localhost: bool = Field(
        default=False,
        description=(
            "Allow scraping of localhost and local IP addresses. FOR DEVELOPMENT ONLY."
        ),
    )

    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/108.0.0.0 Safari/537.36"
        ),
        description="User-Agent string for browser requests",
    )

    # Circuit breaker settings
    circuit_breaker_threshold: int = Field(
        default=5,
        description="Number of failures before opening the circuit breaker",
        gt=0,
    )
    circuit_breaker_recovery_seconds: int = Field(
        default=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        description=(
            "Number of seconds before the circuit breaker enters half-open state"
        ),
        gt=0,
    )

    # Retry settings
    retry_max_retries: int = 3
    retry_initial_delay: float = 1.0

    # Fallback and Retry
    fallback_enabled: bool = Field(
        True, description="Enable fallback to secondary scraper."
    )
    max_retries: int = Field(
        3, description="Maximum number of retries for a failed request."
    )
    retry_delay_seconds: int = Field(
        5, description="Delay in seconds between retries."
    )

    # Server Configuration
    server_host: str = Field("127.0.0.1", description="Host for the MCP server.")
    server_port: int = Field(8080, description="Port for the MCP server.")

    # Service Information
    service_name: str = Field("mcp-web-scraper", description="Name of the service.")
    service_version: str = "0.1.0"
    log_level: str = "INFO"

    # Playwright settings
    playwright_timeout: int = DEFAULT_TIMEOUT_SECONDS
    enable_resource_blocking: bool = True
    blocked_resource_types: list[str] = [
        "image",
        "stylesheet",
        "font",
        "media",
        "other",
    ]

    # Requests settings
    requests_timeout: int = 15

    @field_validator("debug_logs_enabled", mode="before")
    def parse_debug_logs(cls, v: any) -> bool:
        """Parse debug logs from various string formats with strict validation"""
        if isinstance(v, str):
            lower_v = v.lower()
            if lower_v in ("true", "1", "yes", "on"):
                return True
            elif lower_v in ("false", "0", "no", "off"):
                return False
            else:
                raise ValueError(
                    f"Invalid boolean value: '{v}'. Must be one of: true, false, 1, "
                    "0, yes, no, on, off"
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
CIRCUIT_BREAKER_THRESHOLD = _settings.circuit_breaker_threshold
CIRCUIT_BREAKER_RECOVERY_SECONDS = _settings.circuit_breaker_recovery_seconds
DEFAULT_TEST_REQUEST_TIMEOUT = _settings.default_test_request_timeout
DEFAULT_TEST_NO_DELAY_THRESHOLD = _settings.default_test_no_delay_threshold
DEBUG_LOGS_ENABLED = _settings.debug_logs_enabled
ALLOW_LOCALHOST = _settings.allow_localhost
USER_AGENT = _settings.user_agent
