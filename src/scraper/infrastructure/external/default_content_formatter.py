"""
DefaultContentFormatter - Concrete implementation of IContentFormatter

This adapter implements the IContentFormatter interface using existing output formatters,
following the Adapter pattern and Dependency Inversion Principle.
"""

from typing import Optional

from bs4 import BeautifulSoup

from src.output_format_handler import to_markdown, to_text, truncate_content
from src.scraper.application.contracts.content_formatter import IContentFormatter


class DefaultContentFormatter(IContentFormatter):
    """
    Default implementation of IContentFormatter interface.

    This class provides concrete implementation of content formatting operations
    using existing output format handlers, allowing it to be injected into services
    that depend on the abstraction.

    Benefits:
    - Follows Dependency Inversion Principle
    - Allows easy swapping of formatting strategies
    - Enables better testing through mocking
    - Reuses existing proven format handlers
    """

    def __init__(self):
        """Initialize the default content formatter."""
        pass

    def format_to_markdown(self, html_content: str) -> str:
        """
        Format HTML content to Markdown using existing formatter.

        Args:
            html_content: HTML string to format

        Returns:
            Markdown formatted string
        """
        return to_markdown(html_content)

    def format_to_text(self, html_content: str) -> str:
        """
        Format HTML content to plain text using existing formatter.

        Args:
            html_content: HTML string to format

        Returns:
            Plain text formatted string
        """
        # Create soup for text formatting
        soup = BeautifulSoup(html_content, "html.parser")
        return to_text(soup=soup)

    def format_to_html(self, html_content: str) -> str:
        """
        Format HTML content to clean HTML.

        Args:
            html_content: HTML string to format

        Returns:
            Clean HTML formatted string
        """
        # Parse and clean the HTML
        soup = BeautifulSoup(html_content, "html.parser")

        if soup and soup.body:
            # Return only the inner content of the body tag
            return "".join(str(child) for child in soup.body.children)
        else:
            # Return the content as-is if no body tag
            return html_content

    def truncate_content(self, content: str, max_length: Optional[int]) -> str:
        """
        Truncate content to specified maximum length using existing utility.

        Args:
            content: Content string to truncate
            max_length: Maximum length allowed, None for no truncation

        Returns:
            Truncated content string
        """
        if max_length is None:
            return content

        return truncate_content(content, max_length)
