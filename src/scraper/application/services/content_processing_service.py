"""Content Processing Service for handling HTML content extraction and formatting.

This service implements the Single Responsibility Principle by focusing solely on
content processing tasks, extracted from the large extract_text_from_url function.
"""

from typing import Optional, Tuple

from bs4 import BeautifulSoup

from src.config import DEFAULT_MIN_CONTENT_LENGTH, DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP
from src.logger import Logger
from src.output_format_handler import (
    OutputFormat,
    to_markdown,
    to_text,
    truncate_content,
)
from src.scraper.infrastructure.external.html_utils import _extract_and_clean_html
from src.scraper.infrastructure.web_scraping.rate_limiting import get_domain_from_url

logger = Logger(__name__)


class ContentProcessingService:
    """
    Service responsible for processing HTML content and formatting output.

    Responsibilities:
    - Extract and clean HTML content
    - Validate content length
    - Format content to different output types
    - Handle content processing errors

    This follows SRP by focusing only on content processing concerns.
    """

    def __init__(self, chunked_processor=None):
        """
        Initialize the content processing service.

        Args:
            chunked_processor: Optional chunked HTML processor for large documents
        """
        self.chunked_processor = chunked_processor

    def process_html(
        self, html_content: str, elements_to_remove: list, url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Process HTML content and extract title, clean HTML, and text content.

        Args:
            html_content: Raw HTML string from the page
            elements_to_remove: Tags to strip from the HTML before parsing
            url: Source URL, used for logging

        Returns:
            Tuple of (title, clean_html, text_content, error)
            Error is None when extraction succeeds
        """
        try:
            # Use chunked processor if available
            if self.chunked_processor:
                page_title, clean_html, text_content, error, soup = (
                    self.chunked_processor.extract_clean_html_optimized(
                        html_content, elements_to_remove, url
                    )
                )

                if error:
                    return None, None, None, error

                if not clean_html and not text_content:
                    logger.warning(f"Could not find body tag for {url}")
                    return None, None, None, "[ERROR] Could not find body tag in HTML."

                return page_title, clean_html, text_content, None

            # Fallback to direct processing if no chunked processor
            return self._process_html_fallback(html_content, elements_to_remove, url)

        except Exception as e:
            # Fallback to original method if chunked processing fails
            logger.warning(
                f"Chunked processing failed for {url}, falling back to original method: {e}"
            )

            try:
                return self._process_html_fallback(
                    html_content, elements_to_remove, url
                )
            except Exception as fallback_error:
                logger.error(
                    f"Both chunked and original processing failed for {url}: {fallback_error}"
                )
                return (
                    None,
                    None,
                    None,
                    f"[ERROR] HTML processing failed: {str(fallback_error)}",
                )

    def _process_html_fallback(
        self, html_content: str, elements_to_remove: list, url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Fallback HTML processing method using BeautifulSoup directly.

        Args:
            html_content: Raw HTML string
            elements_to_remove: Tags to remove
            url: Source URL for logging

        Returns:
            Tuple of (title, clean_html, text_content, error)
        """
        soup, target_element = _extract_and_clean_html(html_content, elements_to_remove)

        if not target_element:
            logger.warning(f"Could not find body tag for {url}")
            return None, None, None, "[ERROR] Could not find body tag in HTML."

        page_title = (
            soup.title.string.strip() if soup.title and soup.title.string else ""
        )
        clean_html = str(target_element)
        text_content = target_element.get_text(separator="\n", strip=True)

        return page_title, clean_html, text_content, None

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
        Format content according to the requested output format.

        Args:
            title: Page title
            html_content: Clean HTML content
            text_content: Plain text content
            output_format: Desired output format
            max_length: Optional maximum length for truncation

        Returns:
            Formatted content string
        """
        if output_format is OutputFormat.TEXT:
            # Create soup for text formatting
            soup = BeautifulSoup(html_content, "html.parser")
            formatted = to_text(soup=soup)
        elif output_format is OutputFormat.HTML:
            # Return clean HTML, preferring body content if available
            soup = BeautifulSoup(html_content, "html.parser")
            if soup and soup.body:
                # Return only the inner content of the body tag
                formatted = "".join(str(child) for child in soup.body.children)
            else:
                formatted = html_content
        else:  # Default to Markdown
            formatted = to_markdown(html_content)

        # Apply truncation if max_length is specified
        if max_length is not None:
            formatted = truncate_content(formatted, max_length)

        return formatted
