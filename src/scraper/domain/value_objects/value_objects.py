"""
Value objects for the scraper module.

These classes replace primitive obsession by encapsulating commonly used
values with proper validation, type safety, and meaningful operations.
"""

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

from src.core.constants import (
    BYTES_PER_MB,
    MAX_TIMEOUT_SECONDS,
    MB_PER_KB,
    MILLISECONDS_PER_SECOND,
)
from src.output_format_handler import OutputFormat
from src.settings import DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class TimeoutValue:
    """
    Represents a timeout value with validation and unit conversion.

    Provides type safety for timeout values and automatic conversion
    between seconds and milliseconds.
    """

    _seconds: float

    def __init__(self, seconds: float):
        if seconds <= 0:
            raise ValueError("Timeout must be positive")
        if (
            seconds > MAX_TIMEOUT_SECONDS
        ):  # Use named constant instead of magic number 240
            raise ValueError(f"Timeout too large (max {MAX_TIMEOUT_SECONDS} seconds)")

        # Use object.__setattr__ because the class is frozen
        object.__setattr__(self, "_seconds", float(seconds))

    @property
    def seconds(self) -> float:
        """Get timeout in seconds."""
        return self._seconds

    @property
    def milliseconds(self) -> int:
        """Get timeout in milliseconds."""
        return int(
            self._seconds * MILLISECONDS_PER_SECOND
        )  # Use named constant instead of magic number 1000

    @classmethod
    def from_milliseconds(cls, milliseconds: int) -> "TimeoutValue":
        """Create timeout from milliseconds."""
        return cls(
            milliseconds / MILLISECONDS_PER_SECOND
        )  # Use named constant instead of magic number 1000.0

    def __str__(self) -> str:
        """String representation of timeout."""
        if self._seconds == int(self._seconds):
            return f"{int(self._seconds)}s"
        return f"{self._seconds}s"

    def __lt__(self, other: "TimeoutValue") -> bool:
        return self._seconds < other._seconds

    def __le__(self, other: "TimeoutValue") -> bool:
        return self._seconds <= other._seconds

    def __gt__(self, other: "TimeoutValue") -> bool:
        return self._seconds > other._seconds

    def __ge__(self, other: "TimeoutValue") -> bool:
        return self._seconds >= other._seconds

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeoutValue):
            return False
        return self._seconds == other._seconds


@dataclass(frozen=True)
class MemorySize:
    """
    Represents a memory size with validation and unit conversion.

    Provides type safety for memory sizes and automatic conversion
    between different units.
    """

    _megabytes: float

    def __init__(self, megabytes: float):
        if megabytes <= 0:
            raise ValueError("Memory size must be positive")

        # Use object.__setattr__ because the class is frozen
        object.__setattr__(self, "_megabytes", float(megabytes))

    @property
    def megabytes(self) -> float:
        """Get memory size in megabytes."""
        return self._megabytes

    @property
    def kilobytes(self) -> float:
        """Get memory size in kilobytes."""
        return (
            self._megabytes * MB_PER_KB
        )  # Use named constant instead of magic number 1024

    @property
    def bytes(self) -> int:
        """Get memory size in bytes."""
        return int(
            self._megabytes * BYTES_PER_MB
        )  # Use named constant instead of magic number 1024 * 1024

    @classmethod
    def from_bytes(cls, bytes_value: int) -> "MemorySize":
        """Create memory size from bytes."""
        return cls(
            bytes_value / BYTES_PER_MB
        )  # Use named constant instead of magic number (1024 * 1024)

    @classmethod
    def from_kilobytes(cls, kilobytes: float) -> "MemorySize":
        """Create memory size from kilobytes."""
        return cls(
            kilobytes / MB_PER_KB
        )  # Use named constant instead of magic number 1024

    def __str__(self) -> str:
        """String representation of memory size."""
        if self._megabytes < 1:
            return f"{self.kilobytes:.1f}KB"
        # Show integer values without decimal point for whole numbers
        if self._megabytes == int(self._megabytes):
            return f"{int(self._megabytes)}MB"
        return f"{self._megabytes:.1f}MB"

    def __lt__(self, other: "MemorySize") -> bool:
        return self._megabytes < other._megabytes

    def __le__(self, other: "MemorySize") -> bool:
        return self._megabytes <= other._megabytes

    def __gt__(self, other: "MemorySize") -> bool:
        return self._megabytes > other._megabytes

    def __ge__(self, other: "MemorySize") -> bool:
        return self._megabytes >= other._megabytes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MemorySize):
            return False
        return self._megabytes == other._megabytes

    def __add__(self, other: "MemorySize") -> "MemorySize":
        """Add two memory sizes."""
        return MemorySize(self._megabytes + other._megabytes)

    def __sub__(self, other: "MemorySize") -> "MemorySize":
        """Subtract two memory sizes."""
        result = self._megabytes - other._megabytes
        if result <= 0:
            raise ValueError("Memory size subtraction result must be positive")
        return MemorySize(result)


@dataclass(frozen=True)
class ScrapingConfig:
    """
    DEPRECATED: This class is superseded by the ScrapingRequest model.
    It is maintained for backward compatibility and will be removed in a future version.

    Configuration object for web scraping operations.

    Replaces the long parameter list in extract_text_from_url with a
    well-structured, validated configuration object.
    """

    url: str
    timeout: Optional[TimeoutValue] = None
    grace_period: Optional[TimeoutValue] = None
    output_format: OutputFormat = OutputFormat.MARKDOWN
    wait_for_network_idle: bool = True
    max_length: Optional[int] = None
    user_agent: Optional[str] = None
    click_selector: Optional[str] = None
    custom_elements_to_remove: Optional[List[str]] = None

    def __post_init__(self):
        """Validate and set default values after initialization."""
        # Validate URL
        if not self.url:
            raise ValueError("URL is required")

        parsed = urlparse(self.url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

        # Set default timeout if not provided
        if self.timeout is None:
            object.__setattr__(self, "timeout", TimeoutValue(DEFAULT_TIMEOUT_SECONDS))

        # Set default grace period if not provided
        if self.grace_period is None:
            object.__setattr__(self, "grace_period", TimeoutValue(2.0))

        # Set default custom_elements_to_remove if not provided
        if self.custom_elements_to_remove is None:
            object.__setattr__(self, "custom_elements_to_remove", [])

        # Validate max_length
        if self.max_length is not None and self.max_length <= 0:
            raise ValueError("max_length must be positive")

    def to_dict(self) -> dict:
        """
        Convert config to dictionary for backwards compatibility.

        This allows the new config object to work with existing code
        that expects individual parameters.
        """
        return {
            "url": self.url,
            "custom_timeout": (
                self.timeout.seconds if self.timeout else DEFAULT_TIMEOUT_SECONDS
            ),
            "grace_period_seconds": (
                self.grace_period.seconds if self.grace_period else 2.0
            ),
            "output_format": self.output_format,
            "wait_for_network_idle": self.wait_for_network_idle,
            "max_length": self.max_length,
            "user_agent": self.user_agent,
            "click_selector": self.click_selector,
            "custom_elements_to_remove": self.custom_elements_to_remove or [],
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> "ScrapingConfig":
        """
        Create config from dictionary for backwards compatibility.

        This allows existing code that creates parameter dictionaries
        to work with the new config object.
        """
        # Convert timeout values
        timeout = None
        if "custom_timeout" in config_dict:
            timeout = TimeoutValue(config_dict["custom_timeout"])

        grace_period = None
        if "grace_period_seconds" in config_dict:
            grace_period = TimeoutValue(config_dict["grace_period_seconds"])

        return cls(
            url=config_dict["url"],
            timeout=timeout,
            grace_period=grace_period,
            output_format=config_dict.get("output_format", OutputFormat.MARKDOWN),
            wait_for_network_idle=config_dict.get("wait_for_network_idle", True),
            max_length=config_dict.get("max_length"),
            user_agent=config_dict.get("user_agent"),
            click_selector=config_dict.get("click_selector"),
            custom_elements_to_remove=config_dict.get("custom_elements_to_remove", []),
        )
