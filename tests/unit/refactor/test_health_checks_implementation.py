"""
Test suite for T021: Health Checks Implementation.

TDD Implementation: RED-GREEN-REFACTOR cycle tests for health monitoring system.
"""

import pytest

from src.scraper.health import (
    HealthMetric,
    HealthMonitor,
    HealthReport,
    HealthStatus,
    SystemHealthChecker,
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test all health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestHealthMetric:
    """Test HealthMetric data structure."""

    def test_health_metric_creation(self):
        """Test basic health metric creation."""
        metric = HealthMetric(
            name="test_metric",
            status=HealthStatus.HEALTHY,
            value=50.0,
            threshold=80.0,
            message="Test metric is healthy",
        )

        assert metric.name == "test_metric"
        assert metric.status == HealthStatus.HEALTHY
        assert metric.value == 50.0
        assert metric.threshold == 80.0
        assert metric.message == "Test metric is healthy"
        assert metric.timestamp > 0


class TestHealthReport:
    """Test HealthReport aggregation and filtering."""

    def test_health_report_creation(self):
        """Test basic health report creation."""
        metrics = [
            HealthMetric("cpu", HealthStatus.HEALTHY, 50.0),
            HealthMetric("memory", HealthStatus.WARNING, 85.0),
        ]

        report = HealthReport(overall_status=HealthStatus.WARNING, metrics=metrics)

        assert report.overall_status == HealthStatus.WARNING
        assert len(report.metrics) == 2
        assert report.timestamp > 0


class TestSystemHealthChecker:
    """Test SystemHealthChecker functionality."""

    def test_system_health_checker_creation(self):
        """Test system health checker initialization."""
        checker = SystemHealthChecker(cpu_threshold=70.0, memory_threshold=85.0)

        assert checker.cpu_threshold == 70.0
        assert checker.memory_threshold == 85.0


class TestHealthMonitor:
    """Test HealthMonitor facade functionality."""

    def test_health_monitor_creation(self):
        """Test health monitor initialization."""
        monitor = HealthMonitor(cpu_threshold=70.0, memory_threshold=85.0)

        assert monitor.system_checker is not None
        assert monitor.system_checker.cpu_threshold == 70.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
