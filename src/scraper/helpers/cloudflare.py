"""Cloudflare challenge detection and solving.

Provides:
- detect_cf_challenge_live(page) — live page-based detection
- detect_cf_challenge_html(html) — regex-based HTML detection (legacy)
- setup_turnstile_interceptor(page) — intercepts Turnstile script to capture params
- solve_cf_challenge(page, solver, url) — solves a Turnstile challenge transparently
"""

import asyncio
import re

from src.logger import Logger
from src.scraper.helpers.captcha_solver import CaptchaSolver, CaptchaSolveError

logger = Logger(__name__)

# Legacy HTML-regex patterns (from the original errors.py)
_CF_HTML_PATTERNS = [
    re.compile(r'Attention Required! \| Cloudflare', re.IGNORECASE),
    re.compile(r'cf-browser-verification', re.IGNORECASE),
    re.compile(r'Checking your browser before accessing', re.IGNORECASE),
    re.compile(r'Please enable JavaScript and Cookies to continue', re.IGNORECASE),
    re.compile(r'Cloudflare Ray ID', re.IGNORECASE),
    re.compile(r'cloudflare\.com/speedtest', re.IGNORECASE),
    re.compile(r'Why do I have to complete a CAPTCHA\?', re.IGNORECASE),
]

# Regex patterns for extracting Turnstile sitekey from HTML
_SITEKEY_PATTERNS = [
    re.compile(r'data-sitekey="([^"]+)"'),
    re.compile(r"sitekey['\"]?\s*[:=]\s*['\"]([0-9a-zA-Z_.-]+)['\"]"),
    re.compile(r"turnstileSiteKey['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"/turnstile/v0/api\.js\?.*?sitekey=([^&\"']+)"),
]


def detect_cf_challenge_html(html_content: str) -> bool:
    """Check raw HTML for Cloudflare challenge patterns (legacy detector)."""
    return any(p.search(html_content) for p in _CF_HTML_PATTERNS)


async def detect_cf_challenge_live(page) -> str | None:
    """Detect Cloudflare challenge on a live page.

    Returns a signal string on detection, or None if no challenge found.
    Never throws — returns None on any error.
    """
    try:
        title = await page.title()
        if "Just a moment" in title:
            logger.warning("Cloudflare challenge detected: title='Just a moment'")
            return "title:just-a-moment"

        url = page.url
        if "__cf_chl_jschl_tk__" in url:
            logger.warning("Cloudflare challenge detected: cf_chl token in URL")
            return "url:cf-chl-token"

        try:
            content = await page.content()
        except Exception:
            return None

        for marker in ("cf-challenge-running", "cf-error-details", "h-captcha", "g-recaptcha"):
            if marker in content:
                logger.warning(f"Cloudflare challenge detected: marker={marker!r} in DOM")
                return f"dom:{marker}"
    except Exception as exc:
        logger.debug(f"Cloudflare detector failed: {exc}")
    return None


async def setup_turnstile_interceptor(page) -> None:
    """Intercept the Cloudflare Turnstile script to capture render() parameters.

    Monkey-patches turnstile.render() to capture sitekey, action, cData, chlPageData
    into window.__turnstileParams. Must be called BEFORE navigation.
    """
    async def _intercept_turnstile(route):
        response = await route.fetch()
        body = await response.body()
        original_js = body.decode("utf-8", errors="replace")

        patch_js = """
;(function() {
    var _origRender = window.turnstile ? window.turnstile.render : null;
    function _patchRender() {
        if (!window.turnstile || !window.turnstile.render) return;
        if (window.turnstile.__patched) return;
        var orig = window.turnstile.render;
        window.turnstile.render = function(container, params) {
            window.__turnstileParams = {
                sitekey: params.sitekey || '',
                action: params.action || '',
                cData: params.cData || '',
                chlPageData: params.chlPageData || '',
            };
            window.__turnstileCallback = params.callback || null;
            window.turnstile.__patched = true;
            return orig.call(window.turnstile, container, params);
        };
    }
    _patchRender();
    var _val = window.turnstile;
    try {
        Object.defineProperty(window, 'turnstile', {
            configurable: true,
            get: function() { return _val; },
            set: function(v) { _val = v; if (v && v.render) _patchRender(); }
        });
    } catch(e) {}
})();
"""
        modified_js = original_js + patch_js
        await route.fulfill(
            response=response,
            body=modified_js,
            headers={**response.headers, "content-length": str(len(modified_js))},
        )

    await page.route("**/challenges.cloudflare.com/turnstile/**", _intercept_turnstile)


async def _extract_turnstile_params(page) -> dict | None:
    """Extract Turnstile params from interceptor or HTML fallback.

    Returns dict with sitekey/action/cData/chlPageData or None.
    """
    # 1. Poll the interceptor's captured params (up to 20s)
    for _ in range(40):
        await asyncio.sleep(0.5)
        params = await page.evaluate("() => window.__turnstileParams")
        if params and params.get("sitekey"):
            return params

    logger.warning("Turnstile interceptor did not capture params — trying HTML regex fallback")
    html = await page.content()

    # 2. Regex fallback for sitekey
    params = None
    for pattern in _SITEKEY_PATTERNS:
        match = pattern.search(html)
        if match:
            params = {"sitekey": match.group(1), "action": "", "cData": "", "chlPageData": ""}
            logger.warning(f"Turnstile: found sitekey via HTML regex: {match.group(1)[:15]}...")
            break

    # 3. Extract challenge page metadata from _cf_chl_opt JS object
    if params and params.get("sitekey"):
        ctype_match = re.search(r"cType\s*:\s*['\"](\w+)['\"]", html)
        if ctype_match:
            params["action"] = ctype_match.group(1)

        cray_match = re.search(r"cRay\s*:\s*['\"]([^'\"]+)['\"]", html)
        if cray_match:
            params["cData"] = cray_match.group(1)

        chlpage_match = re.search(r'chlPageData["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        if chlpage_match:
            params["chlPageData"] = chlpage_match.group(1)

        logger.warning(
            f"Turnstile regex extraction — action={params.get('action')} "
            f"cData={bool(params.get('cData'))} chlPageData={bool(params.get('chlPageData'))}"
        )

    # 4. DOM fallback: data-sitekey attribute
    if not params or not params.get("sitekey"):
        sitekey_el = await page.query_selector("[data-sitekey]")
        if sitekey_el:
            sitekey = await sitekey_el.get_attribute("data-sitekey")
            if sitekey:
                params = {"sitekey": sitekey, "action": "", "cData": "", "chlPageData": ""}
                logger.warning("Turnstile: found sitekey via DOM fallback")

    return params if params and params.get("sitekey") else None


async def solve_cf_challenge(
    page,
    solver: CaptchaSolver,
    page_url: str,
) -> tuple[bool, str | None]:
    """Solve a Cloudflare Turnstile challenge on the page.

    Returns (success, error_message). On success, the page should have
    navigated past the challenge to the real content.
    """
    params = await _extract_turnstile_params(page)
    if not params:
        return False, "Could not extract Turnstile sitekey from challenge page"

    logger.info(
        f"Turnstile: solving challenge sitekey={params['sitekey'][:10]}... "
        f"action={params.get('action')} has_pagedata={bool(params.get('chlPageData'))}"
    )

    try:
        token = await solver.solve_turnstile(
            site_key=params["sitekey"],
            page_url=page_url,
            action=params.get("action") or None,
            cdata=params.get("cData") or None,
            pagedata=params.get("chlPageData") or None,
        )
    except CaptchaSolveError as exc:
        return False, str(exc)

    # Inject token into the page
    await page.evaluate("""(token) => {
        if (typeof window.__turnstileCallback === 'function') {
            window.__turnstileCallback(token);
        }
        document.querySelectorAll(
            '[name="cf-turnstile-response"], [name="g-recaptcha-response"]'
        ).forEach(el => { el.value = token; });
    }""", token)

    # Wait for CF to validate and redirect
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        logger.warning("Turnstile: networkidle timeout after token injection (may still succeed)")

    # Check if the page navigated away from the challenge (URL changed = redirect = success)
    current_url = page.url
    if current_url != page_url:
        logger.info(f"Turnstile: page redirected from challenge to {current_url}")
        return True, None

    # URL didn't change — check if challenge markers are still present
    post_challenge = await detect_cf_challenge_live(page)
    if post_challenge:
        # Token was injected but challenge persists — could be a demo page or failed solve
        logger.warning(f"Turnstile: challenge still present after injection ({post_challenge})")
        return False, f"Challenge still present after token injection: {post_challenge}"

    return True, None
