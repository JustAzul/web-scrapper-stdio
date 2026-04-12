"""Persistent browser pool for reusing Chromium instances across requests.

Instead of launching a new Playwright driver + Chromium process per scrape,
the pool keeps a fixed number of Chromium instances alive. Each request gets
a fresh BrowserContext (isolated cookies/storage) from the least-loaded browser.
"""

import asyncio

from patchright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

from src.config import BROWSER_POOL_SIZE
from src.logger import Logger
from src.scraper.helpers.browser import apply_stealth

logger = Logger(__name__)


class _BrowserSlot:
    """Tracks a single Chromium instance and its active context count."""

    __slots__ = ("browser", "active_contexts", "lock")

    def __init__(self, browser: Browser):
        self.browser = browser
        self.active_contexts = 0
        self.lock = asyncio.Lock()


class BrowserPool:
    """Pool of persistent Chromium browser instances.

    Usage::

        pool = BrowserPool(pool_size=2)
        await pool.start()

        context, page = await pool.acquire(ua, viewport, lang, timeout_seconds)
        try:
            # ... use page ...
        finally:
            await pool.release(context)

        await pool.shutdown()
    """

    def __init__(self, pool_size: int = BROWSER_POOL_SIZE):
        self._pool_size = max(1, pool_size)
        self._playwright: Playwright | None = None
        self._slots: list[_BrowserSlot] = []
        self._started = False
        self._acquire_semaphore: asyncio.Semaphore | None = None
        self._pick_lock: asyncio.Lock | None = None

    @property
    def is_started(self) -> bool:
        return self._started

    async def start(self) -> None:
        """Launch Playwright driver and Chromium instances."""
        if self._started:
            return

        logger.info(f"Starting browser pool with {self._pool_size} instance(s)")
        self._playwright = await async_playwright().start()

        for i in range(self._pool_size):
            browser = await self._playwright.chromium.launch(headless=True)
            self._slots.append(_BrowserSlot(browser))
            logger.info(f"Browser slot {i} launched")

        # Semaphore prevents unbounded context creation
        self._acquire_semaphore = asyncio.Semaphore(self._pool_size * 10)
        self._pick_lock = asyncio.Lock()
        self._started = True
        logger.info("Browser pool ready")

    async def _ensure_browser_healthy(self, slot: _BrowserSlot, index: int) -> None:
        """Check if browser is connected; relaunch if dead."""
        if slot.browser.is_connected():
            return

        logger.warning(f"Browser slot {index} is dead, relaunching")
        try:
            await slot.browser.close()
        except Exception:
            pass

        slot.browser = await self._playwright.chromium.launch(headless=True)
        slot.active_contexts = 0
        logger.info(f"Browser slot {index} relaunched")

    def _pick_slot(self) -> tuple[int, _BrowserSlot]:
        """Pick the least-loaded browser slot."""
        return min(enumerate(self._slots), key=lambda x: x[1].active_contexts)

    async def acquire(
        self,
        user_agent: str,
        viewport: dict,
        accept_language: str,
        timeout_seconds: int,
    ) -> tuple[BrowserContext, Page]:
        """Get a fresh browser context and page from the pool.

        Returns (context, page). Caller MUST call release(context) when done.
        """
        if not self._started:
            raise RuntimeError("BrowserPool not started. Call start() first.")

        await self._acquire_semaphore.acquire()

        async with self._pick_lock:
            index, slot = self._pick_slot()

            async with slot.lock:
                await self._ensure_browser_healthy(slot, index)

                context = await slot.browser.new_context(
                    user_agent=user_agent,
                    viewport=viewport,
                    java_script_enabled=True,
                    locale=accept_language.split(",")[0],
                    extra_http_headers={"Accept-Language": accept_language},
                )
                page = await context.new_page()
                await apply_stealth(page, timeout_seconds)

                slot.active_contexts += 1

        return context, page

    async def release(self, context: BrowserContext) -> None:
        """Close a browser context and return the slot to the pool."""
        # Find which slot owns this context
        for slot in self._slots:
            try:
                if context.browser == slot.browser:
                    try:
                        await context.close()
                    except Exception:
                        pass
                    async with slot.lock:
                        slot.active_contexts = max(0, slot.active_contexts - 1)
                    self._acquire_semaphore.release()
                    return
            except Exception:
                pass

        # Fallback: context's browser not found in pool (shouldn't happen)
        try:
            await context.close()
        except Exception:
            pass
        self._acquire_semaphore.release()

    async def shutdown(self) -> None:
        """Close all browsers and stop Playwright."""
        if not self._started:
            return

        logger.info("Shutting down browser pool")
        for i, slot in enumerate(self._slots):
            try:
                await slot.browser.close()
                logger.info(f"Browser slot {i} closed")
            except Exception as e:
                logger.warning(f"Error closing browser slot {i}: {e}")

        self._slots.clear()

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._started = False
        logger.info("Browser pool shut down")


# Module-level singleton
_pool: BrowserPool | None = None


async def get_pool() -> BrowserPool:
    """Get or create the global browser pool singleton."""
    global _pool
    if _pool is None or not _pool.is_started:
        _pool = BrowserPool(pool_size=BROWSER_POOL_SIZE)
        await _pool.start()
    return _pool


async def shutdown_pool() -> None:
    """Shut down the global browser pool if it exists."""
    global _pool
    if _pool is not None and _pool.is_started:
        await _pool.shutdown()
        _pool = None
