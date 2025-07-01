"""
ScrapingRequest Parameter Object

Replaces the 10 parameters in WebScrapingService.scrape_url with a single object
following the Parameter Object pattern to reduce complexity and improve maintainability.
"""

from dataclasses import dataclass
from typing import List, Optional

from src.enums import OutputFormat


@dataclass
class ScrapingRequest:
    """Represents a request for scraping a URL."""

    url: str
    output_format: OutputFormat = OutputFormat.MARKDOWN
    timeout_seconds: Optional[int] = None
    custom_elements_to_remove: Optional[List[str]] = None
    grace_period_seconds: float = 2.0
    max_length: Optional[int] = None
    user_agent: Optional[str] = None
    wait_for_network_idle: bool = True
    click_selector: Optional[str] = None
    custom_timeout: Optional[int] = None

    def __post_init__(self):
        if not self.url:
            raise ValueError("URL is required")
        if self.timeout_seconds is not None and self.timeout_seconds < 0:
            raise ValueError("timeout_seconds must be positive")
        if self.grace_period_seconds < 0:
            raise ValueError("grace_period_seconds must be positive")
        if self.max_length is not None and self.max_length < 0:
            raise ValueError("max_length must be positive")

        # Backward compatibility for custom_timeout
        if self.custom_timeout is not None and self.timeout_seconds is None:
            self.timeout_seconds = self.custom_timeout

    @classmethod
    def from_legacy_parameters(cls, **kwargs):
        new_kwargs = kwargs.copy()
        if "elements_to_remove" in new_kwargs:
            new_kwargs["custom_elements_to_remove"] = new_kwargs.pop(
                "elements_to_remove"
            )

        if "custom_timeout" in new_kwargs and new_kwargs.get("timeout_seconds") is None:
            new_kwargs["timeout_seconds"] = new_kwargs["custom_timeout"]

        # Remove the legacy key to avoid passing it to the dataclass __init__
        new_kwargs.pop("custom_timeout", None)

        return cls(**new_kwargs)

    def has_click_selector(self) -> bool:
        """Check if a click selector is provided and not empty."""
        return bool(self.click_selector and self.click_selector.strip())

    def get_effective_timeout(self) -> Optional[int]:
        """Get the effective timeout, preferring timeout_seconds over legacy custom_timeout."""
        return (
            self.timeout_seconds
            if self.timeout_seconds is not None
            else self.custom_timeout
        )

    def get_elements_to_remove(self) -> List[str]:
        """Get elements to remove, returning an empty list if None."""
        return self.custom_elements_to_remove or []
