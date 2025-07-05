"""
DefaultContentCleaner - Concrete implementation of IContentCleaner

This adapter implements the IContentCleaner interface using existing HTML utilities,
following the Adapter pattern and Dependency Inversion Principle.
"""

from typing import List

from bs4 import BeautifulSoup

from src.logger import get_logger
from src.scraper.application.contracts.content_cleaner import IContentCleaner
from src.scraper.infrastructure.external.html_utils import _extract_and_clean_html

logger = get_logger(__name__)


class DefaultContentCleaner(IContentCleaner):
    """
    Default implementation of IContentCleaner interface.

    This class provides concrete implementation of content cleaning operations
    using existing HTML utilities and BeautifulSoup, allowing it to be injected
    into services that depend on the abstraction.

    Benefits:
    - Follows Dependency Inversion Principle
    - Allows easy swapping of cleaning strategies
    - Enables better testing through mocking
    - Reuses existing proven HTML utilities
    """

    def __init__(self):
        """Initialize the default content cleaner."""
        pass

    def clean_html(self, html_content: str, elements_to_remove: List[str]) -> str:
        """
        Clean HTML content by removing unwanted elements.

        Args:
            html_content: Raw HTML string to clean
            elements_to_remove: List of element tag names to remove

        Returns:
            Cleaned HTML string
        """
        try:
            # Use existing HTML utilities for cleaning
            soup, target_element = _extract_and_clean_html(
                html_content, elements_to_remove
            )

            if target_element:
                return str(target_element)
            else:
                # If no target element found, return cleaned full HTML
                return str(soup) if soup else html_content

        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return html_content  # Return original on error

    def extract_main_content(self, html_content: str) -> str:
        """
        Extract the main content area from HTML.

        Args:
            html_content: Raw HTML string

        Returns:
            Main content HTML string
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Priority order for main content extraction
            content_selectors = [
                "main",  # HTML5 main element
                "article",  # HTML5 article element
                '[role="main"]',  # ARIA main role
                ".main-content",  # Common class name
                "#main-content",  # Common ID
                ".content",  # Generic content class
                "#content",  # Generic content ID
                "body",  # Fallback to body
            ]

            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    return str(element)

            # Final fallback - return the entire HTML
            return html_content

        except Exception as e:
            logger.warning(f"Error extracting main content: {e}")
            return html_content  # Return original on error

    def validate_content_length(
        self, text_content: str, min_length: int, url: str
    ) -> bool:
        """
        Validate that content meets minimum length requirements.

        Args:
            text_content: Extracted text content
            min_length: Minimum required length
            url: Source URL for logging

        Returns:
            True if content is long enough, False otherwise
        """
        if not text_content or len(text_content) < min_length:
            logger.warning(
                f"No significant text content extracted (length < {min_length}) at {url}"
            )
            return False
        return True
