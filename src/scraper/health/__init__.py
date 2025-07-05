"""
Health Checks Implementation for Web Scraper MCP.

This module implements comprehensive health monitoring and status checks
following T021 requirements.

TDD Implementation: GREEN phase - comprehensive health monitoring system.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric."""

    name: str
    status: HealthStatus
    value: Any
    threshold: Optional[Any] = None
    message: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": self.timestamp,
        }


@dataclass
class HealthReport:
    """Complete health assessment report."""

    overall_status: HealthStatus
    metrics: List[HealthMetric]
    timestamp: float = 0.0
    duration_ms: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "metrics": [metric.to_dict() for metric in self.metrics],
        }

    def get_metrics_by_status(self, status: HealthStatus) -> List[HealthMetric]:
        """Get metrics filtered by status."""
        return [metric for metric in self.metrics if metric.status == status]

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(metric.status == HealthStatus.CRITICAL for metric in self.metrics)


class SystemHealthChecker:
    """Monitors system-level health metrics."""

    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.logger = get_logger(__name__)

    async def check_health(self) -> List[HealthMetric]:
        """Check system health metrics."""
        metrics = []

        # CPU usage check
        cpu_metric = await self._check_cpu_usage()
        metrics.append(cpu_metric)

        # Memory usage check
        memory_metric = await self._check_memory_usage()
        metrics.append(memory_metric)

        return metrics

    async def _check_cpu_usage(self) -> HealthMetric:
        """Check CPU usage percentage."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)

            if cpu_percent >= self.cpu_threshold:
                status = HealthStatus.CRITICAL
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent >= self.cpu_threshold * 0.8:
                status = HealthStatus.WARNING
                message = f"Elevated CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"

            return HealthMetric(
                name="cpu_usage",
                status=status,
                value=cpu_percent,
                threshold=self.cpu_threshold,
                message=message,
            )
        except Exception as e:
            return HealthMetric(
                name="cpu_usage",
                status=HealthStatus.UNKNOWN,
                value=None,
                message=f"CPU check failed: {str(e)}",
            )

    async def _check_memory_usage(self) -> HealthMetric:
        """Check memory usage percentage."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            if memory_percent >= self.memory_threshold:
                status = HealthStatus.CRITICAL
                message = f"High memory usage: {memory_percent:.1f}%"
            elif memory_percent >= self.memory_threshold * 0.8:
                status = HealthStatus.WARNING
                message = f"Elevated memory usage: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_percent:.1f}%"

            return HealthMetric(
                name="memory_usage",
                status=status,
                value=memory_percent,
                threshold=self.memory_threshold,
                message=message,
            )
        except Exception as e:
            return HealthMetric(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                value=None,
                message=f"Memory check failed: {str(e)}",
            )


class HealthMonitor:
    """Main health monitoring facade."""

    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0):
        self.system_checker = SystemHealthChecker(cpu_threshold, memory_threshold)
        self.logger = get_logger(__name__)

    async def get_health_report(self) -> HealthReport:
        """Get comprehensive health report."""
        start_time = time.time()
        all_metrics = []

        try:
            # Gather all health metrics
            system_metrics = await self.system_checker.check_health()
            all_metrics.extend(system_metrics)

            # Determine overall status
            overall_status = self._determine_overall_status(all_metrics)

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            all_metrics.append(
                HealthMetric(
                    name="health_check_error",
                    status=HealthStatus.CRITICAL,
                    value=False,
                    message=f"Health check system error: {str(e)}",
                )
            )
            overall_status = HealthStatus.CRITICAL

        duration_ms = (time.time() - start_time) * 1000

        return HealthReport(
            overall_status=overall_status, metrics=all_metrics, duration_ms=duration_ms
        )

    def _determine_overall_status(self, metrics: List[HealthMetric]) -> HealthStatus:
        """Determine overall health status from individual metrics."""
        if any(metric.status == HealthStatus.CRITICAL for metric in metrics):
            return HealthStatus.CRITICAL
        elif any(metric.status == HealthStatus.WARNING for metric in metrics):
            return HealthStatus.WARNING
        elif any(metric.status == HealthStatus.UNKNOWN for metric in metrics):
            return HealthStatus.WARNING  # Treat unknown as warning
        else:
            return HealthStatus.HEALTHY

    async def is_healthy(self) -> bool:
        """Quick health check - returns True if system is healthy."""
        report = await self.get_health_report()
        return report.overall_status == HealthStatus.HEALTHY


# Export all health monitoring components
__all__ = [
    "HealthStatus",
    "HealthMonitor",
    "SystemHealthChecker",
    "HealthReport",
    "HealthMetric",
]
