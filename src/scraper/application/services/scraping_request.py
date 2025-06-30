"""
ScrapingRequest Parameter Object

Replaces the 10 parameters in WebScrapingService.scrape_url with a single object
following the Parameter Object pattern to reduce complexity and improve maintainability.
"""

from dataclasses import dataclass
from typing import List, Optional

from src.output_format_handler import OutputFormat


@dataclass(frozen=True)
class ScrapingRequest:
    """
    Parameter object for web scraping requests.
    Encapsulates all scraping parameters into a single, immutable object.
    """

    url: str
    output_format: OutputFormat = OutputFormat.MARKDOWN
    timeout_seconds: Optional[int] = None
    custom_elements_to_remove: Optional[List[str]] = None
    grace_period_seconds: float = 2.0
    max_length: Optional[int] = None
    user_agent: Optional[str] = None
    wait_for_network_idle: bool = True
    click_selector: Optional[str] = None
    custom_timeout: Optional[int] = None  # For backward compatibility

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.url or not self.url.strip():
            raise ValueError("URL is required and cannot be empty")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.grace_period_seconds <= 0:
            raise ValueError("grace_period_seconds must be positive")
        if self.max_length is not None and self.max_length <= 0:
            raise ValueError("max_length must be positive")

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

    def has_click_selector(self) -> bool:
        """Check if a click selector is provided and not empty."""
        return bool(self.click_selector and self.click_selector.strip())
