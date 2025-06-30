"""
URLConfig - Single Responsibility: URL validation and normalization

Extracted from ScrapingConfig to follow SRP principle.
This class is responsible only for URL-related operations.
"""

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class URLConfig:
    """
    Configuration for URL validation and normalization.

    Single Responsibility: Handles all URL-related validation and processing.
    """

    url: str

    def __post_init__(self):
        """Validate URL after initialization."""
        if not self.url:
            raise ValueError("URL is required")

        parsed = urlparse(self.url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

    @property
    def normalized_url(self) -> str:
        """Get normalized URL (lowercase domain)."""
        parsed = urlparse(self.url)
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

        if parsed.path:
            normalized += parsed.path
        if parsed.params:
            normalized += f";{parsed.params}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        if parsed.fragment:
            normalized += f"#{parsed.fragment}"

        return normalized

    @property
    def is_valid(self) -> bool:
        """Check if URL is valid."""
        try:
            parsed = urlparse(self.url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @property
    def domain(self) -> str:
        """Get domain from URL."""
        parsed = urlparse(self.url)
        return parsed.netloc.lower()

    @property
    def scheme(self) -> str:
        """Get scheme from URL."""
        parsed = urlparse(self.url)
        return parsed.scheme.lower()

    def __str__(self) -> str:
        """String representation."""
        return self.normalized_url
