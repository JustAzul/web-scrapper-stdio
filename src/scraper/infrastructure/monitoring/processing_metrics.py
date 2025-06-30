"""
Processing metrics module for HTML processing.

This module provides metrics tracking functionality that was extracted
from ChunkedHTMLProcessor to follow Single Responsibility Principle.
"""

import time
import threading
from typing import Dict, Any
from contextlib import contextmanager


class ProcessingMetrics:
    """
    Tracks performance metrics for HTML processing operations.

    This class is responsible for collecting and storing metrics about
    processing time, memory usage, and success/failure rates.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize the processing metrics tracker.

        Args:
            enabled: Whether metrics collection is enabled
        """
        self.enabled = enabled
        self._last_metrics: Dict[str, Any] = {}
        self._metrics_lock = threading.Lock()

    def start_processing(self) -> float:
        """
        Start a processing timer.

        Returns:
            Current timestamp for timing calculations
        """
        return time.time()

    def record_processing_success(
        self,
        start_time: float,
        content_size_mb: float,
        used_chunked_processing: bool,
        memory_peak_mb: float,
        chunks_processed: int,
    ) -> None:
        """
        Record successful processing metrics.

        Args:
            start_time: When processing started
            content_size_mb: Size of content processed in MB
            used_chunked_processing: Whether chunked processing was used
            memory_peak_mb: Peak memory usage in MB
            chunks_processed: Number of chunks processed
        """
        if not self.enabled:
            return

        processing_time = time.time() - start_time

        with self._metrics_lock:
            self._last_metrics = {
                "processing_time": processing_time,
                "content_size_mb": content_size_mb,
                "used_chunked_processing": used_chunked_processing,
                "memory_peak_mb": memory_peak_mb,
                "chunks_processed": chunks_processed,
                "processing_successful": True,
            }

    def record_processing_error(
        self, start_time: float, content_size_mb: float, error_message: str
    ) -> None:
        """
        Record processing error metrics.

        Args:
            start_time: When processing started
            content_size_mb: Size of content that failed to process
            error_message: Error message describing the failure
        """
        if not self.enabled:
            return

        processing_time = time.time() - start_time

        with self._metrics_lock:
            self._last_metrics = {
                "processing_time": processing_time,
                "content_size_mb": content_size_mb,
                "used_chunked_processing": False,
                "memory_peak_mb": 0.0,
                "chunks_processed": 0,
                "processing_successful": False,
                "error": error_message,
            }

    def get_last_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from the last processing operation.

        Returns:
            Copy of the last metrics dictionary
        """
        if not self.enabled:
            return {}

        with self._metrics_lock:
            return self._last_metrics.copy()

    @contextmanager
    def processing_context(
        self,
        content_size_mb: float,
        used_chunked_processing: bool,
        memory_peak_mb: float,
        chunks_processed: int,
    ):
        """
        Context manager for automatic metrics recording.

        Args:
            content_size_mb: Size of content being processed
            used_chunked_processing: Whether chunked processing is used
            memory_peak_mb: Peak memory usage
            chunks_processed: Number of chunks to process

        Yields:
            ProcessingContext object with success() method
        """
        start_time = self.start_processing()

        class ProcessingContext:
            def __init__(self, metrics_instance):
                self.metrics = metrics_instance
                self.success_called = False

            def success(self):
                self.success_called = True

        context = ProcessingContext(self)

        try:
            yield context

            # If success() was called explicitly, record success
            if context.success_called:
                self.record_processing_success(
                    start_time=start_time,
                    content_size_mb=content_size_mb,
                    used_chunked_processing=used_chunked_processing,
                    memory_peak_mb=memory_peak_mb,
                    chunks_processed=chunks_processed,
                )
            else:
                # If no explicit success call, assume success if no exception
                self.record_processing_success(
                    start_time=start_time,
                    content_size_mb=content_size_mb,
                    used_chunked_processing=used_chunked_processing,
                    memory_peak_mb=memory_peak_mb,
                    chunks_processed=chunks_processed,
                )

        except Exception as e:
            # Record error metrics
            self.record_processing_error(
                start_time=start_time,
                content_size_mb=content_size_mb,
                error_message=str(e),
            )
            # Re-raise the exception
            raise

    def __repr__(self) -> str:
        """String representation of the ProcessingMetrics."""
        return f"ProcessingMetrics(enabled={self.enabled})"
