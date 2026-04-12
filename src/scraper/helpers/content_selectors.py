import asyncio

from src.logger import Logger
from patchright.async_api import TimeoutError as PlaywrightTimeoutError

logger = Logger(__name__)


async def wait_for_dom_stable(page, grace_period_seconds: float) -> None:
    """Wait for DOM to stabilize using MutationObserver, with grace_period as max timeout.

    If grace_period_seconds is 0, returns immediately.
    Otherwise, injects a MutationObserver that resolves when no DOM mutations
    occur for 200ms, or when grace_period_seconds elapses (whichever is first).
    Falls back to asyncio.sleep on any error.
    """
    if grace_period_seconds <= 0:
        return

    timeout_ms = int(grace_period_seconds * 1000)
    try:
        await page.evaluate(f"""
            () => new Promise((resolve) => {{
                let timer;
                const maxTimeout = setTimeout(() => {{
                    if (observer) observer.disconnect();
                    resolve();
                }}, {timeout_ms});
                const observer = new MutationObserver(() => {{
                    clearTimeout(timer);
                    timer = setTimeout(() => {{
                        clearTimeout(maxTimeout);
                        observer.disconnect();
                        resolve();
                    }}, 200);
                }});
                observer.observe(document.body, {{subtree: true, childList: true, characterData: true}});
                // If no mutations at all, resolve after a short initial wait
                timer = setTimeout(() => {{
                    clearTimeout(maxTimeout);
                    observer.disconnect();
                    resolve();
                }}, 200);
            }})
        """)
    except Exception as e:
        logger.debug(f"MutationObserver wait failed ({e}), falling back to sleep({grace_period_seconds}s)")
        await asyncio.sleep(grace_period_seconds)


async def _wait_for_content_stabilization(page, domain, timeout_seconds, wait_for_network_idle=True):
    if wait_for_network_idle:
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout_seconds * 1000 / 2)
            logger.debug("Network became idle")

        except PlaywrightTimeoutError:
            logger.debug(
                f"Network didn't become fully idle after {timeout_seconds/2}s, continuing anyway")

    try:
        await page.wait_for_selector('body', timeout=timeout_seconds * 1000 / 2)
        return True

    except PlaywrightTimeoutError:
        logger.warning("<body> tag not found after waiting.")
        return False
