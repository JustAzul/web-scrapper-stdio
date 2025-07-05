"""
Performance Monitoring and Optimization System for Web Scraper MCP.

This module implements performance monitoring, analysis, and optimization
capabilities following T015 requirements:

1. Performance metrics collection and analysis
2. Bottleneck identification and reporting
3. Memory usage monitoring and optimization
4. Request timing and throughput analysis
5. Automated performance recommendations
"""

import gc
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional

import psutil

from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class for storing performance metrics of a scraping operation."""

    # Timing metrics (seconds)
    total_time: float = 0.0
    navigation_time: float = 0.0
    content_extraction_time: float = 0.0
    content_processing_time: float = 0.0
    network_time: float = 0.0
    page_load_time: float = 0.0
    browser_startup_time: float = 0.0
    dom_ready_time: float = 0.0

    # Memory metrics (MB)
    memory_usage_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_delta_mb: float = 0.0

    # Content metrics
    content_size_bytes: int = 0
    processed_content_size_bytes: int = 0
    compression_ratio: float = 0.0

    # Request metrics
    requests_count: int = 0
    failed_requests: int = 0
    retry_count: int = 0

    # Optimization flags
    used_cache: bool = False
    used_chunked_processing: bool = False
    used_resource_blocking: bool = False

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.content_size_bytes > 0 and self.processed_content_size_bytes > 0:
            self.compression_ratio = (
                self.processed_content_size_bytes / self.content_size_bytes
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/analysis."""
        return {
            "timing": {
                "total_time": self.total_time,
                "navigation_time": self.navigation_time,
                "content_extraction_time": self.content_extraction_time,
                "content_processing_time": self.content_processing_time,
                "network_time": self.network_time,
                "browser_startup_time": self.browser_startup_time,
                "page_load_time": self.page_load_time,
                "dom_ready_time": self.dom_ready_time,
            },
            "memory": {
                "usage_mb": self.memory_usage_mb,
                "peak_mb": self.memory_peak_mb,
                "delta_mb": self.memory_delta_mb,
            },
            "content": {
                "size_bytes": self.content_size_bytes,
                "processed_size_bytes": self.processed_content_size_bytes,
                "compression_ratio": self.compression_ratio,
            },
            "requests": {
                "count": self.requests_count,
                "failed": self.failed_requests,
                "retries": self.retry_count,
            },
            "optimizations": {
                "used_cache": self.used_cache,
                "used_chunked_processing": self.used_chunked_processing,
                "used_resource_blocking": self.used_resource_blocking,
            },
        }


@dataclass
class PerformanceThresholds:
    """Performance thresholds for optimization analysis."""

    # Time thresholds (seconds)
    max_total_time: float = 30.0
    max_navigation_time: float = 10.0
    max_content_processing_time: float = 5.0

    # Memory thresholds (MB)
    max_memory_usage: float = 512.0
    max_memory_delta: float = 100.0

    # Content thresholds
    min_compression_ratio: float = 0.1
    max_content_size_mb: float = 50.0

    # Request thresholds
    max_retry_count: int = 3
    max_failure_rate: float = 0.1


@dataclass
class PerformanceRecommendation:
    """Performance optimization recommendation."""

    category: str
    priority: str  # HIGH, MEDIUM, LOW
    issue: str
    recommendation: str
    potential_improvement: str
    implementation_effort: str  # LOW, MEDIUM, HIGH


class PerformanceAnalyzer:
    """Analyzes performance metrics and provides optimization recommendations."""

    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.logger = get_logger(__name__)

    def analyze_metrics(
        self, metrics: PerformanceMetrics
    ) -> List[PerformanceRecommendation]:
        """
        Analyze performance metrics and generate recommendations.

        Args:
            metrics: Performance metrics to analyze

        Returns:
            List of performance recommendations
        """
        recommendations = []

        # Analyze timing performance
        recommendations.extend(self._analyze_timing(metrics))

        # Analyze memory performance
        recommendations.extend(self._analyze_memory(metrics))

        # Analyze content processing
        recommendations.extend(self._analyze_content(metrics))

        # Analyze request patterns
        recommendations.extend(self._analyze_requests(metrics))

        # Analyze optimizations
        recommendations.extend(self._analyze_optimizations(metrics))

        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

        return recommendations

    def _analyze_timing(
        self, metrics: PerformanceMetrics
    ) -> List[PerformanceRecommendation]:
        """Analyze timing performance."""
        recommendations = []

        # Total time analysis
        if metrics.total_time > self.thresholds.max_total_time:
            recommendations.append(
                PerformanceRecommendation(
                    category="timing",
                    priority="HIGH",
                    issue=(
                        f"Total scraping time ({metrics.total_time:.1f}s) exceeds "
                        f"threshold ({self.thresholds.max_total_time}s)"
                    ),
                    recommendation=(
                        "Enable resource blocking, implement caching, or use lighter "
                        "extraction methods"
                    ),
                    potential_improvement="30-50% time reduction",
                    implementation_effort="MEDIUM",
                )
            )

        # Navigation time analysis
        if metrics.navigation_time > self.thresholds.max_navigation_time:
            recommendations.append(
                PerformanceRecommendation(
                    category="timing",
                    priority="MEDIUM",
                    issue=f"Navigation time ({metrics.navigation_time:.1f}s) is slow",
                    recommendation=(
                        "Enable resource blocking for images/CSS/fonts, "
                        "reduce timeout values"
                    ),
                    potential_improvement="20-40% navigation improvement",
                    implementation_effort="LOW",
                )
            )

        # Content processing time analysis
        if (
            metrics.content_processing_time
            > self.thresholds.max_content_processing_time
        ):
            recommendations.append(
                PerformanceRecommendation(
                    category="timing",
                    priority="MEDIUM",
                    issue=(
                        "Content processing time "
                        f"({metrics.content_processing_time:.1f}s) is slow"
                    ),
                    recommendation=(
                        "Enable chunked processing for large content, optimize "
                        "HTML parsing"
                    ),
                    potential_improvement="25-45% processing improvement",
                    implementation_effort="MEDIUM",
                )
            )

        return recommendations

    def _analyze_memory(
        self, metrics: PerformanceMetrics
    ) -> List[PerformanceRecommendation]:
        """Analyze memory performance."""
        recommendations = []

        # Memory usage analysis
        if metrics.memory_usage_mb > self.thresholds.max_memory_usage:
            recommendations.append(
                PerformanceRecommendation(
                    category="memory",
                    priority="HIGH",
                    issue=(
                        f"Memory usage ({metrics.memory_usage_mb:.1f}MB) exceeds "
                        "threshold"
                    ),
                    recommendation=(
                        "Enable chunked processing, implement memory monitoring, "
                        "reduce content size"
                    ),
                    potential_improvement="40-60% memory reduction",
                    implementation_effort="MEDIUM",
                )
            )

        # Memory delta analysis
        if metrics.memory_delta_mb > self.thresholds.max_memory_delta:
            recommendations.append(
                PerformanceRecommendation(
                    category="memory",
                    priority="MEDIUM",
                    issue=(
                        f"Memory increase ({metrics.memory_delta_mb:.1f}MB) indicates "
                        "potential leak"
                    ),
                    recommendation=(
                        "Implement proper cleanup, use context managers, force garbage "
                        "collection"
                    ),
                    potential_improvement="Memory leak prevention",
                    implementation_effort="LOW",
                )
            )

        return recommendations

    def _analyze_content(
        self, metrics: PerformanceMetrics
    ) -> List[PerformanceRecommendation]:
        """Analyze content processing performance."""
        recommendations = []

        # Content size analysis
        content_size_mb = metrics.content_size_bytes / (1024 * 1024)
        if content_size_mb > self.thresholds.max_content_size_mb:
            recommendations.append(
                PerformanceRecommendation(
                    category="content",
                    priority="MEDIUM",
                    issue=f"Content size ({content_size_mb:.1f}MB) is very large",
                    recommendation=(
                        "Enable resource blocking, implement content filtering, "
                        "use streaming processing"
                    ),
                    potential_improvement="Faster processing, reduced memory usage",
                    implementation_effort="MEDIUM",
                )
            )

        # Compression ratio analysis
        if metrics.compression_ratio > (1 - self.thresholds.min_compression_ratio):
            recommendations.append(
                PerformanceRecommendation(
                    category="content",
                    priority="LOW",
                    issue=(
                        f"Low content compression ratio ({metrics.compression_ratio:.2f})"
                    ),
                    recommendation=(
                        "Improve content filtering, remove more noise elements"
                    ),
                    potential_improvement="Better content quality, smaller output",
                    implementation_effort="LOW",
                )
            )

        return recommendations

    def _analyze_requests(
        self, metrics: PerformanceMetrics
    ) -> List[PerformanceRecommendation]:
        """Analyze request patterns."""
        recommendations = []

        # Retry analysis
        if metrics.retry_count > self.thresholds.max_retry_count:
            recommendations.append(
                PerformanceRecommendation(
                    category="requests",
                    priority="MEDIUM",
                    issue=(
                        f"High retry count ({metrics.retry_count}) indicates "
                        "reliability issues"
                    ),
                    recommendation=(
                        "Implement exponential backoff, improve error handling, "
                        "check network stability"
                    ),
                    potential_improvement="Better reliability, faster completion",
                    implementation_effort="MEDIUM",
                )
            )

        # Failure rate analysis
        if metrics.requests_count > 0:
            failure_rate = metrics.failed_requests / metrics.requests_count
            if failure_rate > self.thresholds.max_failure_rate:
                recommendations.append(
                    PerformanceRecommendation(
                        category="requests",
                        priority="HIGH",
                        issue=(
                            f"High failure rate ({failure_rate:.1%}) indicates "
                            "systemic issues"
                        ),
                        recommendation=(
                            "Review error handling, implement circuit breaker, "
                            "improve fallback strategies"
                        ),
                        potential_improvement=(
                            "Higher success rate, better user experience"
                        ),
                        implementation_effort="HIGH",
                    )
                )

        return recommendations

    def _analyze_optimizations(
        self, metrics: PerformanceMetrics
    ) -> List[PerformanceRecommendation]:
        """Analyze optimization usage."""
        recommendations = []

        # Cache usage analysis
        if not metrics.used_cache and metrics.total_time > 5.0:
            recommendations.append(
                PerformanceRecommendation(
                    category="optimizations",
                    priority="MEDIUM",
                    issue="Caching not utilized for slow operations",
                    recommendation=(
                        "Implement result caching for repeated URLs or content patterns"
                    ),
                    potential_improvement="50-80% improvement for repeated requests",
                    implementation_effort="MEDIUM",
                )
            )

        # Chunked processing analysis
        if not metrics.used_chunked_processing and metrics.memory_usage_mb > 100:
            recommendations.append(
                PerformanceRecommendation(
                    category="optimizations",
                    priority="MEDIUM",
                    issue="Chunked processing not used for large content",
                    recommendation="Enable chunked processing for memory efficiency",
                    potential_improvement="30-50% memory reduction",
                    implementation_effort="LOW",
                )
            )

        # Resource blocking analysis
        if not metrics.used_resource_blocking and metrics.navigation_time > 5.0:
            recommendations.append(
                PerformanceRecommendation(
                    category="optimizations",
                    priority="LOW",
                    issue="Resource blocking not enabled for slow navigation",
                    recommendation=(
                        "Enable resource blocking for images, CSS, and fonts"
                    ),
                    potential_improvement="20-40% navigation improvement",
                    implementation_effort="LOW",
                )
            )

        return recommendations


class PerformanceMonitor:
    """Real-time performance monitoring for scraping operations."""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.start_time = 0.0
        self.start_memory = 0.0
        self.peak_memory = 0.0
        self._lock = Lock()
        self.logger = get_logger(__name__)

    def start_monitoring(self):
        """Start performance monitoring."""
        with self._lock:
            self.start_time = time.time()
            self.start_memory = self._get_memory_usage()
            self.peak_memory = self.start_memory
            self.metrics = PerformanceMetrics()

    def stop_monitoring(self) -> PerformanceMetrics:
        """Stop monitoring and return final metrics."""
        with self._lock:
            self.metrics.total_time = time.time() - self.start_time
            current_memory = self._get_memory_usage()
            self.metrics.memory_usage_mb = current_memory
            self.metrics.memory_peak_mb = self.peak_memory
            self.metrics.memory_delta_mb = current_memory - self.start_memory

            return self.metrics

    def record_timing(self, operation: str, duration: float):
        """Record timing for a specific operation."""
        with self._lock:
            if operation == "navigation":
                self.metrics.navigation_time += duration
            elif operation == "content_extraction":
                self.metrics.content_extraction_time += duration
            elif operation == "content_processing":
                self.metrics.content_processing_time += duration
            elif operation == "network":
                self.metrics.network_time += duration
            elif operation == "browser_startup":
                self.metrics.browser_startup_time += duration
            elif operation == "page_load":
                self.metrics.page_load_time += duration
            elif operation == "dom_ready":
                self.metrics.dom_ready_time += duration

    def record_content_metrics(self, original_size: int, processed_size: int):
        """Record content size metrics."""
        with self._lock:
            self.metrics.content_size_bytes = original_size
            self.metrics.processed_content_size_bytes = processed_size
            if original_size > 0:
                self.metrics.compression_ratio = processed_size / original_size

    def record_request_metrics(self, success: bool, retry: bool = False):
        """Record request success/failure metrics."""
        with self._lock:
            self.metrics.requests_count += 1
            if not success:
                self.metrics.failed_requests += 1
            if retry:
                self.metrics.retry_count += 1

    def record_optimization_usage(
        self,
        cache: bool = False,
        chunked: bool = False,
        resource_blocking: bool = False,
    ):
        """Record optimization technique usage."""
        with self._lock:
            if cache:
                self.metrics.used_cache = True
            if chunked:
                self.metrics.used_chunked_processing = True
            if resource_blocking:
                self.metrics.used_resource_blocking = True

    def update_memory_peak(self):
        """Update peak memory usage."""
        current_memory = self._get_memory_usage()
        with self._lock:
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0


@asynccontextmanager
async def performance_context(url: str = "unknown"):
    """Context manager for automatic performance monitoring."""
    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    try:
        yield monitor
    finally:
        metrics = monitor.stop_monitoring()

        # Analyze performance and log recommendations
        analyzer = PerformanceAnalyzer()
        recommendations = analyzer.analyze_metrics(metrics)

        # Log performance summary
        logger.info(
            f"Performance summary for {url}: {metrics.total_time:.2f}s total, "
            f"{metrics.memory_peak_mb:.1f}MB peak memory"
        )

        # Log high-priority recommendations
        high_priority_recs = [r for r in recommendations if r.priority == "HIGH"]
        if high_priority_recs:
            logger.warning(f"High-priority performance issues found for {url}:")
            for rec in high_priority_recs:
                logger.warning(f"  - {rec.issue}: {rec.recommendation}")


class PerformanceProfiler:
    """Advanced performance profiling for detailed analysis."""

    def __init__(self):
        self.profiles: List[Dict[str, Any]] = []
        self.logger = get_logger(__name__)

    async def profile_operation(
        self, operation_name: str, operation_func, *args, **kwargs
    ):
        """Profile a specific operation with detailed metrics."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Force garbage collection before operation
        gc.collect()
        gc_start_memory = self._get_memory_usage()

        try:
            result = await operation_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)

        end_time = time.time()
        end_memory = self._get_memory_usage()

        # Force garbage collection after operation
        gc.collect()
        gc_end_memory = self._get_memory_usage()

        profile = {
            "operation": operation_name,
            "success": success,
            "error": error,
            "duration": end_time - start_time,
            "memory_start": start_memory,
            "memory_end": end_memory,
            "memory_delta": end_memory - start_memory,
            "memory_leaked": gc_end_memory - gc_start_memory,
            "timestamp": time.time(),
        }

        self.profiles.append(profile)

        # Log performance issues
        if not success:
            self.logger.error(f"Operation {operation_name} failed: {error}")
        elif profile["duration"] > 10.0:
            self.logger.warning(
                f"Slow operation {operation_name}: {profile['duration']:.2f}s"
            )
        elif profile["memory_leaked"] > 50.0:
            self.logger.warning(
                f"Memory leak detected in {operation_name}: "
                f"{profile['memory_leaked']:.1f}MB"
            )

        return result

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all profiled operations."""
        if not self.profiles:
            return {}

        total_operations = len(self.profiles)
        successful_operations = sum(1 for p in self.profiles if p["success"])
        total_time = sum(p["duration"] for p in self.profiles)
        total_memory_leaked = sum(max(0, p["memory_leaked"]) for p in self.profiles)

        slowest_operation = max(self.profiles, key=lambda p: p["duration"])
        most_memory_intensive = max(self.profiles, key=lambda p: p["memory_delta"])

        return {
            "total_operations": total_operations,
            "success_rate": successful_operations / total_operations,
            "total_time": total_time,
            "average_time": total_time / total_operations,
            "total_memory_leaked": total_memory_leaked,
            "slowest_operation": {
                "name": slowest_operation["operation"],
                "duration": slowest_operation["duration"],
            },
            "most_memory_intensive": {
                "name": most_memory_intensive["operation"],
                "memory_delta": most_memory_intensive["memory_delta"],
            },
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0


# Export all performance monitoring components
__all__ = [
    "PerformanceMetrics",
    "PerformanceThresholds",
    "PerformanceRecommendation",
    "PerformanceAnalyzer",
    "PerformanceMonitor",
    "PerformanceProfiler",
    "performance_context",
]
