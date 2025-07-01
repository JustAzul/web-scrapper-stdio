"""
TDD Tests for T009 - ScrapingConfig SRP Refactoring
Tests for breaking ScrapingConfig into specialized classes following SRP
"""

import pytest

from src.output_format_handler import OutputFormat


class TestURLConfig:
    """TDD Tests for URLConfig - Single responsibility: URL validation and normalization"""

    def test_url_config_creation_with_valid_url(self):
        """Test creating URLConfig with valid URL"""
        # This test will fail initially (RED phase)
        from src.scraper.domain.value_objects.url_config import URLConfig

        config = URLConfig("https://example.com")
        assert config.url == "https://example.com"
        assert config.normalized_url == "https://example.com"
        assert config.is_valid is True

    def test_url_config_creation_with_invalid_url(self):
        """Test URLConfig validation with invalid URL"""
        from src.scraper.domain.value_objects.url_config import URLConfig

        with pytest.raises(ValueError, match="Invalid URL format"):
            URLConfig("not-a-url")

    def test_url_config_creation_with_empty_url(self):
        """Test URLConfig validation with empty URL"""
        from src.scraper.domain.value_objects.url_config import URLConfig

        with pytest.raises(ValueError, match="URL is required"):
            URLConfig("")

    def test_url_config_normalization(self):
        """Test URL normalization functionality"""
        from src.scraper.domain.value_objects.url_config import URLConfig

        config = URLConfig("HTTPS://EXAMPLE.COM/PATH")
        assert config.normalized_url == "https://example.com/PATH"

    def test_url_config_immutability(self):
        """Test that URLConfig is immutable"""
        from src.scraper.domain.value_objects.url_config import URLConfig

        config = URLConfig("https://example.com")
        with pytest.raises(AttributeError):
            config.url = "https://other.com"


class TestTimeoutConfig:
    """TDD Tests for TimeoutConfig - Single responsibility: Timeout management"""

    def test_timeout_config_creation_with_defaults(self):
        """Test creating TimeoutConfig with default values"""
        from src.scraper.domain.value_objects.timeout_config import TimeoutConfig

        config = TimeoutConfig()
        assert config.page_timeout.seconds == 30  # Default
        assert config.grace_period.seconds == 2.0  # Default

    def test_timeout_config_creation_with_custom_values(self):
        """Test creating TimeoutConfig with custom values"""
        from src.scraper.domain.value_objects.timeout_config import TimeoutConfig
        from src.scraper.domain.value_objects.value_objects import TimeoutValue

        config = TimeoutConfig(
            page_timeout=TimeoutValue(60), grace_period=TimeoutValue(5.0)
        )
        assert config.page_timeout.seconds == 60
        assert config.grace_period.seconds == 5.0

    def test_timeout_config_validation(self):
        """Test TimeoutConfig validation"""
        from src.scraper.domain.value_objects.timeout_config import TimeoutConfig
        from src.scraper.domain.value_objects.value_objects import TimeoutValue

        with pytest.raises(ValueError):
            TimeoutConfig(page_timeout=TimeoutValue(-1))

    def test_timeout_config_immutability(self):
        """Test that TimeoutConfig is immutable"""
        from src.scraper.domain.value_objects.timeout_config import TimeoutConfig

        config = TimeoutConfig()
        with pytest.raises(AttributeError):
            config.page_timeout = None


class TestOutputConfig:
    """TDD Tests for OutputConfig - Single responsibility: Output formatting configuration"""

    def test_output_config_creation_with_defaults(self):
        """Test creating OutputConfig with default values"""
        from src.scraper.domain.value_objects.output_config import OutputConfig

        config = OutputConfig()
        assert config.format == OutputFormat.MARKDOWN
        assert config.max_length is None

    def test_output_config_creation_with_custom_values(self):
        """Test creating OutputConfig with custom values"""
        from src.scraper.domain.value_objects.output_config import OutputConfig

        config = OutputConfig(format=OutputFormat.TEXT, max_length=1000)
        assert config.format == OutputFormat.TEXT
        assert config.max_length == 1000

    def test_output_config_max_length_validation(self):
        """Test OutputConfig max_length validation"""
        from src.scraper.domain.value_objects.output_config import OutputConfig

        with pytest.raises(ValueError, match="max_length must be positive"):
            OutputConfig(max_length=0)

        with pytest.raises(ValueError, match="max_length must be positive"):
            OutputConfig(max_length=-100)

    def test_output_config_immutability(self):
        """Test that OutputConfig is immutable"""
        from src.scraper.domain.value_objects.output_config import OutputConfig

        config = OutputConfig()
        with pytest.raises(AttributeError):
            config.format = OutputFormat.TEXT


class TestBrowserConfig:
    """TDD Tests for BrowserConfig - Single responsibility: Browser behavior configuration"""

    def test_browser_config_creation_with_defaults(self):
        """Test creating BrowserConfig with default values"""
        from src.scraper.domain.value_objects.browser_config import BrowserConfig

        config = BrowserConfig()
        assert config.user_agent is None
        assert config.wait_for_network_idle is True

    def test_browser_config_creation_with_custom_values(self):
        """Test creating BrowserConfig with custom values"""
        from src.scraper.domain.value_objects.browser_config import BrowserConfig

        config = BrowserConfig(user_agent="Custom Agent", wait_for_network_idle=False)
        assert config.user_agent == "Custom Agent"
        assert config.wait_for_network_idle is False

    def test_browser_config_immutability(self):
        """Test that BrowserConfig is immutable"""
        from src.scraper.domain.value_objects.browser_config import BrowserConfig

        config = BrowserConfig()
        with pytest.raises(AttributeError):
            config.user_agent = "Modified Agent"


class TestProcessingConfig:
    """TDD Tests for ProcessingConfig - Single responsibility: Content processing configuration"""

    def test_processing_config_creation_with_defaults(self):
        """Test creating ProcessingConfig with default values"""
        from src.scraper.domain.value_objects.processing_config import ProcessingConfig

        config = ProcessingConfig()
        assert config.custom_elements_to_remove == []
        assert config.click_selector is None

    def test_processing_config_creation_with_custom_values(self):
        """Test creating ProcessingConfig with custom values"""
        from src.scraper.domain.value_objects.processing_config import ProcessingConfig

        config = ProcessingConfig(
            custom_elements_to_remove=["script", "style"], click_selector="#button"
        )
        assert config.custom_elements_to_remove == ["script", "style"]
        assert config.click_selector == "#button"

    def test_processing_config_immutability(self):
        """Test that ProcessingConfig is immutable"""
        from src.scraper.domain.value_objects.processing_config import ProcessingConfig

        config = ProcessingConfig()
        with pytest.raises(AttributeError):
            config.click_selector = "#modified"


class TestRefactoredScrapingConfig:
    """TDD Tests for RefactoredScrapingConfig - Composition of specialized configs"""

    def test_refactored_config_creation_with_defaults(self):
        """Test creating RefactoredScrapingConfig with default values"""
        from src.scraper.domain.value_objects.refactored_scraping_config import (
            RefactoredScrapingConfig,
        )

        config = RefactoredScrapingConfig("https://example.com")
        assert config.url_config.url == "https://example.com"
        assert config.timeout_config.page_timeout.seconds == 30
        assert config.output_config.format == OutputFormat.MARKDOWN
        assert config.browser_config.wait_for_network_idle is True
        assert config.processing_config.custom_elements_to_remove == []

    def test_refactored_config_creation_with_custom_values(self):
        """Test creating RefactoredScrapingConfig with custom values"""
        from src.scraper.domain.value_objects.browser_config import BrowserConfig
        from src.scraper.domain.value_objects.output_config import OutputConfig
        from src.scraper.domain.value_objects.processing_config import ProcessingConfig
        from src.scraper.domain.value_objects.refactored_scraping_config import (
            RefactoredScrapingConfig,
        )
        from src.scraper.domain.value_objects.timeout_config import TimeoutConfig
        from src.scraper.domain.value_objects.value_objects import TimeoutValue

        config = RefactoredScrapingConfig(
            url="https://example.com",
            timeout_config=TimeoutConfig(
                page_timeout=TimeoutValue(60), grace_period=TimeoutValue(5.0)
            ),
            output_config=OutputConfig(format=OutputFormat.TEXT, max_length=1000),
            browser_config=BrowserConfig(
                user_agent="Custom Agent", wait_for_network_idle=False
            ),
            processing_config=ProcessingConfig(
                custom_elements_to_remove=["script", "style"], click_selector="#button"
            ),
        )

        assert config.url_config.url == "https://example.com"
        assert config.timeout_config.page_timeout.seconds == 60
        assert config.output_config.format == OutputFormat.TEXT
        assert config.browser_config.user_agent == "Custom Agent"
        assert config.processing_config.click_selector == "#button"

    def test_refactored_config_backward_compatibility_to_dict(self):
        """Test backward compatibility - to_dict method"""
        from src.scraper.domain.value_objects.refactored_scraping_config import (
            RefactoredScrapingConfig,
        )

        config = RefactoredScrapingConfig("https://example.com")
        config_dict = config.to_dict()

        assert config_dict["url"] == "https://example.com"
        assert config_dict["custom_timeout"] == 30
        assert config_dict["grace_period_seconds"] == 2.0
        assert config_dict["output_format"] == OutputFormat.MARKDOWN
        assert config_dict["wait_for_network_idle"] is True
        assert config_dict["max_length"] is None
        assert config_dict["user_agent"] is None
        assert config_dict["click_selector"] is None
        assert config_dict["custom_elements_to_remove"] == []

    def test_refactored_config_backward_compatibility_from_dict(self):
        """Test backward compatibility - from_dict method"""
        from src.scraper.domain.value_objects.refactored_scraping_config import (
            RefactoredScrapingConfig,
        )

        config_dict = {
            "url": "https://example.com",
            "custom_timeout": 45,
            "grace_period_seconds": 3.0,
            "output_format": OutputFormat.TEXT,
            "wait_for_network_idle": False,
            "max_length": 500,
            "user_agent": "Test Agent",
            "click_selector": "#button",
            "custom_elements_to_remove": ["script", "style"],
        }

        config = RefactoredScrapingConfig.from_dict(config_dict)

        assert config.url_config.url == "https://example.com"
        assert config.timeout_config.page_timeout.seconds == 45
        assert config.timeout_config.grace_period.seconds == 3.0
        assert config.output_config.format == OutputFormat.TEXT
        assert config.browser_config.wait_for_network_idle is False
        assert config.output_config.max_length == 500
        assert config.browser_config.user_agent == "Test Agent"
        assert config.processing_config.click_selector == "#button"
        assert config.processing_config.custom_elements_to_remove == ["script", "style"]

    def test_refactored_config_immutability(self):
        """Test that RefactoredScrapingConfig is immutable"""
        from src.scraper.domain.value_objects.refactored_scraping_config import (
            RefactoredScrapingConfig,
        )

        config = RefactoredScrapingConfig("https://example.com")
        with pytest.raises(AttributeError):
            config.url_config = None


class TestScrapingConfigBackwardCompatibility:
    """TDD Tests to ensure the original ScrapingConfig interface is preserved"""

    def test_original_scraping_config_still_works(self):
        """Test that original ScrapingConfig still works after refactoring"""
        from src.scraper.domain.value_objects.value_objects import ScrapingConfig

        config = ScrapingConfig(url="https://example.com")
        assert config.url == "https://example.com"
        assert config.timeout.seconds == 30

    def test_refactored_config_can_replace_original(self):
        """Test that RefactoredScrapingConfig can be used as drop-in replacement"""
        from src.scraper.domain.value_objects.refactored_scraping_config import (
            RefactoredScrapingConfig,
        )

        # Should have same interface as original
        config = RefactoredScrapingConfig("https://example.com")
        config_dict = config.to_dict()

        # Should produce same dict structure as original
        assert "url" in config_dict
        assert "custom_timeout" in config_dict
        assert "grace_period_seconds" in config_dict
        assert "output_format" in config_dict
