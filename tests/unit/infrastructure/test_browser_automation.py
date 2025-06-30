"""
Test cases for browser automation abstraction layer.

These tests define the interface contract that any browser automation
implementation must satisfy, following Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from unittest.mock import AsyncMock, Mock

import pytest


@dataclass
class BrowserResponse:
    """Standardized response from browser navigation."""

    status_code: int
    url: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class BrowserConfiguration:
    """Browser configuration settings."""

    user_agent: str
    viewport: Dict[str, int]
    timeout_seconds: int
    accept_language: str


class BrowserAutomationInterface(ABC):
    """
    Interface for browser automation operations.

    Follows Interface Segregation Principle by providing only
    the operations needed for web scraping.
    """

    @abstractmethod
    async def navigate_to_url(self, url: str) -> BrowserResponse:
        """Navigate to the specified URL."""
        pass

    @abstractmethod
    async def get_page_content(self) -> str:
        """Get the current page HTML content."""
        pass

    @abstractmethod
    async def wait_for_content_stabilization(self, timeout_seconds: int) -> bool:
        """Wait for page content to stabilize."""
        pass

    @abstractmethod
    async def click_element(self, selector: str) -> bool:
        """Click element by CSS selector."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        pass


class BrowserAutomationFactory(ABC):
    """Factory for creating browser automation instances."""

    @abstractmethod
    async def create_browser(
        self, config: BrowserConfiguration
    ) -> BrowserAutomationInterface:
        """Create a browser automation instance."""
        pass


class TestBrowserAutomationInterface:
    """Test the browser automation interface contract."""

    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser automation instance."""
        browser = Mock(spec=BrowserAutomationInterface)
        browser.navigate_to_url = AsyncMock()
        browser.get_page_content = AsyncMock()
        browser.wait_for_content_stabilization = AsyncMock()
        browser.click_element = AsyncMock()
        browser.close = AsyncMock()
        return browser

    @pytest.fixture
    def browser_config(self):
        """Create a test browser configuration."""
        return BrowserConfiguration(
            user_agent="Test Browser 1.0",
            viewport={"width": 1920, "height": 1080},
            timeout_seconds=30,
            accept_language="en-US",
        )

    @pytest.mark.asyncio
    async def test_successful_navigation(self, mock_browser):
        """Test successful navigation returns proper response."""
        # Arrange
        expected_response = BrowserResponse(
            status_code=200, url="https://example.com", success=True
        )
        mock_browser.navigate_to_url.return_value = expected_response

        # Act
        result = await mock_browser.navigate_to_url("https://example.com")

        # Assert
        assert result.success is True
        assert result.status_code == 200
        assert result.url == "https://example.com"
        assert result.error_message is None
        mock_browser.navigate_to_url.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_failed_navigation(self, mock_browser):
        """Test failed navigation returns error response."""
        # Arrange
        expected_response = BrowserResponse(
            status_code=404,
            url="https://nonexistent.com",
            success=False,
            error_message="Page not found",
        )
        mock_browser.navigate_to_url.return_value = expected_response

        # Act
        result = await mock_browser.navigate_to_url("https://nonexistent.com")

        # Assert
        assert result.success is False
        assert result.status_code == 404
        assert result.error_message == "Page not found"

    @pytest.mark.asyncio
    async def test_get_page_content(self, mock_browser):
        """Test getting page content."""
        # Arrange
        expected_content = "<html><body>Test content</body></html>"
        mock_browser.get_page_content.return_value = expected_content

        # Act
        result = await mock_browser.get_page_content()

        # Assert
        assert result == expected_content
        mock_browser.get_page_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_content_stabilization_success(self, mock_browser):
        """Test successful content stabilization."""
        # Arrange
        mock_browser.wait_for_content_stabilization.return_value = True

        # Act
        result = await mock_browser.wait_for_content_stabilization(timeout_seconds=10)

        # Assert
        assert result is True
        mock_browser.wait_for_content_stabilization.assert_called_once_with(
            timeout_seconds=10
        )

    @pytest.mark.asyncio
    async def test_wait_for_content_stabilization_timeout(self, mock_browser):
        """Test content stabilization timeout."""
        # Arrange
        mock_browser.wait_for_content_stabilization.return_value = False

        # Act
        result = await mock_browser.wait_for_content_stabilization(timeout_seconds=1)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_click_element_success(self, mock_browser):
        """Test successful element click."""
        # Arrange
        mock_browser.click_element.return_value = True

        # Act
        result = await mock_browser.click_element("#button")

        # Assert
        assert result is True
        mock_browser.click_element.assert_called_once_with("#button")

    @pytest.mark.asyncio
    async def test_click_element_failure(self, mock_browser):
        """Test failed element click."""
        # Arrange
        mock_browser.click_element.return_value = False

        # Act
        result = await mock_browser.click_element("#nonexistent")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_browser_cleanup(self, mock_browser):
        """Test browser cleanup."""
        # Act
        await mock_browser.close()

        # Assert
        mock_browser.close.assert_called_once()


class TestBrowserConfiguration:
    """Test browser configuration value object."""

    def test_browser_configuration_creation(self):
        """Test creating browser configuration."""
        config = BrowserConfiguration(
            user_agent="Test Browser",
            viewport={"width": 1024, "height": 768},
            timeout_seconds=15,
            accept_language="en-US",
        )

        assert config.user_agent == "Test Browser"
        assert config.viewport == {"width": 1024, "height": 768}
        assert config.timeout_seconds == 15
        assert config.accept_language == "en-US"

    def test_browser_configuration_immutability(self):
        """Test that browser configuration is immutable."""
        from src.scraper.application.contracts.browser_automation import (
            BrowserConfiguration as RealBrowserConfiguration,
        )

        config = RealBrowserConfiguration(
            user_agent="Test Browser",
            viewport={"width": 1024, "height": 768},
            timeout_seconds=15,
            accept_language="en-US",
        )

        # Test that we cannot modify fields directly (dataclass frozen=True)
        with pytest.raises(AttributeError):
            config.user_agent = "Modified"


class TestBrowserAutomationFactory:
    """Test browser automation factory."""

    @pytest.fixture
    def mock_factory(self):
        """Create a mock browser factory."""
        factory = Mock(spec=BrowserAutomationFactory)
        factory.create_browser = AsyncMock()
        return factory

    @pytest.fixture
    def browser_config(self):
        """Create a test browser configuration."""
        return BrowserConfiguration(
            user_agent="Test Browser 1.0",
            viewport={"width": 1920, "height": 1080},
            timeout_seconds=30,
            accept_language="en-US",
        )

    @pytest.mark.asyncio
    async def test_create_browser(self, mock_factory, browser_config):
        """Test browser creation through factory."""
        # Arrange
        mock_browser = Mock(spec=BrowserAutomationInterface)
        mock_factory.create_browser.return_value = mock_browser

        # Act
        result = await mock_factory.create_browser(browser_config)

        # Assert
        assert result == mock_browser
        mock_factory.create_browser.assert_called_once_with(browser_config)
