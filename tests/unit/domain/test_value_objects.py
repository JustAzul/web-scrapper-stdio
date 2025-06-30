"""
Tests for value objects that replace primitive obsession.

These value objects provide type safety, validation, and encapsulation
for commonly used primitive values throughout the scraper.
"""

import pytest

from src.output_format_handler import OutputFormat
from src.scraper.domain.value_objects.value_objects import (
    MemorySize,
    ScrapingConfig,
    TimeoutValue,
)


class TestTimeoutValue:
    """Test timeout value object with proper validation and conversion."""

    def test_timeout_creation_with_seconds(self):
        """Test creating timeout with seconds."""
        timeout = TimeoutValue(30)
        assert timeout.seconds == 30
        assert timeout.milliseconds == 30000

    def test_timeout_creation_from_milliseconds(self):
        """Test creating timeout from milliseconds."""
        timeout = TimeoutValue.from_milliseconds(5000)
        assert timeout.seconds == 5
        assert timeout.milliseconds == 5000

    def test_timeout_validation_positive_values(self):
        """Test that timeout validates positive values."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            TimeoutValue(0)

        with pytest.raises(ValueError, match="Timeout must be positive"):
            TimeoutValue(-5)

    def test_timeout_validation_maximum_values(self):
        """Test that timeout validates maximum reasonable values."""
        with pytest.raises(ValueError, match="Timeout too large"):
            TimeoutValue(300)  # 5 minutes should be max

    def test_timeout_string_representation(self):
        """Test timeout string representation."""
        timeout = TimeoutValue(30)
        assert str(timeout) == "30s"

    def test_timeout_comparison(self):
        """Test timeout comparison operations."""
        timeout1 = TimeoutValue(30)
        timeout2 = TimeoutValue(60)
        timeout3 = TimeoutValue(30)

        assert timeout1 < timeout2
        assert timeout1 == timeout3
        assert timeout2 > timeout1


class TestMemorySize:
    """Test memory size value object with automatic unit conversion."""

    def test_memory_size_creation_mb(self):
        """Test creating memory size in MB."""
        memory = MemorySize(100)  # 100 MB
        assert memory.megabytes == 100
        assert memory.bytes == 100 * 1024 * 1024

    def test_memory_size_creation_from_bytes(self):
        """Test creating memory size from bytes."""
        memory = MemorySize.from_bytes(1024 * 1024)  # 1 MB in bytes
        assert memory.megabytes == 1
        assert memory.bytes == 1024 * 1024

    def test_memory_size_creation_from_kb(self):
        """Test creating memory size from kilobytes."""
        memory = MemorySize.from_kilobytes(1024)  # 1024 KB = 1 MB
        assert memory.megabytes == 1
        assert memory.kilobytes == 1024

    def test_memory_size_validation(self):
        """Test memory size validation."""
        with pytest.raises(ValueError, match="Memory size must be positive"):
            MemorySize(0)

        with pytest.raises(ValueError, match="Memory size must be positive"):
            MemorySize(-10)

    def test_memory_size_string_representation(self):
        """Test memory size string representation."""
        memory = MemorySize(100)
        assert str(memory) == "100MB"

    def test_memory_size_comparison(self):
        """Test memory size comparison operations."""
        mem1 = MemorySize(100)
        mem2 = MemorySize(200)
        mem3 = MemorySize(100)

        assert mem1 < mem2
        assert mem1 == mem3
        assert mem2 > mem1

    def test_memory_size_arithmetic(self):
        """Test memory size arithmetic operations."""
        mem1 = MemorySize(100)
        mem2 = MemorySize(50)

        result = mem1 + mem2
        assert result.megabytes == 150

        result = mem1 - mem2
        assert result.megabytes == 50


class TestScrapingConfig:
    """Test scraping configuration object that replaces long parameter lists."""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values."""
        config = ScrapingConfig(url="https://example.com")

        assert config.url == "https://example.com"
        assert config.timeout.seconds == 30  # Default timeout
        assert config.grace_period.seconds == 2.0  # Default grace period
        assert config.output_format == OutputFormat.MARKDOWN
        assert config.wait_for_network_idle is True
        assert config.max_length is None
        assert config.user_agent is None
        assert config.click_selector is None
        assert config.custom_elements_to_remove == []

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = ScrapingConfig(
            url="https://test.com",
            timeout=TimeoutValue(60),
            grace_period=TimeoutValue(5),
            output_format=OutputFormat.TEXT,
            wait_for_network_idle=False,
            max_length=1000,
            user_agent="Custom Agent",
            click_selector="#button",
            custom_elements_to_remove=["script", "style"],
        )

        assert config.url == "https://test.com"
        assert config.timeout.seconds == 60
        assert config.grace_period.seconds == 5
        assert config.output_format == OutputFormat.TEXT
        assert config.wait_for_network_idle is False
        assert config.max_length == 1000
        assert config.user_agent == "Custom Agent"
        assert config.click_selector == "#button"
        assert config.custom_elements_to_remove == ["script", "style"]

    def test_config_url_validation(self):
        """Test URL validation in config."""
        with pytest.raises(ValueError, match="URL is required"):
            ScrapingConfig(url="")

        with pytest.raises(ValueError, match="URL is required"):
            ScrapingConfig(url=None)

        with pytest.raises(ValueError, match="Invalid URL format"):
            ScrapingConfig(url="not-a-url")

    def test_config_max_length_validation(self):
        """Test max_length validation in config."""
        with pytest.raises(ValueError, match="max_length must be positive"):
            ScrapingConfig(url="https://example.com", max_length=0)

        with pytest.raises(ValueError, match="max_length must be positive"):
            ScrapingConfig(url="https://example.com", max_length=-100)

    def test_config_immutability(self):
        """Test that config objects are immutable."""
        config = ScrapingConfig(url="https://example.com")

        # Should not be able to modify after creation
        with pytest.raises(AttributeError):
            config.url = "https://other.com"

    def test_config_to_dict(self):
        """Test converting config to dictionary for backwards compatibility."""
        config = ScrapingConfig(
            url="https://example.com", timeout=TimeoutValue(45), max_length=500
        )

        config_dict = config.to_dict()

        assert config_dict["url"] == "https://example.com"
        assert config_dict["custom_timeout"] == 45
        assert config_dict["max_length"] == 500
        assert config_dict["grace_period_seconds"] == 2.0
        assert config_dict["output_format"] == OutputFormat.MARKDOWN

    def test_config_from_dict(self):
        """Test creating config from dictionary for backwards compatibility."""
        config_dict = {
            "url": "https://example.com",
            "custom_timeout": 45,
            "max_length": 500,
            "grace_period_seconds": 3.0,
            "output_format": OutputFormat.TEXT,
            "user_agent": "Test Agent",
        }

        config = ScrapingConfig.from_dict(config_dict)

        assert config.url == "https://example.com"
        assert config.timeout.seconds == 45
        assert config.max_length == 500
        assert config.grace_period.seconds == 3.0
        assert config.output_format == OutputFormat.TEXT
        assert config.user_agent == "Test Agent"
