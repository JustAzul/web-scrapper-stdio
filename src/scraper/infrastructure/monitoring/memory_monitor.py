"""
Memory monitoring module for HTML processing.

This module provides memory monitoring functionality that was extracted
from ChunkedHTMLProcessor to follow Single Responsibility Principle.
"""

from typing import Dict

from src.logger import get_logger

logger = get_logger(__name__)


class MemoryLimitExceededError(RuntimeError):
    """Raised when memory usage exceeds configured limit."""

    pass


class MemoryMonitor:
    """
    Monitors memory usage during HTML processing operations.

    This class is responsible for tracking memory consumption and
    enforcing memory limits to prevent out-of-memory conditions.
    """

    def __init__(self, memory_limit_mb: int = 100, enabled: bool = True):
        """
        Initialize the memory monitor.

        Args:
            memory_limit_mb: Memory limit in megabytes
            enabled: Whether memory monitoring is enabled
        """
        self.memory_limit_mb = memory_limit_mb
        self.enabled = enabled

    def get_memory_usage(self) -> float:
        """
        Get current RSS memory usage in MB.

        Returns:
            Current memory usage in megabytes, or 0.0 if unable to determine
        """
        if not self.enabled:
            return 0.0

        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

    def monitor_memory_usage(self) -> Dict[str, float]:
        """
        Monitor detailed memory usage information.

        Returns:
            Dictionary containing memory usage metrics
        """
        if not self.enabled:
            return {"memory_rss_mb": 0.1, "memory_vms_mb": 0.1, "memory_percent": 0.1}

        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "memory_rss_mb": memory_info.rss / 1024 / 1024,  # RSS in MB
                "memory_vms_mb": memory_info.vms / 1024 / 1024,  # VMS in MB
                # Ensure non-zero
                "memory_percent": max(0.1, process.memory_percent()),
            }
        except Exception as e:
            logger.warning(f"Failed to monitor memory usage: {e}")
            return {
                "memory_rss_mb": 0.1,  # Default to small non-zero values
                "memory_vms_mb": 0.1,
                "memory_percent": 0.1,
            }

    def check_memory_limit(self, threshold_multiplier: float = 1.2) -> None:
        """
        Check if current memory usage exceeds the configured limit.

        Args:
            threshold_multiplier: Multiplier for the memory limit threshold

        Raises:
            MemoryLimitExceededError: If memory usage exceeds limit
        """
        if not self.enabled:
            return

        current_memory = self.get_memory_usage()
        threshold = self.memory_limit_mb * threshold_multiplier

        if current_memory > threshold:
            raise MemoryLimitExceededError(
                f"Memory limit exceeded: {current_memory:.1f} MB > "
                f"{self.memory_limit_mb} MB (threshold: {threshold:.1f} MB)"
            )

    def __enter__(self):
        """Context manager entry."""
        self.check_memory_limit()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:  # Only check on successful completion
            self.check_memory_limit()

    def __repr__(self) -> str:
        """String representation of the MemoryMonitor."""
        return (
            f"MemoryMonitor(memory_limit_mb={self.memory_limit_mb}, "
            f"enabled={self.enabled})"
        )
