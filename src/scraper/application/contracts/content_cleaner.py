"""
IContentCleaner Interface - Abstract interface for content cleaning operations

This interface follows the Dependency Inversion Principle (DIP) by providing
an abstraction for content cleaning operations, allowing different implementations
to be injected without changing the dependent code.
"""

from abc import ABC, abstractmethod
from typing import List


class IContentCleaner(ABC):
    """
    Abstract interface for content cleaning operations.

    This interface defines the contract for HTML content cleaning functionality,
    allowing different cleaning strategies to be used interchangeably.

    Following DIP: High-level modules should not depend on low-level modules.
    Both should depend on abstractions.
    """

    @abstractmethod
    def clean_html(self, html_content: str, elements_to_remove: List[str]) -> str:
        """
        Clean HTML content by removing unwanted elements.

        Args:
            html_content: Raw HTML string to clean
            elements_to_remove: List of element tag names to remove

        Returns:
            Cleaned HTML string
        """
        pass

    @abstractmethod
    def extract_main_content(self, html_content: str) -> str:
        """
        Extract the main content area from HTML.

        Args:
            html_content: Raw HTML string

        Returns:
            Main content HTML string
        """
        pass

    @abstractmethod
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
        pass
