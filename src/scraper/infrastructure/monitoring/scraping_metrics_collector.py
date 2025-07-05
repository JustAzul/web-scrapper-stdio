"""
ScrapingMetricsCollector - Single Responsibility: Collect scraping metrics
Part of refactoring T003 - Break up IntelligentFallbackScraper following SRP
"""

import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional


class ScrapingMetricsCollector:
    """Collects metrics from scraping operations following the Single Responsibility Principle"""

    def __init__(self, enabled: bool = True):
        """
        Initializes the metrics collector

        Args:
            enabled: If metrics collection is enabled
        """
        self.enabled = enabled
        self.last_metrics: Dict[str, Any] = {}
        self._metrics_lock = threading.Lock()

    def start_operation(self) -> float:
        """
        Starts timing an operation

        Returns:
            Timestamp of the operation's start
        """
        return time.time()

    def record_scraping_success(
        self,
        start_time: float,
        strategy_used: str,
        attempts: int,
        final_url: Optional[str] = None,
        content_size: Optional[int] = None,
    ) -> None:
        """
        Records scraping success metrics

        Args:
            start_time: Timestamp of the operation's start
            strategy_used: Strategy used (playwright_optimized, requests_fallback, etc.)
            attempts: Number of attempts made
            final_url: Final URL after redirects
            content_size: Size of the obtained content in bytes
        """
        if not self.enabled:
            return

        total_time = time.time() - start_time

        with self._metrics_lock:
            self.last_metrics = {
                "success": True,
                "total_time": total_time,
                "strategy_used": strategy_used,
                "attempts": attempts,
                "final_url": final_url,
                "content_size": content_size,
                "timestamp": time.time(),
                "error_message": None,
            }

    def record_scraping_failure(
        self,
        start_time: float,
        error_message: str,
        attempts: int,
        strategy_attempted: Optional[str] = None,
    ) -> None:
        """
        Records scraping failure metrics

        Args:
            start_time: Timestamp of the operation's start
            error_message: Error message
            attempts: Number of attempts made
            strategy_attempted: Strategy that was attempted
        """
        if not self.enabled:
            return

        total_time = time.time() - start_time

        with self._metrics_lock:
            self.last_metrics = {
                "success": False,
                "total_time": total_time,
                "strategy_used": strategy_attempted,
                "attempts": attempts,
                "final_url": None,
                "content_size": None,
                "timestamp": time.time(),
                "error_message": error_message,
            }

    def get_last_metrics(self) -> Dict[str, Any]:
        """
        Returns a copy of the metrics from the last operation

        Returns:
            Dictionary with metrics from the last operation
        """
        if not self.enabled:
            return {}

        with self._metrics_lock:
            return self.last_metrics.copy()

    def clear_metrics(self) -> None:
        """Clears stored metrics"""
        with self._metrics_lock:
            self.last_metrics.clear()

    def is_enabled(self) -> bool:
        """
        Checks if metrics collection is enabled

        Returns:
            True if enabled, False otherwise
        """
        return self.enabled

    def enable(self) -> None:
        """Enables metrics collection"""
        self.enabled = True

    def disable(self) -> None:
        """Disables metrics collection"""
        self.enabled = False
        self.clear_metrics()

    @contextmanager
    def operation_context(self, operation_name: str):
        """
        Context manager for automatic measurement of operations

        Args:
            operation_name: Name of the operation being measured

        Yields:
            Context object with success() and failure() methods
        """
        start_time = self.start_operation()

        class OperationContext:
            def __init__(self, metrics_collector, start_time, operation_name):
                self.metrics = metrics_collector
                self.start_time = start_time
                self.operation_name = operation_name
                self.completed = False

            def success(self, strategy_used: str, attempts: int = 1, **kwargs):
                if not self.completed:
                    self.metrics.record_scraping_success(
                        self.start_time, strategy_used, attempts, **kwargs
                    )
                    self.completed = True

            def failure(self, error_message: str, attempts: int = 1, **kwargs):
                if not self.completed:
                    self.metrics.record_scraping_failure(
                        self.start_time, error_message, attempts, **kwargs
                    )
                    self.completed = True

        context = OperationContext(self, start_time, operation_name)

        try:
            yield context
        except Exception as e:
            if not context.completed:
                context.failure(str(e))
            raise

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Returns a performance summary of the last operation

        Returns:
            Performance summary
        """
        metrics = self.get_last_metrics()
        if not metrics:
            return {}

        return {
            "operation_successful": metrics.get("success", False),
            "total_time_seconds": metrics.get("total_time", 0),
            "strategy_used": metrics.get("strategy_used"),
            "attempts_made": metrics.get("attempts", 0),
            "has_error": metrics.get("error_message") is not None,
        }

    def __repr__(self) -> str:
        """String representation of the metrics collector"""
        return f"ScrapingMetricsCollector(enabled={self.enabled})"
