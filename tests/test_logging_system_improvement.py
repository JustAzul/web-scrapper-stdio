"""
Test suite for T007-TDD: Logging System Improvement.

This module tests the replacement of print statements with proper logging
in test files, ensuring structured logging with appropriate levels and formatting.

TDD Approach:
1. RED: Write failing tests for logging requirements
2. GREEN: Implement minimum logging improvements
3. REFACTOR: Optimize logging structure and performance
"""

import logging
import sys
from unittest.mock import patch

import pytest

from src.logger import Logger


class TestLoggingSystemImprovement:
    """Test cases for logging system improvement (T007-TDD)."""

    def test_logger_initialization(self):
        """Test Logger class initializes correctly with proper configuration."""
        logger = Logger("test_logger")

        assert logger.logger.name == "test_logger"
        assert logger.logger.hasHandlers()
        assert len(logger.logger.handlers) >= 1

        # Verify handler configuration
        handler = logger.logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stderr

    def test_logger_formatting(self, caplog):
        """Test Logger uses proper formatting for messages."""
        logger = Logger("test_formatter")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # Verify log was captured
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert record.name == "test_formatter"
        assert record.message == "Test message"

    def test_logger_log_levels(self, caplog):
        """Test Logger supports all required log levels."""
        logger = Logger("test_levels")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        # Should capture all levels when set to DEBUG
        assert (
            len(caplog.records) >= 3
        )  # INFO, WARNING, ERROR (DEBUG may not appear if level is INFO)

        # Find records by level
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]

        assert len(info_records) >= 1
        assert len(warning_records) >= 1
        assert len(error_records) >= 1

        assert info_records[0].message == "Info message"
        assert warning_records[0].message == "Warning message"
        assert error_records[0].message == "Error message"

    def test_debug_logs_environment_control(self):
        """Test debug logging can be controlled via environment variables."""
        # Test with debug disabled
        with patch.dict("os.environ", {"DEBUG_LOGS_ENABLED": "false"}):
            logger = Logger("test_debug_disabled")
            assert logger.logger.level == logging.INFO

        # Test with debug enabled
        with patch.dict("os.environ", {"DEBUG_LOGS_ENABLED": "true"}):
            logger = Logger("test_debug_enabled")
            assert logger.logger.level == logging.DEBUG

    def test_print_statement_replacement_structure(self, caplog):
        """Test that print statements are systematically replaced with logging."""
        logger = Logger("test_replacement")

        with caplog.at_level(logging.INFO):
            # Simulate the replacement pattern
            config_types = ["image", "stylesheet", "font"]

            # New logging approach (what we want)
            logger.info("Configured scraper with resource blocking: %s", config_types)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert "Configured scraper with resource blocking" in record.message
        assert "image" in record.message
        assert "stylesheet" in record.message

    def test_test_output_logging_levels(self, caplog):
        """Test proper log levels for different types of test output."""
        logger = Logger("test_output_levels")

        with caplog.at_level(logging.INFO):
            # Test scenario: Starting a test (INFO level)
            logger.info("Starting Intelligent Fallback System Demo")

            # Test scenario: Test progress (INFO level)
            logger.info(
                "Configured scraper with resource blocking: %s", ["image", "stylesheet"]
            )

            # Test scenario: Simulation/mocking (INFO level)
            logger.info("Simulating 'Page crashed' error in Playwright...")

            # Test scenario: Success verification (INFO level)
            logger.info(
                "Fallback succeeded! Strategy: %s, Attempts: %d", "requests_fallback", 2
            )

            # Test scenario: Performance metrics (INFO level)
            logger.info("Performance acceptable: %.2fs", 1.23)

            # Test scenario: Final validation (INFO level)
            logger.info("SOLUTION VALIDATED: No more 'Page crashed' test failures")

        # All should be INFO level for test output
        assert len(caplog.records) == 6
        for record in caplog.records:
            assert record.levelname == "INFO"

    def test_logging_performance_impact(self):
        """Test that logging doesn't significantly impact test performance."""
        import time

        logger = Logger("test_performance")

        # Measure time for logging vs print
        start_time = time.time()
        for i in range(100):
            logger.info("Performance test message %d", i)
        logging_time = time.time() - start_time

        # Logging should complete quickly (under 1 second for 100 messages)
        assert logging_time < 1.0

    def test_structured_logging_format(self, caplog):
        """Test structured logging format for better parsing and analysis."""
        logger = Logger("test_structured")

        with caplog.at_level(logging.INFO):
            # Test structured logging with context
            logger.info(
                "Test completed successfully",
                extra={
                    "test_name": "test_fallback_system",
                    "duration": 1.23,
                    "status": "success",
                },
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert "Test completed successfully" in record.message

    def test_log_capture_in_tests(self, caplog):
        """Test that logs can be captured and verified in tests."""
        logger = Logger("test_capture")

        with caplog.at_level(logging.WARNING):
            logger.warning("This is a test warning")
            logger.error("This is a test error")

        assert len(caplog.records) == 2

        warning_record = caplog.records[0]
        error_record = caplog.records[1]

        assert warning_record.levelname == "WARNING"
        assert warning_record.message == "This is a test warning"
        assert error_record.levelname == "ERROR"
        assert error_record.message == "This is a test error"

    def test_backward_compatibility(self):
        """Test that existing Logger class maintains backward compatibility."""
        logger = Logger("test_compatibility")

        # Test that all existing methods still work
        assert hasattr(logger, "log")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

        # Test that methods are callable
        assert callable(logger.log)
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)

    def test_no_duplicate_handlers(self):
        """Test that creating multiple Logger instances doesn't create duplicate handlers."""
        logger1 = Logger("test_duplicate1")
        logger2 = Logger("test_duplicate1")  # Same name

        # Should not create duplicate handlers for same logger name
        assert len(logger1.logger.handlers) == len(logger2.logger.handlers)
        assert logger1.logger is logger2.logger  # Should be same logger instance

    @pytest.mark.parametrize(
        "log_level,expected_method",
        [
            ("debug", "debug"),
            ("info", "info"),
            ("warning", "warning"),
            ("error", "error"),
        ],
    )
    def test_log_level_methods(self, log_level, expected_method, caplog):
        """Test each log level method works correctly."""
        logger = Logger("test_parametrized")

        method = getattr(logger, expected_method)
        assert callable(method)

        with caplog.at_level(logging.DEBUG):
            method(f"Test {log_level} message")

        # Should have captured the log if level is enabled
        if logger.logger.isEnabledFor(getattr(logging, log_level.upper())):
            matching_records = [
                r for r in caplog.records if f"Test {log_level} message" in r.message
            ]
            assert len(matching_records) >= 1


class TestPrintStatementReplacement:
    """Test specific print statement replacement scenarios."""

    def test_emoji_logging_support(self, caplog):
        """Test that logging properly handles emoji characters in messages."""
        logger = Logger("test_emoji")

        with caplog.at_level(logging.INFO):
            logger.info("🚀 Starting test with emoji")
            logger.info("✅ Success with checkmark")
            logger.info("🎯 Target achieved")

        assert len(caplog.records) == 3
        assert "🚀 Starting test with emoji" in caplog.records[0].message
        assert "✅ Success with checkmark" in caplog.records[1].message
        assert "🎯 Target achieved" in caplog.records[2].message

    def test_formatted_string_logging(self, caplog):
        """Test proper replacement of f-string print statements."""
        logger = Logger("test_fstring")

        strategy = "requests_fallback"
        attempts = 2
        content_length = 1234
        processing_time = 1.23

        with caplog.at_level(logging.INFO):
            # Replace: print(f"Strategy used: {result.strategy_used}")
            logger.info("Strategy used: %s", strategy)

            # Replace: print(f"Attempts made: {result.attempts}")
            logger.info("Attempts made: %d", attempts)

            # Replace: print(f"Content length: {len(result.content)} characters")
            logger.info("Content length: %d characters", content_length)

            # Replace: print(f"Processing time: {result.performance_metrics['total_time']:.2f}s")
            logger.info("Processing time: %.2fs", processing_time)

        assert len(caplog.records) == 4
        assert "Strategy used: requests_fallback" in caplog.records[0].message
        assert "Attempts made: 2" in caplog.records[1].message
        assert "Content length: 1234 characters" in caplog.records[2].message
        assert "Processing time: 1.23s" in caplog.records[3].message

    def test_multiline_logging_replacement(self, caplog):
        """Test replacement of multiline print statements."""
        logger = Logger("test_multiline")

        with caplog.at_level(logging.INFO):
            # Replace multiline prints with structured logging
            logger.info("SOLUTION VALIDATED:")
            logger.info("  ✅ No more 'Page crashed' test failures")
            logger.info("  ✅ Robust fallback to HTTP requests")
            logger.info("  ✅ Performance optimized with resource blocking")
            logger.info("  ✅ Circuit breaker prevents repeated failures")
            logger.info("  ✅ Content cleaning maintains quality")

        assert len(caplog.records) == 6
        assert "SOLUTION VALIDATED:" in caplog.records[0].message
        assert "No more 'Page crashed' test failures" in caplog.records[1].message
        assert "Robust fallback to HTTP requests" in caplog.records[2].message
        assert (
            "Performance optimized with resource blocking" in caplog.records[3].message
        )
        assert "Circuit breaker prevents repeated failures" in caplog.records[4].message
        assert "Content cleaning maintains quality" in caplog.records[5].message
