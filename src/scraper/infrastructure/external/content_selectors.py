from src.logger import Logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = Logger(__name__)


async def _wait_for_content_stabilization(
    page, domain, timeout_seconds, wait_for_network_idle=True
):
    if wait_for_network_idle:
        try:
            await page.wait_for_load_state(
                "networkidle", timeout=timeout_seconds * 1000 / 2
            )
            logger.debug("Network became idle")

        except PlaywrightTimeoutError:
            logger.debug(
                f"Network didn't become fully idle after {timeout_seconds / 2}s, continuing anyway"
            )

    try:
        await page.wait_for_selector("body", timeout=timeout_seconds * 1000 / 2)
        return True

    except PlaywrightTimeoutError:
        logger.warning("<body> tag not found after waiting.")
        return False
