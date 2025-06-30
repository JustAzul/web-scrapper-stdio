"""
BrowserConfig - Single Responsibility: Browser behavior configuration

Extracted from ScrapingConfig to follow SRP principle.
This class is responsible only for browser-related configuration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BrowserConfig:
    """
    Configuration for browser behavior.

    Single Responsibility: Handles all browser-related configuration.
    """

    user_agent: Optional[str] = None
    wait_for_network_idle: bool = True

    @property
    def has_custom_user_agent(self) -> bool:
        """Check if custom user agent is set."""
        return self.user_agent is not None and self.user_agent.strip() != ""

    @property
    def should_wait_for_network(self) -> bool:
        """Check if should wait for network idle."""
        return self.wait_for_network_idle

    def with_user_agent(self, user_agent: Optional[str]) -> "BrowserConfig":
        """Create new BrowserConfig with different user agent."""
        return BrowserConfig(
            user_agent=user_agent, wait_for_network_idle=self.wait_for_network_idle
        )

    def with_network_wait(self, wait: bool) -> "BrowserConfig":
        """Create new BrowserConfig with different network wait setting."""
        return BrowserConfig(user_agent=self.user_agent, wait_for_network_idle=wait)

    def get_effective_user_agent(self, default_user_agent: str) -> str:
        """Get effective user agent (custom or default)."""
        return self.user_agent if self.has_custom_user_agent else default_user_agent

    def __str__(self) -> str:
        """String representation."""
        ua_str = (
            f"user_agent='{self.user_agent}'" if self.user_agent else "user_agent=None"
        )
        return f"BrowserConfig({ua_str}, wait_network={self.wait_for_network_idle})"
