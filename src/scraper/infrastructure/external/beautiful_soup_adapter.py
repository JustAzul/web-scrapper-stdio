"""
BeautifulSoupAdapter - Concrete implementation of IHTMLParser using BeautifulSoup

This adapter implements the IHTMLParser interface using BeautifulSoup4,
following the Adapter pattern and Dependency Inversion Principle.
"""

from typing import Any, List

from bs4 import BeautifulSoup

from src.scraper.application.contracts.html_parser import IHTMLParser


class BeautifulSoupAdapter(IHTMLParser):
    """
    Adapter that implements IHTMLParser using BeautifulSoup4.

    This class adapts the BeautifulSoup library to conform to our
    IHTMLParser interface, allowing it to be injected into services
    that depend on the abstraction rather than the concrete implementation.

    Benefits:
    - Follows Dependency Inversion Principle
    - Allows easy swapping of HTML parsers
    - Enables better testing through mocking
    - Isolates BeautifulSoup dependency
    """

    def __init__(self, parser: str = "html.parser"):
        """
        Initialize the BeautifulSoup adapter.

        Args:
            parser: BeautifulSoup parser to use (default: "html.parser")
        """
        self.parser = parser

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.

        Args:
            html_content: Raw HTML string to parse

        Returns:
            BeautifulSoup object representing the parsed HTML
        """
        return BeautifulSoup(html_content, self.parser)

    def extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the title from parsed HTML using BeautifulSoup.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title string, empty string if no title found
        """
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return ""

    def extract_text(self, element: Any) -> str:
        """
        Extract plain text content from an HTML element using BeautifulSoup.

        Args:
            element: BeautifulSoup element to extract text from

        Returns:
            Plain text content with proper formatting
        """
        if element is None:
            return ""

        # Use BeautifulSoup's get_text method with proper formatting
        return element.get_text(separator="\n", strip=True)

    def remove_elements(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> BeautifulSoup:
        """
        Remove specified HTML elements from the parsed structure.

        Args:
            soup: BeautifulSoup object
            elements_to_remove: List of element tag names to remove

        Returns:
            Modified BeautifulSoup object with elements removed
        """
        # Create a copy to avoid modifying the original
        soup_copy = BeautifulSoup(str(soup), self.parser)

        # Remove each specified element type
        for element_name in elements_to_remove:
            for element in soup_copy.find_all(element_name):
                element.decompose()  # Remove element and free memory

        return soup_copy
