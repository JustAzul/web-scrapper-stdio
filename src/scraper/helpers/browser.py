from playwright_stealth import stealth_async

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
    {"width": 1280, "height": 800},
]
LANGUAGES = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7"]


async def _setup_browser_context(p, user_agent, viewport, accept_language, timeout_seconds):
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        java_script_enabled=True,
        locale=accept_language.split(",")[0],
        extra_http_headers={"Accept-Language": accept_language},
    )
    page = await context.new_page()

    await stealth_async(page)
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"
        "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});"
    )
    page.set_default_navigation_timeout(timeout_seconds * 1000)
    page.set_default_timeout(timeout_seconds * 1000)

    return browser, context, page
