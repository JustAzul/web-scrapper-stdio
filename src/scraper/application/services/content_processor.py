"""
RefactoredContentProcessingService - DIP-compliant content processing service

This service follows the Dependency Inversion Principle by depending on abstractions
(interfaces) rather than concrete implementations, allowing for better testability,
flexibility, and maintainability.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from src.logger import get_logger
from src.output_format_handler import OutputFormat
from src.scraper.application.contracts.content_cleaner import IContentCleaner
from src.scraper.application.contracts.content_formatter import IContentFormatter
from src.scraper.application.contracts.html_parser import IHTMLParser
from src.scraper.infrastructure.web_scraping.rate_limiting import get_domain_from_url
from src.settings import (
    DEFAULT_MIN_CONTENT_LENGTH,
    DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP,
)

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Dataclass for holding the results of HTML processing."""

    title: Optional[str]
    clean_html: Optional[str]
    text_content: Optional[str]


class RefactoredContentProcessingService:
    """
    Refactored content processing service following Dependency Inversion Principle.

    This service depends on abstractions (interfaces)
    rather than concrete implementations, allowing different implementations
    to be injected at runtime.

    Benefits:
    - Follows Dependency Inversion Principle (DIP)
    - Enhanced testability through dependency injection
    - Flexible architecture allowing strategy swapping
    - Better separation of concerns
    - Easier to extend and maintain

    Dependencies (injected via constructor):
    - IHTMLParser: For HTML parsing operations
    - IContentCleaner: For content cleaning operations
    - IContentFormatter: For content formatting operations
    """

    def __init__(
        self,
        html_parser: IHTMLParser,
        content_cleaner: IContentCleaner,
        content_formatter: IContentFormatter,
    ):
        """
        Initialize the refactored content processing service with injected dependencies.

        Args:
            html_parser: Implementation of IHTMLParser interface
            content_cleaner: Implementation of IContentCleaner interface
            content_formatter: Implementation of IContentFormatter interface
        """
        self.html_parser = html_parser
        self.content_cleaner = content_cleaner
        self.content_formatter = content_formatter

    def process_html_content(
        self, html_content: str, elements_to_remove: list, url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Process HTML content using injected dependencies.
        This method is designed to be backward compatible with the return signature
        of the original ContentProcessingService.
        """
        try:
            # Step 1 & 2: Use injected dependencies for processing
            result = self._process_with_dependencies(
                html_content, elements_to_remove, url
            )

            # Step 3: Check if the extracted content is significant
            min_len = self.get_min_content_length(url)
            if not self.validate_content_length(result.text_content, min_len, url):
                return (
                    None,
                    None,
                    None,
                    (
                        f"[ERROR] No significant text content extracted (length < "
                        f"{min_len})."
                    ),
                )

            # Step 4: Return successful result
            return result.title, result.clean_html, result.text_content, None

        except Exception as e:
            logger.error(f"All processing methods failed for {url}: {e}", exc_info=True)
            return (
                None,
                None,
                None,
                f"[ERROR] HTML processing failed: {str(e)}",
            )

    def _process_with_dependencies(
        self, html_content: str, elements_to_remove: list, url: str
    ) -> ProcessingResult:
        """
        Process HTML using injected dependencies.
        """
        # Parse HTML using injected parser
        soup = self.html_parser.parse_html(html_content)

        # Extract title using injected parser
        page_title = self.html_parser.extract_title(soup)

        # Clean HTML using injected cleaner
        clean_html = self.content_cleaner.clean_html(html_content, elements_to_remove)

        text_content = None
        if clean_html:
            # Parse cleaned HTML to extract text
            cleaned_soup = self.html_parser.parse_html(clean_html)
            text_content = self.html_parser.extract_text(cleaned_soup)
        else:
            logger.warning(f"Could not clean HTML for {url}")

        return ProcessingResult(
            title=page_title, clean_html=clean_html, text_content=text_content
        )

    def validate_content_length(
        self, text_content: str, min_length: int, url: str
    ) -> bool:
        """
        Validate content length using injected cleaner.

        Args:
            text_content: Extracted text content
            min_length: Minimum required length
            url: Source URL for logging

        Returns:
            True if content is long enough, False otherwise
        """
        return self.content_cleaner.validate_content_length(
            text_content, min_length, url
        )

    def get_min_content_length(self, url: str) -> int:
        """
        Get the minimum content length based on the domain.

        Args:
            url: Source URL

        Returns:
            Minimum content length threshold
        """
        original_domain = get_domain_from_url(url)

        # Special handling for search.app domains
        if original_domain and "search.app" in original_domain:
            return DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP

        return DEFAULT_MIN_CONTENT_LENGTH

    def format_content(
        self,
        title: str,
        html_content: str,
        text_content: str,
        output_format: OutputFormat,
        max_length: Optional[int] = None,
    ) -> str:
        """
        Format content using injected formatter.

        Args:
            title: Page title
            html_content: Clean HTML content
            text_content: Plain text content
            output_format: Desired output format
            max_length: Optional maximum length for truncation

        Returns:
            Formatted content string
        """
        # Use injected formatter based on output format
        if output_format is OutputFormat.TEXT:
            formatted = self.content_formatter.format_to_text(html_content)
        elif output_format is OutputFormat.HTML:
            formatted = self.content_formatter.format_to_html(html_content)
        else:  # Default to Markdown
            formatted = self.content_formatter.format_to_markdown(html_content)

        # Apply truncation using injected formatter
        if max_length is not None:
            formatted = self.content_formatter.truncate_content(formatted, max_length)

        return formatted
