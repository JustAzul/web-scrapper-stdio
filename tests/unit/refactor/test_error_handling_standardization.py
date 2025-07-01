"""
Tests for Error Handling Standardization (T014).

This module tests the comprehensive exception hierarchy and error handling patterns.
Follows TDD methodology with comprehensive coverage.
"""

import pytest

from src.scraper.domain.exceptions import (
    BrowserError,
    CloudflareBlockError,
    ConfigurationError,
    ContentExtractionError,
    ContentValidationError,
    MemoryError,
    NavigationError,
    NetworkError,
    ParsingError,
    RateLimitError,
    ResourceError,
    ScraperError,
    TimeoutError,
    URLValidationError,
    ValidationError,
    get_retry_delay,
    is_recoverable_error,
    wrap_exception,
)


class TestScraperErrorBase:
    """Test the base ScraperError class."""

    def test_scraper_error_basic_creation(self):
        """Test basic ScraperError creation with minimal parameters."""
        error = ScraperError(message="Test error", error_code="TEST_ERROR")

        assert str(error) == "[TEST_ERROR] Test error"
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.context == {}
        assert error.recoverable is False
        assert error.retry_after is None
        assert error.original_exception is None

    def test_scraper_error_full_creation(self):
        """Test ScraperError creation with all parameters."""
        original_ex = ValueError("Original error")
        context = {"url": "https://example.com", "attempt": 1}

        error = ScraperError(
            message="Full test error",
            error_code="FULL_ERROR",
            context=context,
            recoverable=True,
            retry_after=5.0,
            original_exception=original_ex,
        )

        assert error.message == "Full test error"
        assert error.error_code == "FULL_ERROR"
        assert error.context == context
        assert error.recoverable is True
        assert error.retry_after == 5.0
        assert error.original_exception == original_ex

    def test_scraper_error_to_dict(self):
        """Test ScraperError serialization to dictionary."""
        original_ex = RuntimeError("Runtime issue")
        context = {"key": "value"}

        error = ScraperError(
            message="Serialization test",
            error_code="SERIALIZE_ERROR",
            context=context,
            recoverable=True,
            retry_after=10.0,
            original_exception=original_ex,
        )

        result = error.to_dict()
        expected = {
            "error_code": "SERIALIZE_ERROR",
            "message": "Serialization test",
            "context": context,
            "recoverable": True,
            "retry_after": 10.0,
            "original_exception": "Runtime issue",
        }

        assert result == expected

    def test_scraper_error_to_dict_no_original_exception(self):
        """Test ScraperError serialization without original exception."""
        error = ScraperError(message="No original", error_code="NO_ORIG")

        result = error.to_dict()
        assert result["original_exception"] is None


class TestNavigationErrors:
    """Test navigation-related errors."""

    def test_navigation_error_creation(self):
        """Test NavigationError creation and properties."""
        url = "https://example.com/test"
        message = "Connection refused"

        error = NavigationError(url, message)

        assert error.error_code == "NAV_FAILED"
        assert error.recoverable is True
        assert error.context["url"] == url
        assert message in str(error)
        assert url in str(error)

    def test_timeout_error_creation(self):
        """Test TimeoutError creation and retry calculation."""
        operation = "page_load"
        timeout = 30.0

        error = TimeoutError(operation, timeout)

        assert error.error_code == "TIMEOUT"
        assert error.recoverable is True
        assert error.retry_after == timeout * 1.5  # 45.0
        assert error.context["operation"] == operation
        assert error.context["timeout"] == timeout

    def test_browser_error_creation(self):
        """Test BrowserError creation."""
        message = "Page crashed"
        browser_type = "chromium"

        error = BrowserError(message, browser_type)

        assert error.error_code == "BROWSER_ERROR"
        assert error.recoverable is False
        assert error.context["browser_type"] == browser_type
        assert browser_type in str(error)


class TestContentErrors:
    """Test content processing errors."""

    def test_content_extraction_error(self):
        """Test ContentExtractionError creation."""
        url = "https://example.com"
        message = "No content found"
        extraction_type = "text"

        error = ContentExtractionError(message, url, extraction_type)

        assert error.error_code == "CONTENT_EXTRACTION_FAILED"
        assert error.recoverable is True
        assert error.context["url"] == url
        assert error.context["extraction_type"] == extraction_type

    def test_parsing_error(self):
        """Test ParsingError creation."""
        message = "Invalid HTML structure"
        parser = "beautifulsoup"

        error = ParsingError(message, parser)

        assert error.error_code == "PARSING_FAILED"
        assert error.recoverable is True
        assert error.context["parser"] == parser

    def test_content_validation_error(self):
        """Test ContentValidationError creation."""
        message = "Content too short"
        validation_rule = "min_length"

        error = ContentValidationError(message, validation_rule)

        assert error.error_code == "CONTENT_INVALID"
        assert error.recoverable is False
        assert error.context["validation_rule"] == validation_rule


class TestNetworkErrors:
    """Test network-related errors."""

    def test_network_error(self):
        """Test NetworkError creation."""
        message = "Connection timeout"
        status_code = 500

        error = NetworkError(message, status_code)

        assert error.error_code == "NETWORK_ERROR"
        assert error.recoverable is True
        assert error.retry_after == 5.0
        assert error.context["status_code"] == status_code

    def test_rate_limit_error(self):
        """Test RateLimitError creation."""
        domain = "example.com"
        retry_after = 120.0

        error = RateLimitError(domain, retry_after)

        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.recoverable is True
        assert error.retry_after == retry_after
        assert error.context["domain"] == domain

    def test_cloudflare_block_error(self):
        """Test CloudflareBlockError creation."""
        url = "https://protected.com"
        protection_type = "cloudflare"

        error = CloudflareBlockError(url, protection_type)

        assert error.error_code == "ACCESS_BLOCKED"
        assert error.recoverable is True
        assert error.retry_after == 30.0
        assert error.context["url"] == url
        assert error.context["protection_type"] == protection_type


class TestSystemErrors:
    """Test system and configuration errors."""

    def test_configuration_error(self):
        """Test ConfigurationError creation."""
        message = "Missing API key"
        config_key = "api_key"

        error = ConfigurationError(message, config_key)

        assert error.error_code == "CONFIG_ERROR"
        assert error.recoverable is False
        assert error.context["config_key"] == config_key

    def test_resource_error(self):
        """Test ResourceError creation."""
        resource_type = "disk_space"
        message = "Insufficient space"

        error = ResourceError(resource_type, message)

        assert error.error_code == "RESOURCE_EXHAUSTED"
        assert error.recoverable is True
        assert error.retry_after == 10.0
        assert error.context["resource_type"] == resource_type

    def test_memory_error(self):
        """Test MemoryError creation."""
        memory_usage_mb = 1024.5
        limit_mb = 512.0

        error = MemoryError(memory_usage_mb, limit_mb)

        assert error.error_code == "RESOURCE_EXHAUSTED"
        assert error.recoverable is True
        assert error.context["memory_usage_mb"] == memory_usage_mb
        assert error.context["limit_mb"] == limit_mb
        assert str(memory_usage_mb) in str(error)
        assert str(limit_mb) in str(error)


class TestValidationErrors:
    """Test validation-related errors."""

    def test_validation_error(self):
        """Test ValidationError creation."""
        field = "timeout"
        value = -5
        message = "Must be positive"

        error = ValidationError(field, value, message)

        assert error.error_code == "VALIDATION_ERROR"
        assert error.recoverable is False
        assert error.context["field"] == field
        assert error.context["value"] == str(value)

    def test_url_validation_error(self):
        """Test URLValidationError creation."""
        url = "invalid-url"
        reason = "Missing protocol"

        error = URLValidationError(url, reason)

        assert error.error_code == "VALIDATION_ERROR"
        assert error.recoverable is False
        assert error.context["field"] == "url"
        assert error.context["value"] == url


class TestUtilityFunctions:
    """Test utility functions for error handling."""

    def test_wrap_exception(self):
        """Test wrapping generic exceptions."""
        original = ValueError("Original error")
        error_code = "WRAPPED_ERROR"
        message = "Wrapped message"
        context = {"key": "value"}

        wrapped = wrap_exception(
            original_exception=original,
            error_code=error_code,
            message=message,
            context=context,
            recoverable=True,
        )

        assert isinstance(wrapped, ScraperError)
        assert wrapped.error_code == error_code
        assert wrapped.message == message
        assert wrapped.context == context
        assert wrapped.recoverable is True
        assert wrapped.original_exception == original

    def test_is_recoverable_error_scraper_error(self):
        """Test is_recoverable_error with ScraperError."""
        recoverable_error = ScraperError("Test", "TEST", recoverable=True)
        non_recoverable_error = ScraperError("Test", "TEST", recoverable=False)

        assert is_recoverable_error(recoverable_error) is True
        assert is_recoverable_error(non_recoverable_error) is False

    def test_is_recoverable_error_generic_exceptions(self):
        """Test is_recoverable_error with generic exceptions."""
        # Recoverable types
        assert is_recoverable_error(ConnectionError()) is True
        assert is_recoverable_error(OSError()) is True

        # Non-recoverable types
        assert is_recoverable_error(ValueError()) is False
        assert is_recoverable_error(TypeError()) is False

    def test_get_retry_delay_scraper_error(self):
        """Test get_retry_delay with ScraperError."""
        error_with_delay = ScraperError("Test", "TEST", retry_after=15.0)
        error_without_delay = ScraperError("Test", "TEST")

        assert get_retry_delay(error_with_delay) == 15.0
        assert get_retry_delay(error_without_delay) is None

    def test_get_retry_delay_generic_exceptions(self):
        """Test get_retry_delay with generic exceptions."""
        # Known types with default delays
        assert get_retry_delay(ConnectionError()) == 5.0
        assert get_retry_delay(OSError()) == 5.0

        # Unknown types
        assert get_retry_delay(ValueError()) is None
        assert get_retry_delay(TypeError()) is None


class TestErrorHierarchy:
    """Test the overall error hierarchy and inheritance."""

    def test_all_errors_inherit_from_scraper_error(self):
        """Test that all custom errors inherit from ScraperError."""
        error_classes = [
            NavigationError,
            TimeoutError,
            BrowserError,
            ContentExtractionError,
            ParsingError,
            ContentValidationError,
            NetworkError,
            RateLimitError,
            CloudflareBlockError,
            ConfigurationError,
            ResourceError,
            MemoryError,
            ValidationError,
            URLValidationError,
        ]

        for error_class in error_classes:
            assert issubclass(error_class, ScraperError)

    def test_memory_error_inherits_from_resource_error(self):
        """Test that MemoryError inherits from ResourceError."""
        assert issubclass(MemoryError, ResourceError)
        assert issubclass(MemoryError, ScraperError)

    def test_url_validation_error_inherits_from_validation_error(self):
        """Test that URLValidationError inherits from ValidationError."""
        assert issubclass(URLValidationError, ValidationError)
        assert issubclass(URLValidationError, ScraperError)


class TestErrorContext:
    """Test error context and metadata handling."""

    def test_error_context_preservation(self):
        """Test that error context is preserved through inheritance."""
        url = "https://example.com"
        message = "Test navigation"

        error = NavigationError(url, message)

        # Context should be accessible
        assert "url" in error.context
        assert error.context["url"] == url

        # Should be serializable
        serialized = error.to_dict()
        assert serialized["context"]["url"] == url

    def test_error_chaining(self):
        """Test error chaining with original exceptions."""
        original = ConnectionError("Network issue")
        wrapped = wrap_exception(
            original_exception=original,
            error_code="NETWORK_FAIL",
            message="Failed to connect",
            context={"attempt": 3},
        )

        assert wrapped.original_exception == original
        assert wrapped.context["attempt"] == 3

        # Should be preserved in serialization
        serialized = wrapped.to_dict()
        assert "Network issue" in serialized["original_exception"]


# Integration tests
class TestErrorHandlingIntegration:
    """Test error handling in realistic scenarios."""

    def test_error_handling_workflow(self):
        """Test a complete error handling workflow."""
        # Simulate a network error that should be retried
        network_error = NetworkError("Connection timeout", status_code=503)

        # Check if it's recoverable
        assert is_recoverable_error(network_error) is True

        # Get retry delay
        retry_delay = get_retry_delay(network_error)
        assert retry_delay == 5.0

        # Serialize for logging
        error_dict = network_error.to_dict()
        assert error_dict["recoverable"] is True
        assert error_dict["retry_after"] == 5.0

    def test_non_recoverable_error_workflow(self):
        """Test workflow for non-recoverable errors."""
        # Simulate a configuration error
        config_error = ConfigurationError("Missing API key", "api_key")

        # Should not be recoverable
        assert is_recoverable_error(config_error) is False

        # Should not have retry delay
        retry_delay = get_retry_delay(config_error)
        assert retry_delay is None

        # Should be marked as non-recoverable in serialization
        error_dict = config_error.to_dict()
        assert error_dict["recoverable"] is False


if __name__ == "__main__":
    pytest.main([__file__])
