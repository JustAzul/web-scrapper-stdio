"""
AsyncHTMLProcessor - Fully async HTML processing implementation

This provides a fully async interface for HTML processing operations,
eliminating any sync/async inconsistencies in the HTML processing system.
Part of T013 - Async/Await Standardization.
"""

import asyncio
from typing import Any, Optional, Tuple

from bs4 import BeautifulSoup

from src.logger import get_logger
from src.scraper.infrastructure.external.html_utils import (
    _extract_and_clean_html,
    _extract_markdown_and_text,
)

logger = get_logger(__name__)


class AsyncHTMLProcessor:
    """
    Fully async HTML processor that provides consistent async interface.

    This class standardizes HTML processing operations to be fully async,
    eliminating the mixed sync/async patterns found in the original
    HTML processing implementation.

    Benefits:
    - Consistent async-only API
    - Better integration with async codebases
    - Proper async resource management
    - No blocking operations for large HTML processing
    """

    def __init__(self, parser: str = "html.parser"):
        """
        Initialize async HTML processor.

        Args:
            parser: BeautifulSoup parser to use
        """
        self.parser = parser
        self.logger = logger

    async def extract_and_clean_html_async(
        self, html_content: str, elements_to_remove: list
    ) -> Tuple[Optional[BeautifulSoup], Optional[Any]]:
        """
        Extract and clean HTML asynchronously.

        For large HTML documents, this runs the processing in a thread pool
        to avoid blocking the event loop.

        Args:
            html_content: Raw HTML content
            elements_to_remove: List of element tags to remove

        Returns:
            Tuple of (soup, target_element)
        """
        # For small HTML (< 100KB), process directly
        if len(html_content) < 100_000:
            return _extract_and_clean_html(html_content, elements_to_remove)

        # For large HTML, use thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, _extract_and_clean_html, html_content, elements_to_remove
        )

        self.logger.debug(
            f"Processed large HTML document ({len(html_content)} chars) asynchronously"
        )
        return result

    async def extract_markdown_and_text_async(self, html_content: str) -> str:
        """
        Extract markdown and text from HTML asynchronously.

        Args:
            html_content: HTML content to process

        Returns:
            Extracted text content
        """
        # Parse HTML
        soup = BeautifulSoup(html_content, self.parser)

        # For large documents, use thread pool
        if len(html_content) > 100_000:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _extract_markdown_and_text, soup)
            self.logger.debug("Extracted text from large HTML document asynchronously")
            return result
        else:
            return _extract_markdown_and_text(soup)

    async def parse_html_async(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content asynchronously.

        Args:
            html_content: HTML content to parse

        Returns:
            BeautifulSoup object
        """
        # For large HTML, use thread pool
        if len(html_content) > 200_000:
            loop = asyncio.get_event_loop()
            soup = await loop.run_in_executor(
                None, BeautifulSoup, html_content, self.parser
            )
            self.logger.debug(
                f"Parsed large HTML document ({len(html_content)} chars) asynchronously"
            )
            return soup
        else:
            return BeautifulSoup(html_content, self.parser)

    async def extract_title_async(self, soup: BeautifulSoup) -> str:
        """
        Extract title from parsed HTML asynchronously.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title string
        """
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return ""

    async def extract_text_async(self, element: Any) -> str:
        """
        Extract plain text from HTML element asynchronously.

        Args:
            element: HTML element to extract text from

        Returns:
            Plain text content
        """
        if element is None:
            return ""

        # For large elements, use thread pool
        element_str = str(element)
        if len(element_str) > 50_000:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: element.get_text(separator="\n", strip=True)
            )
            self.logger.debug("Extracted text from large element asynchronously")
            return result
        else:
            return element.get_text(separator="\n", strip=True)

    async def remove_elements_async(
        self, soup: BeautifulSoup, elements_to_remove: list
    ) -> BeautifulSoup:
        """
        Remove specified elements from HTML asynchronously.

        Args:
            soup: BeautifulSoup object
            elements_to_remove: List of element tag names to remove

        Returns:
            Modified BeautifulSoup object
        """
        # Create a copy to avoid modifying the original
        soup_copy = BeautifulSoup(str(soup), self.parser)

        # For large documents with many elements to remove, use thread pool
        if len(str(soup)) > 100_000 and len(elements_to_remove) > 10:
            loop = asyncio.get_event_loop()

            def remove_elements():
                for element_name in elements_to_remove:
                    for element in soup_copy.find_all(element_name):
                        element.decompose()
                return soup_copy

            result = await loop.run_in_executor(None, remove_elements)
            self.logger.debug(
                f"Removed {len(elements_to_remove)} element types asynchronously"
            )
            return result
        else:
            # Remove each specified element type
            for element_name in elements_to_remove:
                for element in soup_copy.find_all(element_name):
                    element.decompose()
            return soup_copy

    async def process_html_pipeline_async(
        self, html_content: str, elements_to_remove: list
    ) -> Tuple[str, str, str]:
        """
        Process HTML through complete async pipeline.

        Args:
            html_content: Raw HTML content
            elements_to_remove: Elements to remove

        Returns:
            Tuple of (title, clean_html, text_content)
        """
        # Parse HTML
        soup = await self.parse_html_async(html_content)

        # Extract title
        title = await self.extract_title_async(soup)

        # Clean HTML
        soup, target_element = await self.extract_and_clean_html_async(
            html_content, elements_to_remove
        )

        clean_html = str(target_element) if target_element else str(soup)

        # Extract text
        text_content = await self.extract_text_async(target_element or soup)

        return title, clean_html, text_content

    async def cleanup(self) -> None:
        """
        Cleanup HTML processor resources.

        Currently no resources to cleanup, but provided for consistency.
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the async HTML processor."""
        return f"AsyncHTMLProcessor(parser={self.parser})"
