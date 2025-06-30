"""
Test suite for MemoryMonitor class.

This module tests the memory monitoring functionality that was extracted
from ChunkedHTMLProcessor to follow Single Responsibility Principle.
"""

from unittest.mock import Mock, patch

import pytest

from src.scraper.infrastructure.monitoring.memory_monitor import (
    MemoryLimitExceededError,
    MemoryMonitor,
)


class TestMemoryMonitor:
    """Test cases for MemoryMonitor class."""

    def test_memory_monitor_initialization(self):
        """Test MemoryMonitor initializes with correct default values."""
        monitor = MemoryMonitor()

        assert monitor.memory_limit_mb == 100
        assert monitor.enabled is True

    def test_memory_monitor_custom_initialization(self):
        """Test MemoryMonitor initializes with custom values."""
        monitor = MemoryMonitor(memory_limit_mb=200, enabled=False)

        assert monitor.memory_limit_mb == 200
        assert monitor.enabled is False

    @patch("psutil.Process")
    def test_get_memory_usage_success(self, mock_process_class):
        """Test successful memory usage retrieval."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 104857600  # 100 MB in bytes
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()

        # Act
        memory_mb = monitor.get_memory_usage()

        # Assert
        assert memory_mb == 100.0
        mock_process_class.assert_called_once()
        mock_process.memory_info.assert_called_once()

    @patch("psutil.Process")
    def test_get_memory_usage_failure(self, mock_process_class):
        """Test memory usage retrieval handles errors gracefully."""
        # Arrange
        mock_process_class.side_effect = OSError("Process not found")

        monitor = MemoryMonitor()

        # Act
        memory_mb = monitor.get_memory_usage()

        # Assert
        assert memory_mb == 0.0

    @patch("psutil.Process")
    def test_monitor_memory_usage_detailed(self, mock_process_class):
        """Test detailed memory usage monitoring."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 104857600  # 100 MB
        mock_process.memory_info.return_value.vms = 209715200  # 200 MB
        mock_process.memory_percent.return_value = 15.5
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor()

        # Act
        memory_info = monitor.monitor_memory_usage()

        # Assert
        assert memory_info["memory_rss_mb"] == 100.0
        assert memory_info["memory_vms_mb"] == 200.0
        assert memory_info["memory_percent"] == 15.5

    @patch("psutil.Process")
    def test_monitor_memory_usage_error_handling(self, mock_process_class):
        """Test memory monitoring handles errors and returns safe defaults."""
        # Arrange
        mock_process_class.side_effect = OSError("Access denied")

        monitor = MemoryMonitor()

        # Act
        memory_info = monitor.monitor_memory_usage()

        # Assert
        assert memory_info["memory_rss_mb"] == 0.1
        assert memory_info["memory_vms_mb"] == 0.1
        assert memory_info["memory_percent"] == 0.1

    @patch("psutil.Process")
    def test_check_memory_limit_within_limit(self, mock_process_class):
        """Test memory limit check when within limits."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 52428800  # 50 MB
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(memory_limit_mb=100)

        # Act & Assert - should not raise exception
        monitor.check_memory_limit()

    @patch("psutil.Process")
    def test_check_memory_limit_exceeds_limit(self, mock_process_class):
        """Test memory limit check when exceeding limits."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 157286400  # 150 MB
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(memory_limit_mb=100)

        # Act & Assert
        with pytest.raises(MemoryLimitExceededError) as exc_info:
            monitor.check_memory_limit()

        assert "Memory limit exceeded" in str(exc_info.value)
        assert "150.0 MB" in str(exc_info.value)
        assert "100 MB" in str(exc_info.value)

    @patch("psutil.Process")
    def test_check_memory_limit_with_threshold(self, mock_process_class):
        """Test memory limit check with custom threshold."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 115343360  # 110 MB
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(memory_limit_mb=100)

        # Act & Assert - 110 MB > 100 MB * 1.2 threshold, should raise
        with pytest.raises(MemoryLimitExceededError):
            monitor.check_memory_limit(threshold_multiplier=1.0)

        # Should not raise with higher threshold
        monitor.check_memory_limit(threshold_multiplier=1.5)

    def test_check_memory_limit_disabled(self):
        """Test memory limit check when monitoring is disabled."""
        # Arrange
        monitor = MemoryMonitor(enabled=False)

        # Act & Assert - should not raise exception even if we can't mock memory
        monitor.check_memory_limit()

    @patch("psutil.Process")
    def test_context_manager_functionality(self, mock_process_class):
        """Test MemoryMonitor as a context manager."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 52428800  # 50 MB
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(memory_limit_mb=100)

        # Act & Assert
        with monitor:
            # Should not raise exception
            pass

        # Verify memory was checked
        mock_process_class.assert_called()

    @patch("psutil.Process")
    def test_context_manager_with_memory_limit_exceeded(self, mock_process_class):
        """Test MemoryMonitor context manager when memory limit is exceeded."""
        # Arrange
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 157286400  # 150 MB
        mock_process_class.return_value = mock_process

        monitor = MemoryMonitor(memory_limit_mb=100)

        # Act & Assert
        with pytest.raises(MemoryLimitExceededError):
            with monitor:
                pass

    def test_memory_monitor_repr(self):
        """Test string representation of MemoryMonitor."""
        monitor = MemoryMonitor(memory_limit_mb=150, enabled=True)

        repr_str = repr(monitor)

        assert "MemoryMonitor" in repr_str
        assert "150" in repr_str
        assert "enabled=True" in repr_str
