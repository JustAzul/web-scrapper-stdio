"""
IContentFormatter Interface - Abstract interface for content formatting operations

This interface follows the Dependency Inversion Principle (DIP) by providing
an abstraction for content formatting operations, allowing different implementations
to be injected without changing the dependent code.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IContentFormatter(ABC):
    """
    Abstract interface for content formatting operations.

    This interface defines the contract for content formatting functionality,
    allowing different formatting strategies to be used interchangeably.

    Following DIP: High-level modules should not depend on low-level modules.
    Both should depend on abstractions.
    """

    @abstractmethod
    def format_to_markdown(self, html_content: str) -> str:
        """
        Format HTML content to Markdown.

        Args:
            html_content: HTML string to format

        Returns:
            Markdown formatted string
        """
        pass

    @abstractmethod
    def format_to_text(self, html_content: str) -> str:
        """
        Format HTML content to plain text.

        Args:
            html_content: HTML string to format

        Returns:
            Plain text formatted string
        """
        pass

    @abstractmethod
    def format_to_html(self, html_content: str) -> str:
        """
        Format HTML content to clean HTML.

        Args:
            html_content: HTML string to format

        Returns:
            Clean HTML formatted string
        """
        pass

    @abstractmethod
    def truncate_content(self, content: str, max_length: Optional[int]) -> str:
        """
        Truncate content to specified maximum length.

        Args:
            content: Content string to truncate
            max_length: Maximum length allowed, None for no truncation

        Returns:
            Truncated content string
        """
        pass
