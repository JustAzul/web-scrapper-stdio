"""
This module contains the URLValidator service, which is responsible for
validating and normalizing URLs.
"""

from urllib.parse import urlparse, urlunparse


class URLValidator:
    """
    A service dedicated to validating and normalizing URLs to ensure they are
    well-formed and safe for scraping.
    """

    def __init__(self):
        """Initializes the URLValidator."""
        pass

    def validate(self, url: str) -> bool:
        """
        Validates if the given string is a valid HTTP/HTTPS URL.

        Args:
            url: The URL string to validate.

        Returns:
            True if the URL is valid, False otherwise.
        """
        if not url:
            return False
        try:
            result = urlparse(url)
            # A simple check for scheme and netloc
            return result.scheme in ["http", "https"] and bool(result.netloc)
        except (ValueError, AttributeError):
            return False

    def normalize(self, url: str) -> str:
        """Normalizes a URL by adding a default scheme if missing."""
        if "://" not in url:
            url = f"https://{url}"
        parsed = urlparse(url)
        # Rebuild the URL to ensure consistent formatting
        return urlunparse(parsed)
