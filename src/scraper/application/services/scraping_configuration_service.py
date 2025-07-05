"""Scraping Configuration Service for managing browser and scraping configuration.

This service implements the Single Responsibility Principle by focusing solely on
configuration management tasks, extracted from the large extract_text_from_url function.
"""

import random
import secrets
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from src.core.constants import (
    DEFAULT_ACCEPT_LANGUAGES,
    DEFAULT_BROWSER_VIEWPORTS,
    DEFAULT_ELEMENTS_TO_REMOVE,
    DEFAULT_USER_AGENTS,
)
from src.logger import get_logger
from src.scraper.application.contracts.browser_automation import BrowserConfiguration
from src.settings import DEFAULT_TIMEOUT_SECONDS

logger = get_logger(__name__)


class ScrapingConfigurationService:
    """
    Service responsible for managing scraping and browser configuration.

    Responsibilities:
    - Generate browser configurations
    - Manage elements to remove from HTML
    - Handle timeout configuration
    - URL validation
    - Grace period management

    This follows SRP by focusing only on configuration concerns.
    """

    def __init__(self):
        """Initialize the scraping configuration service."""
        pass

    def get_browser_config(
        self,
        custom_user_agent: Optional[str] = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> BrowserConfiguration:
        """
        Generate browser configuration with randomization or custom values.

        Args:
            custom_user_agent: Custom User-Agent string or None for random
            timeout_seconds: Browser timeout in seconds

        Returns:
            BrowserConfiguration object with all necessary browser settings
        """
        # Use custom user agent or select random one
        user_agent = self._get_user_agent(custom_user_agent)

        # Always randomize viewport and language for better scraping disguise
        viewport = random.choice(DEFAULT_BROWSER_VIEWPORTS)  # nosec B311
        accept_language = random.choice(DEFAULT_ACCEPT_LANGUAGES)  # nosec B311

        return BrowserConfiguration(
            user_agent=user_agent,
            viewport=viewport,
            accept_language=accept_language,
            timeout_seconds=timeout_seconds,
        )

    def _get_user_agent(self, custom_user_agent: Optional[str] = None) -> str:
        """Obtém user agent configurado ou aleatório"""
        # Use secure random generation for user agent selection
        secure_random = secrets.SystemRandom()
        user_agent = (
            custom_user_agent
            if custom_user_agent
            else secure_random.choice(DEFAULT_USER_AGENTS)
        )  # Using secure random instead of weak random
        logger.debug(f"User agent configurado: {user_agent[:50]}...")
        return user_agent

    def get_elements_to_remove(self, custom_elements: Optional[List[str]]) -> List[str]:
        """
        Get the complete list of elements to remove from HTML.

        Args:
            custom_elements: Additional elements to remove, or None

        Returns:
            List of HTML element tags to remove during processing
        """
        # Start with default elements and create a copy to avoid mutation
        elements_to_remove = DEFAULT_ELEMENTS_TO_REMOVE.copy()

        # Add custom elements if provided
        if custom_elements:
            elements_to_remove.extend(custom_elements)

        return elements_to_remove

    def get_timeout(self, custom_timeout: Optional[int]) -> int:
        """
        Get timeout value, using custom or default.

        Args:
            custom_timeout: Custom timeout in seconds or None for default

        Returns:
            Timeout value in seconds
        """
        return custom_timeout if custom_timeout is not None else DEFAULT_TIMEOUT_SECONDS

    def get_grace_period(self, custom_grace_period: Optional[float] = None) -> float:
        """
        Get grace period for waiting after navigation.

        Args:
            custom_grace_period: Custom grace period or None for default

        Returns:
            Grace period in seconds
        """
        return custom_grace_period if custom_grace_period is not None else 2.0

    def validate_url(self, url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format and structure.

        Args:
            url: URL string to validate

        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if URL is valid
        """
        if not url:
            return False, "URL cannot be empty or None"

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format - missing scheme or domain"

            if parsed.scheme not in ["http", "https"]:
                return False, "URL must use HTTP or HTTPS protocol"

            return True, None
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"

    def get_scraping_config(
        self,
        custom_user_agent: Optional[str] = None,
        custom_timeout: Optional[int] = None,
        custom_elements_to_remove: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive scraping configuration.

        Args:
            custom_user_agent: Custom User-Agent string
            custom_timeout: Custom timeout in seconds
            custom_elements_to_remove: Additional elements to remove

        Returns:
            Dictionary containing all configuration settings
        """
        timeout_seconds = self.get_timeout(custom_timeout=custom_timeout)

        return {
            "browser_config": self.get_browser_config(
                custom_user_agent=custom_user_agent, timeout_seconds=timeout_seconds
            ),
            "elements_to_remove": self.get_elements_to_remove(
                custom_elements=custom_elements_to_remove
            ),
            "timeout_seconds": timeout_seconds,
        }
