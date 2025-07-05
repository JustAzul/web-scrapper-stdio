import pytest
from src.scraper.scrapper import Scraper
from src.models import ScrapeArgs, OutputFormat

def test_scraper_scrape_returns_content(monkeypatch):
    scraper = Scraper()
    args = ScrapeArgs(
        url="http://example.com",
        timeout_seconds=1,
        grace_period_seconds=0.1,
        output_format=OutputFormat.TEXT,
    )
    # Monkeypatch the scrape internals for CI
    monkeypatch.setattr(scraper, "_configure_page", lambda page, args: None)
    monkeypatch.setattr(scraper, "_process_html", lambda html, args: "mocked content")
    monkeypatch.setattr(scraper, "_format_output", lambda content, fmt: content)
    monkeypatch.setattr(scraper, "_get_user_agent", lambda ua=None: "test-agent")

    class DummyPage:
        def goto(self, url, timeout): return type("Resp", (), {"status": 200, "status_text": "OK"})()
        def content(self): return "<html>mocked</html>"
        def url(self): return "http://example.com"
        def title(self): return "Mocked"
        def close(self): pass
        def set_viewport_size(self, v): pass
        def set_extra_http_headers(self, h): pass

    class DummyBrowser:
        def new_page(self): return DummyPage()
        def close(self): pass

    class DummyPlaywright:
        def __enter__(self): return type("P", (), {"chromium": type("C", (), {"launch": lambda *a, **k: DummyBrowser()})})()
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    monkeypatch.setattr("src.scraper.scrapper.sync_playwright", lambda: DummyPlaywright())

    result = scraper.scrape(args)
    assert isinstance(result, dict)
    assert result["error"] is None
    assert "mocked content" in result["content"]
