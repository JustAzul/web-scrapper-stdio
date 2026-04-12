"""Tests for Cloudflare detection and captcha solver modules."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.scraper.helpers.cloudflare import (
    detect_cf_challenge_html,
    detect_cf_challenge_live,
)
from src.scraper.helpers.captcha_solver import (
    CaptchaSolver,
    CaptchaSolveError,
    PROVIDER_URLS,
)


# --- detect_cf_challenge_html tests ---

class TestDetectCfChallengeHtml:
    def test_detects_attention_required(self):
        assert detect_cf_challenge_html("Attention Required! | Cloudflare") is True

    def test_detects_browser_verification(self):
        assert detect_cf_challenge_html('<div class="cf-browser-verification">') is True

    def test_detects_checking_browser(self):
        assert detect_cf_challenge_html("Checking your browser before accessing") is True

    def test_detects_enable_javascript(self):
        assert detect_cf_challenge_html("Please enable JavaScript and Cookies to continue") is True

    def test_detects_cloudflare_ray_id(self):
        assert detect_cf_challenge_html("Cloudflare Ray ID: abc123") is True

    def test_detects_speedtest_link(self):
        assert detect_cf_challenge_html('href="cloudflare.com/speedtest"') is True

    def test_detects_captcha_prompt(self):
        assert detect_cf_challenge_html("Why do I have to complete a CAPTCHA?") is True

    def test_no_match_on_normal_html(self):
        assert detect_cf_challenge_html("<html><body>Hello World</body></html>") is False

    def test_no_match_on_empty(self):
        assert detect_cf_challenge_html("") is False

    def test_case_insensitive(self):
        assert detect_cf_challenge_html("CLOUDFLARE RAY ID: xyz") is True


# --- detect_cf_challenge_live tests ---

class TestDetectCfChallengeLive:
    @pytest.mark.asyncio
    async def test_detects_just_a_moment_title(self):
        page = AsyncMock()
        page.title.return_value = "Just a moment..."
        page.url = "https://example.com"
        result = await detect_cf_challenge_live(page)
        assert result == "title:just-a-moment"

    @pytest.mark.asyncio
    async def test_detects_cf_chl_token_in_url(self):
        page = AsyncMock()
        page.title.return_value = "Example"
        page.url = "https://example.com?__cf_chl_jschl_tk__=abc"
        page.content.return_value = "<html><body>OK</body></html>"
        result = await detect_cf_challenge_live(page)
        assert result == "url:cf-chl-token"

    @pytest.mark.asyncio
    async def test_detects_dom_marker(self):
        page = AsyncMock()
        page.title.return_value = "Example"
        page.url = "https://example.com"
        page.content.return_value = '<div id="cf-challenge-running"></div>'
        result = await detect_cf_challenge_live(page)
        assert result == "dom:cf-challenge-running"

    @pytest.mark.asyncio
    async def test_no_challenge(self):
        page = AsyncMock()
        page.title.return_value = "Example Domain"
        page.url = "https://example.com"
        page.content.return_value = "<html><body>Normal page</body></html>"
        result = await detect_cf_challenge_live(page)
        assert result is None

    @pytest.mark.asyncio
    async def test_never_throws(self):
        page = AsyncMock()
        page.title.side_effect = Exception("Page crashed")
        result = await detect_cf_challenge_live(page)
        assert result is None


# --- CaptchaSolver tests ---

class TestCaptchaSolver:
    def test_provider_urls_exist(self):
        assert "2captcha" in PROVIDER_URLS
        assert "capsolver" in PROVIDER_URLS
        assert "capmonster" in PROVIDER_URLS

    @pytest.mark.asyncio
    async def test_solve_turnstile_bad_api_key(self):
        solver = CaptchaSolver(
            provider="2captcha",
            api_key="invalid_key",
            base_url=PROVIDER_URLS["2captcha"],
            timeout_s=10,
        )
        with pytest.raises(CaptchaSolveError, match="createTask failed|network error"):
            await solver.solve_turnstile(
                site_key="0x4AAAAAAAB",
                page_url="https://example.com",
            )

    @pytest.mark.asyncio
    async def test_solve_turnstile_network_error(self):
        solver = CaptchaSolver(
            provider="2captcha",
            api_key="test_key",
            base_url="http://localhost:1/nonexistent",
            timeout_s=5,
        )
        with pytest.raises(CaptchaSolveError, match="network error"):
            await solver.solve_turnstile(
                site_key="0x4AAAAAAAB",
                page_url="https://example.com",
            )
