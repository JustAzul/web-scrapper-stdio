"""
Playwright-based implementation of browser automation interface.

This implementation provides concrete browser automation using Playwright,
following the Dependency Inversion Principle by implementing the abstract
interface defined in the interfaces module.
"""

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError,
    async_playwright,
)

from src.core.constants import (
    HTTP_CLIENT_ERROR_THRESHOLD,
    MILLISECONDS_PER_SECOND,
    SELECTOR_CLICK_TIMEOUT_MS,
)
from src.logger import Logger

from ...application.contracts.browser_automation import (
    BrowserAutomation,
    BrowserAutomationFactory,
    BrowserConfiguration,
    BrowserResponse,
)

logger = Logger(__name__)


class PlaywrightBrowser(BrowserAutomation):
    """
    Playwright-based implementation of the BrowserAutomation interface.
    """

    def __init__(self, page: Page, context: BrowserContext, browser: Browser):
        """
        Initialize with Playwright browser objects.

        Args:
            page: Playwright page object
            context: Playwright browser context
            browser: Playwright browser object
        """
        self._page = page
        self._context = context
        self._browser = browser

    async def navigate_to_url(self, url: str) -> BrowserResponse:
        """
        Navigate to URL using Playwright.

        Args:
            url: Target URL

        Returns:
            BrowserResponse with navigation result
        """
        try:
            response = await self._page.goto(url)
            if response and response.status < HTTP_CLIENT_ERROR_THRESHOLD:
                content = await self._page.content()
                return BrowserResponse(
                    success=True,
                    content=content,
                    error=None,
                    status_code=response.status,
                    url=response.url,
                )
            else:
                return BrowserResponse(
                    success=False,
                    content=None,
                    error=f"HTTP {response.status if response else 'Unknown error'}",
                    status_code=response.status if response else None,
                    url=url,
                )
        except TimeoutError:
            return BrowserResponse(
                success=False,
                content=None,
                error="Navigation timeout",
                status_code=None,
                url=url,
            )
        except Exception as e:
            # Format network errors consistently with test expectations
            error_str = str(e)
            if "net::ERR_NAME_NOT_RESOLVED" in error_str:
                error_message = f"Could not resolve host: {url}"
            elif "net::ERR_CONNECTION_REFUSED" in error_str:
                error_message = f"Could not connect to host: {url}"
            elif "Target closed" in error_str:
                error_message = "Browser tab closed unexpectedly during operation"
            else:
                error_message = error_str

            return BrowserResponse(
                success=False,
                content=None,
                error=error_message,
                status_code=None,
                url=url,
            )

    async def get_page_content(self) -> str:
        """
        Get current page HTML content.

        Returns:
            HTML content as string
        """
        return await self._page.content()

    async def wait_for_content_stabilization(self, timeout_seconds: int) -> bool:
        """
        Wait for page content to stabilize.

        Args:
            timeout_seconds: Maximum wait time in seconds

        Returns:
            True if stabilized, False if timeout
        """
        try:
            # Wait for network to be idle (no requests for NETWORK_IDLE_TIMEOUT_MS)
            await self._page.wait_for_load_state(
                "networkidle", timeout=timeout_seconds * MILLISECONDS_PER_SECOND
            )
            return True
        except TimeoutError:
            return False

    async def click_element(self, selector: str) -> bool:
        """
        Click element by CSS selector.

        Args:
            selector: CSS selector

        Returns:
            True if successful, False otherwise
        """
        try:
            await self._page.click(selector, timeout=SELECTOR_CLICK_TIMEOUT_MS)
            return True
        except (TimeoutError, Exception):
            return False

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            await self._context.close()
            await self._browser.close()
        except Exception as e:
            # Ignore cleanup errors, but log them
            logger.warning("Error during browser cleanup: %s", e)


class PlaywrightBrowserFactory(BrowserAutomationFactory):
    """
    Factory for creating Playwright browser instances.

    Implements the factory pattern for browser creation,
    allowing configuration of browser settings.
    """

    async def create_browser(self, config: BrowserConfiguration) -> BrowserAutomation:
        """
        Create Playwright browser instance with configuration.

        Args:
            config: Browser configuration

        Returns:
            Configured browser automation instance
        """
        playwright = await async_playwright().start()

        # Launch browser with configuration
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )

        # Create context with configuration
        context_options = {
            "user_agent": config.user_agent,
        }

        if config.viewport:
            context_options["viewport"] = config.viewport

        if config.accept_language:
            context_options["locale"] = config.accept_language

        context = await browser.new_context(**context_options)

        # Set timeout
        context.set_default_timeout(config.timeout_seconds * MILLISECONDS_PER_SECOND)

        # Create page
        page = await context.new_page()

        return PlaywrightBrowser(page, context, browser)
