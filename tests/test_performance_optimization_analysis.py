"""
Tests for Performance Optimization Analysis (T015).

This module tests the comprehensive performance monitoring, analysis, and optimization
system. Follows TDD methodology with comprehensive coverage.
"""

import asyncio
from unittest.mock import patch

import pytest

from src.scraper.performance import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceThresholds,
    performance_context,
)


class TestPerformanceMetrics:
    """Test the PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test basic PerformanceMetrics creation."""
        metrics = PerformanceMetrics()

        # Check default values
        assert metrics.total_time == 0.0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.content_size_bytes == 0
        assert metrics.requests_count == 0
        assert metrics.used_cache is False
        assert metrics.compression_ratio == 0.0

    def test_performance_metrics_compression_ratio_calculation(self):
        """Test automatic compression ratio calculation."""
        metrics = PerformanceMetrics(
            content_size_bytes=1000, processed_content_size_bytes=300
        )

        # Should calculate compression ratio in __post_init__
        assert metrics.compression_ratio == 0.3

    def test_performance_metrics_to_dict(self):
        """Test metrics serialization to dictionary."""
        metrics = PerformanceMetrics(
            total_time=5.5,
            navigation_time=2.0,
            memory_usage_mb=128.0,
            content_size_bytes=1024,
            requests_count=3,
            used_cache=True,
            used_chunked_processing=True,
        )

        result = metrics.to_dict()

        # Check structure
        assert "timing" in result
        assert "memory" in result
        assert "content" in result
        assert "requests" in result
        assert "optimizations" in result

        # Check values
        assert result["timing"]["total_time"] == 5.5
        assert result["timing"]["navigation_time"] == 2.0
        assert result["memory"]["usage_mb"] == 128.0
        assert result["content"]["size_bytes"] == 1024
        assert result["requests"]["count"] == 3
        assert result["optimizations"]["used_cache"] is True
        assert result["optimizations"]["used_chunked_processing"] is True


class TestPerformanceAnalyzer:
    """Test the PerformanceAnalyzer class."""

    def test_analyzer_creation(self):
        """Test PerformanceAnalyzer creation with default thresholds."""
        analyzer = PerformanceAnalyzer()

        assert analyzer.thresholds is not None
        assert isinstance(analyzer.thresholds, PerformanceThresholds)

    def test_analyze_timing_performance_issues(self):
        """Test timing performance analysis."""
        analyzer = PerformanceAnalyzer()

        # Create metrics with slow total time
        metrics = PerformanceMetrics(total_time=35.0)  # Exceeds 30s threshold

        recommendations = analyzer.analyze_metrics(metrics)

        # Should have timing recommendation
        timing_recs = [r for r in recommendations if r.category == "timing"]
        assert len(timing_recs) > 0

        timing_rec = timing_recs[0]
        assert timing_rec.priority == "HIGH"
        assert "35.0s" in timing_rec.issue

    def test_analyze_memory_performance_issues(self):
        """Test memory performance analysis."""
        analyzer = PerformanceAnalyzer()

        # Create metrics with high memory usage
        metrics = PerformanceMetrics(memory_usage_mb=600.0)  # Exceeds 512MB threshold

        recommendations = analyzer.analyze_metrics(metrics)

        # Should have memory recommendation
        memory_recs = [r for r in recommendations if r.category == "memory"]
        assert len(memory_recs) > 0

        memory_rec = memory_recs[0]
        assert memory_rec.priority == "HIGH"
        assert "600.0MB" in memory_rec.issue


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class."""

    def test_monitor_creation(self):
        """Test PerformanceMonitor creation."""
        monitor = PerformanceMonitor()

        assert monitor.metrics is not None
        assert isinstance(monitor.metrics, PerformanceMetrics)
        assert monitor.start_time == 0.0

    def test_record_timing(self):
        """Test recording timing metrics."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        # Record different operation timings
        monitor.record_timing("navigation", 2.5)
        monitor.record_timing("content_extraction", 1.5)
        monitor.record_timing("content_processing", 0.8)

        metrics = monitor.stop_monitoring()

        assert metrics.navigation_time == 2.5
        assert metrics.content_extraction_time == 1.5
        assert metrics.content_processing_time == 0.8

    def test_record_content_metrics(self):
        """Test recording content size metrics."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        # Record content metrics
        monitor.record_content_metrics(1000, 300)

        metrics = monitor.stop_monitoring()

        assert metrics.content_size_bytes == 1000
        assert metrics.processed_content_size_bytes == 300
        assert metrics.compression_ratio == 0.3

    def test_record_optimization_usage(self):
        """Test recording optimization usage."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        # Record optimization usage
        monitor.record_optimization_usage(
            cache=True, chunked=True, resource_blocking=False
        )

        metrics = monitor.stop_monitoring()

        assert metrics.used_cache is True
        assert metrics.used_chunked_processing is True
        assert metrics.used_resource_blocking is False


class TestPerformanceContext:
    """Test the performance_context context manager."""

    @pytest.mark.asyncio
    async def test_performance_context_basic(self):
        """Test basic performance context usage."""
        with patch("src.scraper.performance.logger") as mock_logger:
            async with performance_context("test-url") as monitor:
                # Should provide a PerformanceMonitor
                assert isinstance(monitor, PerformanceMonitor)

                # Simulate some work
                await asyncio.sleep(0.1)
                monitor.record_timing("test_operation", 0.05)

            # Should have logged performance summary
            assert mock_logger.info.called
            info_calls = [call for call in mock_logger.info.call_args_list]
            assert len(info_calls) > 0

            # Check that URL and timing info are in the log
            log_message = info_calls[0][0][0]
            assert "test-url" in log_message
            assert "total" in log_message.lower()


if __name__ == "__main__":
    pytest.main([__file__])
