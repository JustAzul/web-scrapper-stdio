from src.scraper.domain.value_objects.refactored_scraping_config import RefactoredScrapingConfig
from src.scraper.domain.value_objects.output_config import OutputConfig
from src.scraper.domain.value_objects.timeout_config import TimeoutConfig
from src.scraper.domain.value_objects.browser_config import BrowserConfig
from src.scraper.domain.value_objects.processing_config import ProcessingConfig
from src.output_format_handler import OutputFormat
from src.scraper.domain.value_objects.value_objects import TimeoutValue
import pytest

def test_refactored_scraping_config_creation_and_properties():
    output_config = OutputConfig(format=OutputFormat.HTML, max_length=123)
    timeout_config = TimeoutConfig(page_timeout=TimeoutValue(42), grace_period=TimeoutValue(3))
    browser_config = BrowserConfig(user_agent="ua", wait_for_network_idle=False)
    processing_config = ProcessingConfig(custom_elements_to_remove=[".ads"], click_selector="#btn")
    config = RefactoredScrapingConfig(
        url="https://example.com",
        output_config=output_config,
        timeout_config=timeout_config,
        browser_config=browser_config,
        processing_config=processing_config
    )
    assert config.url == "https://example.com"
    assert config.output_format == OutputFormat.HTML
    assert config.max_length == 123
    assert config.timeout.seconds == 42
    assert config.grace_period.seconds == 3
    assert config.user_agent == "ua"
    assert config.wait_for_network_idle is False
    assert config.click_selector == "#btn"
    assert ".ads" in config.custom_elements_to_remove

def test_refactored_scraping_config_defaults():
    config = RefactoredScrapingConfig(url="https://site.com")
    assert config.url == "https://site.com"
    assert config.output_format == OutputFormat.MARKDOWN
    assert config.max_length is None
    assert config.timeout.seconds > 0
    assert config.grace_period.seconds > 0
    assert config.user_agent is None
    assert config.wait_for_network_idle is True
    assert config.click_selector is None
    assert config.custom_elements_to_remove == []

def test_refactored_scraping_config_invalid_url():
    with pytest.raises(ValueError):
        RefactoredScrapingConfig(url="not-a-url")
