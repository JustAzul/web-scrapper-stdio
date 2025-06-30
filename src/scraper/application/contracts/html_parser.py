"""
IHTMLParser Interface - Abstract interface for HTML parsing

This interface follows the Dependency Inversion Principle (DIP) by providing
an abstraction for HTML parsing operations, allowing different implementations
to be injected without changing the dependent code.
"""

from abc import ABC, abstractmethod
from typing import Any, List

from bs4 import BeautifulSoup


class IHTMLParser(ABC):
    """
    Abstract interface for HTML parsing operations.

    This interface defines the contract for HTML parsing functionality,
    allowing different HTML parsers to be used interchangeably.

    Following DIP: High-level modules should not depend on low-level modules.
    Both should depend on abstractions.
    """

    @abstractmethod
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content into a structured format.

        Args:
            html_content: Raw HTML string to parse

        Returns:
            Parsed HTML structure (BeautifulSoup object)
        """
        pass

    @abstractmethod
    def extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the title from parsed HTML.

        Args:
            soup: Parsed HTML structure

        Returns:
            Page title string, empty string if no title found
        """
        pass

    @abstractmethod
    def extract_text(self, element: Any) -> str:
        """
        Extract plain text content from an HTML element.

        Args:
            element: HTML element to extract text from

        Returns:
            Plain text content with proper formatting
        """
        pass

    @abstractmethod
    def remove_elements(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> BeautifulSoup:
        """
        Remove specified HTML elements from the parsed structure.

        Args:
            soup: Parsed HTML structure
            elements_to_remove: List of element tag names to remove

        Returns:
            Modified HTML structure with elements removed
        """
        pass
