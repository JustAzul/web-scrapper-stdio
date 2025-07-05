from typing import Optional

from playwright.async_api import Browser, Playwright
from playwright_stealth import stealth_async

from src.core.constants import (
    DEFAULT_BROWSER_VIEWPORTS,
    DEFAULT_USER_AGENTS,
)

# NOTE: Browser pooling/singleton is only safe in long-lived, single-process,
# non-test environments.


async def launch_browser(
    playwright: Playwright,
    headless: bool = True,
    user_agent: Optional[str] = None,
) -> Browser:
    """Launches a configured Playwright browser instance."""
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(
        user_agent=user_agent or DEFAULT_USER_AGENTS[0],
        viewport=DEFAULT_BROWSER_VIEWPORTS[0],
    )
    page = await context.new_page()
    await stealth_async(page)
    return browser
