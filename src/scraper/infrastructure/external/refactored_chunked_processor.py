"""
DEPRECATED: This module is part of a legacy system and is no longer recommended for use.
It will be removed in a future version. Please use dependency-injected services instead.

RefactoredChunkedHTMLProcessor - Orchestration of refactored responsibilities
Part of refactoring T002 - Break up ChunkedHTMLProcessor following SRP
"""

import time
from logging import Logger
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from src.core.constants import BYTES_PER_MB, DEFAULT_CHUNK_SIZE_THRESHOLD
from src.logger import get_logger

from .chunking_strategy import ChunkingStrategy
from .content_processor import ContentProcessor
from .fallback_handler import FallbackHandler
from .memory_monitor import MemoryMonitor
from .processing_metrics import ProcessingMetrics


class RefactoredChunkedHTMLProcessor:
    def __init__(
        self,
        parser: str = "lxml",
        extra_noise_cleanup: bool = False,
        memory_limit_mb: int = 150,
        enable_chunking: bool = True,
        chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
        fallback_enabled: bool = True,
        memory_monitor: Optional[MemoryMonitor] = None,
        metrics: Optional[ProcessingMetrics] = None,
        chunking_strategy: Optional[ChunkingStrategy] = None,
        content_processor: Optional[ContentProcessor] = None,
        fallback_handler: Optional[FallbackHandler] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initializes the processor with dependency injection.
        Args:
            parser: HTML parser to use.
            extra_noise_cleanup: Whether to perform extra noise cleanup.
            memory_limit_mb: Memory limit in MB.
            enable_chunking: Whether to enable chunking.
            chunk_size_threshold: Threshold to use chunking.
            fallback_enabled: Whether to enable fallback handler.
            memory_monitor: Injected memory monitor.
            metrics: Injected metrics collector.
            chunking_strategy: Injected chunking strategy.
            content_processor: Injected content processor.
            fallback_handler: Injected fallback handler.
            logger: Injected logger.
        """
        # Basic settings
        self.parser = parser
        self.extra_noise_cleanup = extra_noise_cleanup

        # Dependency Injection - allows mocking for tests
        self.memory_monitor = memory_monitor or MemoryMonitor(
            memory_limit_mb=memory_limit_mb, enabled=True
        )
        self.metrics = metrics or ProcessingMetrics(enabled=True)
        self.chunking_strategy = chunking_strategy or ChunkingStrategy(
            chunk_size_threshold=chunk_size_threshold, enable_chunking=enable_chunking
        )
        self.content_processor = content_processor or ContentProcessor(
            parser=parser, extra_noise_cleanup=extra_noise_cleanup
        )
        self.fallback_handler = fallback_handler or FallbackHandler(
            enabled=fallback_enabled
        )

        # For compatibility with original interface
        self.enable_chunking = enable_chunking
        self.fallback_enabled = fallback_enabled

        self.logger = logger or get_logger(__name__)

    def extract_content(
        self, html_content: str, elements_to_remove: List[str], url: str
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """
        Extracts content while maintaining the original interface of ChunkedHTMLProcessor

        Args:
            html_content: HTML to process
            elements_to_remove: Elements to remove
            url: URL being processed

        Returns:
            Tuple of (title, clean_html, text_content, error, soup)
        """
        start_time = self.metrics.start_processing()
        content_size_mb = len(html_content.encode("utf-8")) / BYTES_PER_MB

        try:
            # Handle empty HTML
            if not html_content or not html_content.strip():
                return "", "", "", None, None

            # Parse HTML
            soup = BeautifulSoup(html_content, self.parser)

            # Determine if chunking should be used
            use_chunked = self.chunking_strategy.should_use_chunked_processing(
                html_content
            )

            if use_chunked:
                self.logger.debug(
                    f"Using chunked processing for {url} (size: {content_size_mb:.2f}MB)"
                )

                # Use fallback handler to try chunked first, then original
                def primary_operation():
                    return self._extract_content_chunked(soup, elements_to_remove)

                def fallback_operation():
                    return self._extract_content_original(soup, elements_to_remove)

                title, clean_html, text_content, error = (
                    self.fallback_handler.execute_with_fallback(
                        primary_operation, fallback_operation
                    )
                )
                use_chunked = (
                    error is None
                )  # If there is an error, it means fallback was used

            else:
                self.logger.debug(
                    f"Using original processing for {url} (size: {content_size_mb:.2f}MB)"
                )
                title, clean_html, text_content, error = self._extract_content_original(
                    soup, elements_to_remove
                )

            # Record success metrics
            if error is None:
                self.metrics.record_processing_success(
                    start_time=start_time,
                    content_size_mb=content_size_mb,
                    used_chunked_processing=use_chunked,
                    memory_peak_mb=self.memory_monitor.get_memory_usage(),
                    chunks_processed=getattr(self, "_chunks_processed", 0),
                )

            self.logger.debug(
                f"Content extraction completed for {url} in {time.time() - start_time:.2f}s"
            )

            return title or "", clean_html or "", text_content or "", error, soup

        except Exception as e:
            error_msg = f"Content extraction failed: {str(e)}"
            self.logger.error(f"Error processing {url}: {error_msg}")

            # Record error metrics
            self.metrics.record_processing_error(
                start_time=start_time,
                content_size_mb=content_size_mb,
                error_message=error_msg,
            )

            return "", "", "", error_msg, None

    def _extract_content_chunked(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extracts content using chunked processing"""
        try:
            # Monitor memory during processing
            with self.memory_monitor:
                return self.content_processor.extract_content_chunked(
                    soup, elements_to_remove, self.chunking_strategy
                )
        except Exception as e:
            raise Exception(f"Chunked processing failed: {str(e)}")

    def _extract_content_original(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extracts content using the original method"""
        return self.content_processor.extract_content_original(soup, elements_to_remove)

    def get_last_processing_metrics(self) -> Dict[str, Any]:
        """Returns metrics from the last processing run"""
        return self.metrics.get_last_metrics()

    async def extract_content_async(
        self, html_content: str, elements_to_remove: List[str], url: str
    ):
        """Asynchronous wrapper for compatibility"""
        return self.extract_content(html_content, elements_to_remove, url)

    # Properties for compatibility with the original interface
    @property
    def noise_selectors(self):
        """Compatibility with the original interface"""
        return self.content_processor.noise_selectors

    def _should_use_chunked_processing(self, html_content: str) -> bool:
        """Compatibility with the original interface"""
        return self.chunking_strategy.should_use_chunked_processing(html_content)


# Functions for compatibility with the original interface
def extract_clean_html_optimized(
    html_content: str, elements_to_remove: List[str], url: str, **processor_kwargs
) -> Tuple[str, str, str, Optional[str], Optional[BeautifulSoup]]:
    """
    Compatibility function that uses the refactored processor
    """
    processor = RefactoredChunkedHTMLProcessor(**processor_kwargs)
    return processor.extract_content(html_content, elements_to_remove, url)


def create_chunked_processor(
    enable_chunking: bool = True,
    chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
    memory_limit_mb: int = 150,
) -> RefactoredChunkedHTMLProcessor:
    """
    Compatibility factory function
    """
    return RefactoredChunkedHTMLProcessor(
        enable_chunking=enable_chunking,
        chunk_size_threshold=chunk_size_threshold,
        memory_limit_mb=memory_limit_mb,
    )
