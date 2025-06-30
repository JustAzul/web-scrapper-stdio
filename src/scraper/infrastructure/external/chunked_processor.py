"""
Chunked HTML Processor

This module processes large HTML documents in chunks to avoid memory issues
and improve performance. It includes intelligent fallback mechanisms and
comprehensive error handling.
"""

import gc
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from src.core.constants import (
    BYTES_PER_MB,
    CONTENT_AREA_PATTERNS,
    DEFAULT_CHUNK_NODE_LIMIT,
    DEFAULT_CHUNK_SIZE_THRESHOLD,
    MEMORY_THRESHOLD_MULTIPLIER,
    NOISE_SELECTORS,
)
from src.logger import Logger

from ..monitoring.memory_monitor import MemoryLimitExceededError, MemoryMonitor
from ..monitoring.processing_metrics import ProcessingMetrics
from .html_utils import _extract_and_clean_html, remove_elements

logger = Logger(__name__)


class ChunkedHTMLProcessor:
    """
    Memory-efficient HTML processor that handles large documents through chunked processing
    while maintaining complete backward compatibility.

    This class now follows Single Responsibility Principle by delegating:
    - Memory monitoring to MemoryMonitor
    - Metrics tracking to ProcessingMetrics
    """

    def __init__(
        self,
        chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
        memory_limit_mb: int = 150,
        enable_chunking: bool = True,
        fallback_enabled: bool = True,
        parser: str = "html.parser",
        extra_noise_cleanup: bool = False,
    ):
        """
        Initialize the chunked HTML processor.

        Args:
            chunk_size_threshold: HTML size threshold to trigger chunked processing
            memory_limit_mb: Memory limit in MB for processing
            enable_chunking: Whether to enable chunked processing
            fallback_enabled: Whether to fallback to original method on errors
            parser: Parser to use for processing
            extra_noise_cleanup: Whether to perform extra noise cleanup
        """
        self.chunk_size_threshold = chunk_size_threshold
        self.enable_chunking = enable_chunking
        self.fallback_enabled = fallback_enabled
        self.parser = parser  # unify parser choice across processors
        self.extra_noise_cleanup = extra_noise_cleanup

        # Dependency injection for SOLID compliance
        self.memory_monitor = MemoryMonitor(
            memory_limit_mb=memory_limit_mb, enabled=True
        )
        self.metrics = ProcessingMetrics(enabled=True)

        # Elements that typically contain unwanted content
        self.noise_selectors = NOISE_SELECTORS

    def extract_content(
        self, html_content: str, elements_to_remove: List[str], url: str
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """
        Extract content from HTML using either chunked or original processing.

        Returns:
            Tuple of (title, clean_html, text_content, error, soup)
        """
        start_time = self.metrics.start_processing()
        content_size_mb = len(html_content.encode("utf-8")) / BYTES_PER_MB

        try:
            # Handle empty HTML - not an error condition, just return empty strings
            if not html_content or not html_content.strip():
                return "", "", "", None, None

            # Always parse the HTML to get basic structure and title
            soup = BeautifulSoup(html_content, self.parser)

            # Extract title first (works even without body)
            page_title = (
                soup.title.string.strip() if soup.title and soup.title.string else ""
            )

            # Check if we should use chunked processing
            use_chunked = self._should_use_chunked_processing(html_content)

            if use_chunked:
                logger.debug(
                    f"Using chunked processing for {url} (size: {content_size_mb:.2f}MB)"
                )
                try:
                    title, clean_html, text_content, error, soup = (
                        self._extract_content_chunked(soup, elements_to_remove, url)
                    )
                except Exception as chunked_error:
                    logger.warning(
                        f"Chunked processing failed, falling back to original method: {chunked_error}"
                    )
                    if self.fallback_enabled:
                        # Use fallback but mark that chunked processing was attempted but failed
                        title, clean_html, text_content, error, soup = (
                            self._extract_content_original(
                                soup, elements_to_remove, url
                            )
                        )
                        use_chunked = (
                            False  # Update flag to reflect that fallback was used
                        )
                    else:
                        raise
            else:
                logger.debug(
                    f"Using original processing for {url} (size: {content_size_mb:.2f}MB)"
                )
                title, clean_html, text_content, error, soup = (
                    self._extract_content_original(soup, elements_to_remove, url)
                )

            # Ensure title is preserved even if body processing fails
            if title is None:
                title = page_title

            # Record successful processing metrics
            self.metrics.record_processing_success(
                start_time=start_time,
                content_size_mb=content_size_mb,
                used_chunked_processing=use_chunked,
                memory_peak_mb=self.memory_monitor.get_memory_usage(),
                chunks_processed=getattr(self, "_chunks_processed", 0),
            )

            logger.debug(
                f"Content extraction completed for {url} in {time.time() - start_time:.2f}s"
            )
            return title or "", clean_html or "", text_content or "", error, soup

        except Exception as e:
            error_msg = f"Content extraction failed: {str(e)}"
            logger.error(f"Error processing {url}: {error_msg}")

            # Record error metrics
            self.metrics.record_processing_error(
                start_time=start_time,
                content_size_mb=content_size_mb,
                error_message=error_msg,
            )

            return "", "", "", error_msg, None

    def _should_use_chunked_processing(self, html_content: str) -> bool:
        """Determine if chunked processing should be used."""
        if not self.enable_chunking:
            return False

        return len(html_content) > self.chunk_size_threshold

    def _extract_content_chunked(
        self, soup: BeautifulSoup, elements_to_remove: List[str], url: str
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """
        Process content using chunked processing for better memory efficiency.
        This simplified version maintains output consistency with original processing.
        """
        try:
            # Convert soup back to HTML string for consistent behavior with original method
            html_content = str(soup)
            new_soup = BeautifulSoup(html_content, self.parser)

            # Extract title first
            title = ""
            if new_soup.title and new_soup.title.string:
                title = new_soup.title.string.strip()

            # Remove unwanted elements using shared helper
            remove_elements(new_soup, elements_to_remove)

            # Get the body tag as target element (same as original)
            target_element = new_soup.body
            if not target_element:
                # If no body tag, use entire soup
                target_element = new_soup

            # For memory efficiency, process large elements in chunks but maintain output structure
            self._chunks_processed = 0

            # If content is very large, process it in chunks for memory efficiency
            if len(str(target_element)) > self.chunk_size_threshold:
                self._process_large_content_in_chunks(target_element)
                self._chunks_processed += 1

            # Extract final content with proper text normalization (matching html_utils)
            clean_html = str(target_element)
            text_content = target_element.get_text(separator="\n", strip=True)
            # Apply the same text normalization as original html_utils
            text_content = re.sub(r"\n\s*\n", "\n\n", text_content).strip()

            # Memory cleanup
            gc.collect()

            return title or "", clean_html or "", text_content or "", None, new_soup

        except Exception as e:
            logger.error(f"Chunked processing failed: {e}")
            raise  # Re-raise to trigger fallback

    def _process_large_content_in_chunks(self, element: Tag) -> None:
        """
        Process large content in smaller chunks for memory efficiency.
        This method processes content in-place without changing the structure.
        """
        # Iterative (stack-based) traversal to prevent RecursionError
        stack = [list(element.children)]  # list of pending child iterables
        chunk_accumulator: List[Tag] = []
        chunk_bytes: int = 0
        CHUNK_NODE_LIMIT = DEFAULT_CHUNK_NODE_LIMIT

        while stack:
            # Use memory monitor to check limits
            try:
                self.memory_monitor.check_memory_limit(
                    threshold_multiplier=MEMORY_THRESHOLD_MULTIPLIER
                )
            except MemoryLimitExceededError as e:
                logger.warning(f"Memory limit exceeded during chunk processing: {e}")
                raise

            current_children = stack.pop()
            while current_children:
                child = current_children.pop(0)
                if isinstance(child, Tag):
                    size = len(str(child))
                    if size > self.chunk_size_threshold:
                        # Push grandchildren onto stack for further processing
                        stack.append(list(child.children))
                    chunk_accumulator.append(child)
                    chunk_bytes += size

                    if (
                        len(chunk_accumulator) >= CHUNK_NODE_LIMIT
                        or chunk_bytes > self.chunk_size_threshold
                    ):
                        # Flush current chunk (no-op here but placeholder for future optimization)
                        chunk_accumulator.clear()
                        chunk_bytes = 0
                        gc.collect()

    def _extract_content_original(
        self, soup: BeautifulSoup, elements_to_remove: List[str], url: str
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """
        Use the original extraction method for backward compatibility.
        """
        try:
            # Convert soup back to HTML string for original function
            html_content = str(soup)
            soup_orig, target_element = _extract_and_clean_html(
                html_content, elements_to_remove
            )

            # Extract title (preserve from original soup if available)
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup_orig and soup_orig.title and soup_orig.title.string:
                title = soup_orig.title.string.strip()

            # Handle case where no body/target element found
            if not target_element:
                # Try to use the entire soup as content if no specific target
                text_content = (
                    soup_orig.get_text(separator="\n", strip=True) if soup_orig else ""
                )
                clean_html = str(soup_orig) if soup_orig else ""

                if text_content and clean_html:
                    return title or "", clean_html, text_content, None, soup_orig
                else:
                    # Return title but indicate body tag issue
                    if title:
                        return (
                            title,
                            "",
                            "",
                            "[ERROR] Could not find body tag in HTML.",
                            soup_orig,
                        )
                    else:
                        return (
                            "",
                            "",
                            "",
                            "[ERROR] Could not find body tag in HTML.",
                            soup_orig,
                        )

            # Extract clean HTML and text from target element
            clean_html = str(target_element)
            text_content = target_element.get_text(separator="\n", strip=True)
            # Apply the same text normalization as original html_utils
            text_content = re.sub(r"\n\s*\n", "\n\n", text_content).strip()

            return title or "", clean_html or "", text_content or "", None, soup_orig

        except Exception as e:
            logger.error(f"Original processing failed: {e}")
            # Return any title we managed to extract
            if title:
                return title, "", "", f"Original processing failed: {str(e)}", None
            else:
                return "", "", "", f"Original processing failed: {str(e)}", None

    def _remove_unwanted_elements(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> None:
        """Proxy to :func:`html_utils.remove_elements` (deprecated)."""
        remove_elements(soup, elements_to_remove)
        if self.extra_noise_cleanup:
            remove_elements(soup, self.noise_selectors)

    def _identify_content_areas(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Identify main content areas in the HTML document.
        Returns a list of BeautifulSoup Tag objects representing content areas.
        """
        content_areas = []

        # First, look for semantic main content elements
        main_elements = soup.find_all(["main", "article"])
        if main_elements:
            content_areas.extend(main_elements)

        # Look for content areas by class/id patterns
        content_patterns = CONTENT_AREA_PATTERNS

        for pattern in content_patterns:
            # Search by class
            elements = soup.find_all(class_=lambda x: x and pattern in x.lower())
            content_areas.extend(elements)

            # Search by id
            elements = soup.find_all(id=lambda x: x and pattern in x.lower())
            content_areas.extend(elements)

        # If no content areas found, use body or entire soup
        if not content_areas:
            if soup.body:
                content_areas.append(soup.body)
            else:
                content_areas.append(soup)

        # Remove duplicates while preserving order
        seen = set()
        unique_areas = []
        for area in content_areas:
            if area not in seen:
                seen.add(area)
                unique_areas.append(area)

        return unique_areas

    def _process_area_in_chunks(self, area: Tag) -> Tuple[List[str], List[str]]:
        """
        Process a content area in chunks to manage memory usage.
        Returns lists of text and HTML chunks.
        """
        text_chunks = []
        html_chunks = []
        current_chunk_size = 0
        current_chunk_elements = []

        def process_current_chunk():
            if current_chunk_elements:
                # Create a new soup for the chunk
                chunk_soup = BeautifulSoup("<div></div>", self.parser)
                chunk_div = chunk_soup.div

                # Add all elements to the chunk
                for element in current_chunk_elements:
                    # Create a copy to avoid modifying original
                    element_copy = BeautifulSoup(str(element), self.parser).contents[0]
                    chunk_div.append(element_copy)

                # Extract text and HTML
                text_chunks.append(chunk_div.get_text(separator="\n", strip=True))
                html_chunks.append(str(chunk_div))

                # Clear the current chunk
                current_chunk_elements.clear()
                nonlocal current_chunk_size
                current_chunk_size = 0

                # Force garbage collection
                gc.collect()

        # Process each direct child of the area
        for element in area.children:
            if isinstance(element, Tag):
                element_size = len(str(element))

                # If adding this element would exceed chunk size, process current chunk
                if current_chunk_size + element_size > self.chunk_size_threshold:
                    process_current_chunk()

                # Add element to current chunk
                current_chunk_elements.append(element)
                current_chunk_size += element_size

                # Monitor memory usage
                try:
                    self.memory_monitor.check_memory_limit()
                    process_current_chunk()
                except MemoryLimitExceededError:
                    process_current_chunk()

        # Process any remaining elements
        if current_chunk_elements:
            process_current_chunk()

        return text_chunks, html_chunks

    def get_last_processing_metrics(self) -> Dict[str, Any]:
        """Get metrics from the last processing operation."""
        return self.metrics.get_last_metrics()

    # ---------------------------------------------------------------------
    # Async convenience wrapper
    # ---------------------------------------------------------------------
    async def extract_content_async(
        self, html_content: str, elements_to_remove: List[str], url: str
    ):
        """Asynchronously extract content without blocking the event loop.

        For most HTML processing operations, the overhead of thread pool execution
        outweighs the benefits. This method provides async compatibility while
        running the operation directly.
        """
        # For most web scraping use cases, HTML processing is I/O bound rather than CPU bound
        # Running directly is more efficient than thread pool overhead
        return self.extract_content(html_content, elements_to_remove, url)


def extract_clean_html_optimized(
    html_content: str, elements_to_remove: List[str], url: str, **processor_kwargs
) -> Tuple[str, str, str, Optional[str], Optional[BeautifulSoup]]:
    """
    REFATORADO T005: Agora usa CentralizedHTMLExtractor para eliminar duplicação
    Mantém compatibilidade com interface otimizada
    """
    # REFATORAÇÃO: Usar implementação centralizada
    from ...domain.value_objects.extraction_config import ExtractionConfig
    from ..web_scraping.centralized_html_extractor import (
        get_centralized_extractor,
    )

    # Mapear processor_kwargs para ExtractionConfig
    config = ExtractionConfig(
        elements_to_remove=elements_to_remove,
        use_chunked_processing=processor_kwargs.get("enable_chunking", True),
        memory_limit_mb=processor_kwargs.get("memory_limit_mb", 150),
        chunk_size_threshold=processor_kwargs.get("chunk_size_threshold", 100 * 1024),
        parser=processor_kwargs.get("parser", "html.parser"),
        enable_fallback=processor_kwargs.get("fallback_enabled", True),
        extra_noise_cleanup=processor_kwargs.get("extra_noise_cleanup", False),
    )

    # Usar extrator centralizado
    extractor = get_centralized_extractor()
    return extractor.extract_clean_html(html_content, url, config)


def create_chunked_processor(
    enable_chunking: bool = True,
    chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
    memory_limit_mb: int = 150,
) -> ChunkedHTMLProcessor:
    """
    Factory function to create a ChunkedHTMLProcessor with common configurations.

    Args:
        enable_chunking: Whether to enable chunked processing
        chunk_size_threshold: Size threshold for triggering chunked processing
        memory_limit_mb: Memory limit in megabytes

    Returns:
        Configured ChunkedHTMLProcessor instance
    """
    return ChunkedHTMLProcessor(
        enable_chunking=enable_chunking,
        chunk_size_threshold=chunk_size_threshold,
        memory_limit_mb=memory_limit_mb,
    )
