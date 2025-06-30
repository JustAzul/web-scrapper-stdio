"""
This module contains the URLValidator service, which is responsible for
validating and normalizing URLs.
"""

from pydantic import HttpUrl, ValidationError


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
        try:
            # Pydantic's HttpUrl is sufficient for the current validation rules.
            HttpUrl(url)
            return True
        except ValidationError:
            return False
