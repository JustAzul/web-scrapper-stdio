"""
RefactoredScrapingConfig - Composition of specialized config classes

This class follows the aggregation pattern to compose all specialized
configuration classes, replacing the monolithic ScrapingConfig.
Maintains backward compatibility while following SRP.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.core.constants import DEFAULT_TIMEOUT_SECONDS
from src.output_format_handler import OutputFormat
from src.scraper.domain.value_objects.value_objects import TimeoutValue

from .browser_config import BrowserConfig
from .output_config import OutputConfig
from .processing_config import ProcessingConfig
from .timeout_config import TimeoutConfig
from .url_config import URLConfig


@dataclass(frozen=True)
class RefactoredScrapingConfig:
    """
    Refactored scraping configuration using composition.

    Follows SRP by composing specialized configuration classes.
    Maintains backward compatibility with original ScrapingConfig.
    """

    url_config: URLConfig
    timeout_config: Optional[TimeoutConfig] = None
    output_config: Optional[OutputConfig] = None
    browser_config: Optional[BrowserConfig] = None
    processing_config: Optional[ProcessingConfig] = None

    def __init__(
        self,
        url: str,
        timeout_config: Optional[TimeoutConfig] = None,
        output_config: Optional[OutputConfig] = None,
        browser_config: Optional[BrowserConfig] = None,
        processing_config: Optional[ProcessingConfig] = None,
    ):
        """Initialize with URL and optional specialized configs."""
        # Create URL config (validates URL)
        object.__setattr__(self, "url_config", URLConfig(url))

        # Set defaults for optional configs
        object.__setattr__(self, "timeout_config", timeout_config or TimeoutConfig())
        object.__setattr__(self, "output_config", output_config or OutputConfig())
        object.__setattr__(self, "browser_config", browser_config or BrowserConfig())
        object.__setattr__(
            self, "processing_config", processing_config or ProcessingConfig()
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary for backward compatibility.

        Maintains the same structure as original ScrapingConfig.
        """
        return {
            "url": self.url_config.url,
            "custom_timeout": self.timeout_config.page_timeout.seconds,
            "grace_period_seconds": self.timeout_config.grace_period.seconds,
            "output_format": self.output_config.format,
            "wait_for_network_idle": self.browser_config.wait_for_network_idle,
            "max_length": self.output_config.max_length,
            "user_agent": self.browser_config.user_agent,
            "click_selector": self.processing_config.click_selector,
            "custom_elements_to_remove": (
                self.processing_config.custom_elements_to_remove
            ),
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RefactoredScrapingConfig":
        """
        Create config from dictionary for backward compatibility.

        Allows existing code to work with the new config structure.
        """
        # Extract URL
        url = config_dict["url"]

        # Create timeout config
        timeout_config = TimeoutConfig(
            page_timeout=TimeoutValue(config_dict.get("custom_timeout", DEFAULT_TIMEOUT_SECONDS)),
            grace_period=TimeoutValue(config_dict.get("grace_period_seconds", 2.0)),
        )

        # Create output config
        output_config = OutputConfig(
            format=config_dict.get("output_format", OutputFormat.MARKDOWN),
            max_length=config_dict.get("max_length"),
        )

        # Create browser config
        browser_config = BrowserConfig(
            user_agent=config_dict.get("user_agent"),
            wait_for_network_idle=config_dict.get("wait_for_network_idle", True),
        )

        # Create processing config
        processing_config = ProcessingConfig(
            custom_elements_to_remove=config_dict.get("custom_elements_to_remove", []),
            click_selector=config_dict.get("click_selector"),
        )

        return cls(
            url=url,
            timeout_config=timeout_config,
            output_config=output_config,
            browser_config=browser_config,
            processing_config=processing_config,
        )

    # Convenience properties for backward compatibility
    @property
    def url(self) -> str:
        """Get URL for backward compatibility."""
        return self.url_config.url

    @property
    def timeout(self) -> TimeoutValue:
        """Get timeout for backward compatibility."""
        return self.timeout_config.page_timeout

    @property
    def grace_period(self) -> TimeoutValue:
        """Get grace period for backward compatibility."""
        return self.timeout_config.grace_period

    @property
    def output_format(self) -> OutputFormat:
        """Get output format for backward compatibility."""
        return self.output_config.format

    @property
    def wait_for_network_idle(self) -> bool:
        """Get wait for network idle for backward compatibility."""
        return self.browser_config.wait_for_network_idle

    @property
    def max_length(self) -> Optional[int]:
        """Get max length for backward compatibility."""
        return self.output_config.max_length

    @property
    def user_agent(self) -> Optional[str]:
        """Get user agent for backward compatibility."""
        return self.browser_config.user_agent

    @property
    def click_selector(self) -> Optional[str]:
        """Get click selector for backward compatibility."""
        return self.processing_config.click_selector

    @property
    def custom_elements_to_remove(self) -> list:
        """Get custom elements to remove for backward compatibility."""
        return self.processing_config.custom_elements_to_remove

    def __str__(self) -> str:
        """String representation."""
        return f"RefactoredScrapingConfig(url='{self.url_config.url}')"
