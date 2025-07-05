"""
TimeoutConfig - Single Responsibility: Timeout management

Extracted from ScrapingConfig to follow SRP principle.
This class is responsible only for timeout-related configuration.
"""

from dataclasses import dataclass
from typing import Optional

from src.scraper.domain.value_objects.value_objects import TimeoutValue
from src.settings import DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class TimeoutConfig:
    """
    Configuration for timeout management.

    Single Responsibility: Handles all timeout-related configuration and validation.
    """

    page_timeout: Optional[TimeoutValue] = None
    grace_period: Optional[TimeoutValue] = None

    def __post_init__(self):
        """Set default values and validate after initialization."""
        # Set default page timeout if not provided
        if self.page_timeout is None:
            object.__setattr__(
                self, "page_timeout", TimeoutValue(DEFAULT_TIMEOUT_SECONDS)
            )

        # Set default grace period if not provided
        if self.grace_period is None:
            object.__setattr__(self, "grace_period", TimeoutValue(2.0))

        # Validate timeout values
        if self.page_timeout.seconds <= 0:
            raise ValueError("page_timeout must be positive")

        if self.grace_period.seconds <= 0:
            raise ValueError("grace_period must be positive")

    @property
    def total_timeout(self) -> TimeoutValue:
        """Get total timeout (page timeout + grace period)."""
        return TimeoutValue(self.page_timeout.seconds + self.grace_period.seconds)

    @property
    def page_timeout_milliseconds(self) -> int:
        """Get page timeout in milliseconds."""
        return self.page_timeout.milliseconds

    @property
    def grace_period_milliseconds(self) -> int:
        """Get grace period in milliseconds."""
        return self.grace_period.milliseconds

    def with_page_timeout(self, timeout_seconds: float) -> "TimeoutConfig":
        """Create new TimeoutConfig with different page timeout."""
        return TimeoutConfig(
            page_timeout=TimeoutValue(timeout_seconds), grace_period=self.grace_period
        )

    def with_grace_period(self, grace_seconds: float) -> "TimeoutConfig":
        """Create new TimeoutConfig with different grace period."""
        return TimeoutConfig(
            page_timeout=self.page_timeout, grace_period=TimeoutValue(grace_seconds)
        )

    def __str__(self) -> str:
        """String representation."""
        return f"TimeoutConfig(page={self.page_timeout}, grace={self.grace_period})"
