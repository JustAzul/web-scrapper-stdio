"""
Test suite for ProcessingMetrics class.

This module tests the metrics tracking functionality that was extracted
from ChunkedHTMLProcessor to follow Single Responsibility Principle.
"""

import time

import pytest

from src.scraper.infrastructure.monitoring.processing_metrics import ProcessingMetrics


class TestProcessingMetrics:
    """Test cases for ProcessingMetrics class."""

    def test_processing_metrics_initialization(self):
        """Test ProcessingMetrics initializes with correct default values."""
        metrics = ProcessingMetrics()

        assert metrics.enabled is True
        assert metrics._last_metrics == {}

    def test_processing_metrics_custom_initialization(self):
        """Test ProcessingMetrics initializes with custom values."""
        metrics = ProcessingMetrics(enabled=False)

        assert metrics.enabled is False

    def test_start_processing_timer(self):
        """Test starting a processing timer."""
        metrics = ProcessingMetrics()

        start_time = metrics.start_processing()

        assert isinstance(start_time, float)
        assert start_time > 0

    def test_record_processing_success(self):
        """Test recording successful processing metrics."""
        metrics = ProcessingMetrics()

        start_time = time.time()
        content_size_mb = 1.5
        used_chunked = True
        memory_peak_mb = 75.0
        chunks_processed = 3

        metrics.record_processing_success(
            start_time=start_time,
            content_size_mb=content_size_mb,
            used_chunked_processing=used_chunked,
            memory_peak_mb=memory_peak_mb,
            chunks_processed=chunks_processed,
        )

        last_metrics = metrics.get_last_metrics()

        assert last_metrics["processing_successful"] is True
        assert last_metrics["content_size_mb"] == content_size_mb
        assert last_metrics["used_chunked_processing"] == used_chunked
        assert last_metrics["memory_peak_mb"] == memory_peak_mb
        assert last_metrics["chunks_processed"] == chunks_processed
        assert "processing_time" in last_metrics
        assert last_metrics["processing_time"] >= 0

    def test_record_processing_error(self):
        """Test recording processing error metrics."""
        metrics = ProcessingMetrics()

        start_time = time.time()
        content_size_mb = 2.0
        error_message = "Processing failed"

        metrics.record_processing_error(
            start_time=start_time,
            content_size_mb=content_size_mb,
            error_message=error_message,
        )

        last_metrics = metrics.get_last_metrics()

        assert last_metrics["processing_successful"] is False
        assert last_metrics["content_size_mb"] == content_size_mb
        assert last_metrics["error"] == error_message
        assert last_metrics["used_chunked_processing"] is False
        assert last_metrics["memory_peak_mb"] == 0.0
        assert last_metrics["chunks_processed"] == 0
        assert "processing_time" in last_metrics

    def test_get_last_metrics_copy(self):
        """Test that get_last_metrics returns a copy, not the original."""
        metrics = ProcessingMetrics()

        start_time = time.time()
        metrics.record_processing_success(
            start_time=start_time,
            content_size_mb=1.0,
            used_chunked_processing=False,
            memory_peak_mb=50.0,
            chunks_processed=0,
        )

        metrics_copy1 = metrics.get_last_metrics()
        metrics_copy2 = metrics.get_last_metrics()

        # Modify one copy
        metrics_copy1["test_key"] = "test_value"

        # Other copy should be unaffected
        assert "test_key" not in metrics_copy2
        assert metrics_copy1 is not metrics_copy2

    def test_disabled_metrics_collection(self):
        """Test that metrics collection can be disabled."""
        metrics = ProcessingMetrics(enabled=False)

        start_time = time.time()
        metrics.record_processing_success(
            start_time=start_time,
            content_size_mb=1.0,
            used_chunked_processing=False,
            memory_peak_mb=50.0,
            chunks_processed=0,
        )

        last_metrics = metrics.get_last_metrics()

        # Should return empty dict when disabled
        assert last_metrics == {}

    def test_thread_safety(self):
        """Test that metrics recording is thread-safe."""
        import threading

        metrics = ProcessingMetrics()
        results = []

        def record_metrics(thread_id):
            start_time = time.time()
            metrics.record_processing_success(
                start_time=start_time,
                content_size_mb=float(thread_id),
                used_chunked_processing=bool(thread_id % 2),
                memory_peak_mb=float(thread_id * 10),
                chunks_processed=thread_id,
            )
            results.append(metrics.get_last_metrics())

        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_metrics, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should have completed successfully
        assert len(results) == 5

        # Final metrics should be from one of the threads
        final_metrics = metrics.get_last_metrics()
        assert final_metrics["processing_successful"] is True

    def test_metrics_format_consistency(self):
        """Test that metrics always have consistent format."""
        metrics = ProcessingMetrics()

        # Test success metrics
        start_time = time.time()
        metrics.record_processing_success(
            start_time=start_time,
            content_size_mb=1.0,
            used_chunked_processing=True,
            memory_peak_mb=50.0,
            chunks_processed=2,
        )

        success_metrics = metrics.get_last_metrics()
        required_keys = {
            "processing_time",
            "content_size_mb",
            "used_chunked_processing",
            "memory_peak_mb",
            "chunks_processed",
            "processing_successful",
        }
        assert set(success_metrics.keys()) == required_keys

        # Test error metrics
        metrics.record_processing_error(
            start_time=start_time, content_size_mb=2.0, error_message="Test error"
        )

        error_metrics = metrics.get_last_metrics()
        required_error_keys = required_keys | {"error"}
        assert set(error_metrics.keys()) == required_error_keys

    def test_processing_time_calculation(self):
        """Test that processing time is calculated correctly."""
        metrics = ProcessingMetrics()

        start_time = time.time() - 2.0  # 2 seconds ago

        metrics.record_processing_success(
            start_time=start_time,
            content_size_mb=1.0,
            used_chunked_processing=False,
            memory_peak_mb=50.0,
            chunks_processed=0,
        )

        last_metrics = metrics.get_last_metrics()
        processing_time = last_metrics["processing_time"]

        # Should be approximately 2 seconds (with some tolerance)
        assert 1.8 <= processing_time <= 2.5

    def test_metrics_data_types(self):
        """Test that metrics have correct data types."""
        metrics = ProcessingMetrics()

        start_time = time.time()
        metrics.record_processing_success(
            start_time=start_time,
            content_size_mb=1.5,
            used_chunked_processing=True,
            memory_peak_mb=75.0,
            chunks_processed=3,
        )

        last_metrics = metrics.get_last_metrics()

        assert isinstance(last_metrics["processing_time"], float)
        assert isinstance(last_metrics["content_size_mb"], float)
        assert isinstance(last_metrics["used_chunked_processing"], bool)
        assert isinstance(last_metrics["memory_peak_mb"], float)
        assert isinstance(last_metrics["chunks_processed"], int)
        assert isinstance(last_metrics["processing_successful"], bool)

    def test_context_manager_functionality(self):
        """Test ProcessingMetrics as a context manager."""
        metrics = ProcessingMetrics()

        with metrics.processing_context(
            content_size_mb=1.0,
            used_chunked_processing=True,
            memory_peak_mb=60.0,
            chunks_processed=1,
        ) as ctx:
            # Simulate some processing time
            time.sleep(0.1)
            ctx.success()

        last_metrics = metrics.get_last_metrics()

        assert last_metrics["processing_successful"] is True
        assert last_metrics["content_size_mb"] == 1.0
        assert last_metrics["processing_time"] >= 0.1

    def test_context_manager_with_error(self):
        """Test ProcessingMetrics context manager with error handling."""
        metrics = ProcessingMetrics()

        with pytest.raises(ValueError):
            with metrics.processing_context(
                content_size_mb=1.0,
                used_chunked_processing=True,
                memory_peak_mb=60.0,
                chunks_processed=1,
            ):
                raise ValueError("Test error")

        last_metrics = metrics.get_last_metrics()

        assert last_metrics["processing_successful"] is False
        assert "error" in last_metrics
