"""Baseline performance benchmarks for web-scrapper-stdio.

Measures current performance characteristics to establish baselines
before any optimization work. All times in seconds.

Run inside Docker:
  docker compose run --rm benchmark
"""

import asyncio
import os
import resource
import statistics
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from playwright.async_api import async_playwright
from src.scraper import extract_text_from_url
from src.scraper.helpers.browser import _setup_browser_context, USER_AGENTS, VIEWPORTS, LANGUAGES
from src.output_format_handler import OutputFormat

# Target URLs for benchmarking
STATIC_URL = "http://example.com"
JS_HEAVY_URL = "https://en.wikipedia.org/wiki/Python_(programming_language)"

ITERATIONS = 5


def get_memory_mb():
    """Get current RSS memory in MB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def print_stats(label, times):
    """Print p50/p95/min/max for a list of timings."""
    times_sorted = sorted(times)
    p50 = statistics.median(times_sorted)
    p95 = times_sorted[int(len(times_sorted) * 0.95)] if len(times_sorted) >= 2 else times_sorted[-1]
    print(f"  {label}:")
    print(f"    p50={p50:.3f}s  p95={p95:.3f}s  min={min(times):.3f}s  max={max(times):.3f}s")
    return p50, p95


async def bench_cold_start():
    """Measure time to spawn Playwright driver + launch Chromium + create context + page."""
    print("\n=== Cold Start (Playwright + Chromium + Context + Page) ===")
    times = []

    for i in range(ITERATIONS):
        t0 = time.perf_counter()
        async with async_playwright() as p:
            browser, context, page = await _setup_browser_context(
                p, USER_AGENTS[0], VIEWPORTS[0], LANGUAGES[0], 30
            )
            t1 = time.perf_counter()
            await context.close()
            await browser.close()
        elapsed = t1 - t0
        times.append(elapsed)
        print(f"  run {i+1}/{ITERATIONS}: {elapsed:.3f}s")

    return print_stats("Cold start", times)


async def bench_full_scrape_static():
    """Measure full extract_text_from_url on a static page (example.com)."""
    print(f"\n=== Full Scrape: Static Page ({STATIC_URL}) ===")
    times = []

    for i in range(ITERATIONS):
        t0 = time.perf_counter()
        result = await extract_text_from_url(
            STATIC_URL,
            grace_period_seconds=2.0,
            output_format=OutputFormat.MARKDOWN,
        )
        t1 = time.perf_counter()
        elapsed = t1 - t0
        status = "ok" if not result.get("error") else f"err: {result['error'][:60]}"
        times.append(elapsed)
        print(f"  run {i+1}/{ITERATIONS}: {elapsed:.3f}s [{status}]")

    return print_stats("Full scrape (static, grace=2.0)", times)


async def bench_grace_period_comparison():
    """Compare grace_period=2.0 vs grace_period=0.1 on static page."""
    print(f"\n=== Grace Period Comparison ({STATIC_URL}) ===")

    for gp in [2.0, 1.0, 0.5, 0.1]:
        times = []
        for i in range(ITERATIONS):
            t0 = time.perf_counter()
            result = await extract_text_from_url(
                STATIC_URL,
                grace_period_seconds=gp,
                output_format=OutputFormat.MARKDOWN,
            )
            t1 = time.perf_counter()
            times.append(t1 - t0)
        print_stats(f"grace_period={gp}", times)


async def bench_consecutive_different_domains():
    """Measure 3 consecutive scrapes to different domains (no rate limiter delay)."""
    print("\n=== Consecutive Scrapes (different domains) ===")
    urls = [
        "http://example.com",
        "http://example.org",
        "https://httpbin.org/html",
    ]
    times = []
    for url in urls:
        t0 = time.perf_counter()
        result = await extract_text_from_url(
            url,
            grace_period_seconds=2.0,
            output_format=OutputFormat.MARKDOWN,
        )
        t1 = time.perf_counter()
        elapsed = t1 - t0
        status = "ok" if not result.get("error") else f"err: {result['error'][:60]}"
        times.append(elapsed)
        print(f"  {url}: {elapsed:.3f}s [{status}]")

    print(f"  Total: {sum(times):.3f}s  Avg: {statistics.mean(times):.3f}s")
    return times


async def bench_js_heavy_page():
    """Measure scraping a JS-heavy page (Wikipedia)."""
    print(f"\n=== JS-Heavy Page ({JS_HEAVY_URL}) ===")
    times = []

    for i in range(3):  # Fewer iterations — slower page
        t0 = time.perf_counter()
        result = await extract_text_from_url(
            JS_HEAVY_URL,
            grace_period_seconds=2.0,
            output_format=OutputFormat.MARKDOWN,
        )
        t1 = time.perf_counter()
        elapsed = t1 - t0
        status = "ok" if not result.get("error") else f"err: {result['error'][:60]}"
        content_len = len(result.get("content") or "")
        times.append(elapsed)
        print(f"  run {i+1}/3: {elapsed:.3f}s [{status}, {content_len} chars]")

    return print_stats("JS-heavy page", times)


async def bench_memory():
    """Measure memory before and after a scrape."""
    print("\n=== Memory Usage ===")
    mem_before = get_memory_mb()
    print(f"  Before scrape: {mem_before:.1f} MB")

    await extract_text_from_url(STATIC_URL, grace_period_seconds=0.5)

    mem_after = get_memory_mb()
    print(f"  After 1 scrape: {mem_after:.1f} MB (delta: {mem_after - mem_before:.1f} MB)")

    # Do 3 more scrapes
    for _ in range(3):
        await extract_text_from_url("http://example.org", grace_period_seconds=0.5)

    mem_final = get_memory_mb()
    print(f"  After 4 scrapes: {mem_final:.1f} MB (delta: {mem_final - mem_before:.1f} MB)")
    return mem_before, mem_after, mem_final


async def main():
    print("=" * 60)
    print("BASELINE BENCHMARKS — web-scrapper-stdio")
    print("=" * 60)
    print(f"Iterations per benchmark: {ITERATIONS}")
    print(f"Static URL: {STATIC_URL}")
    print(f"JS-heavy URL: {JS_HEAVY_URL}")

    cold_p50, cold_p95 = await bench_cold_start()
    static_p50, static_p95 = await bench_full_scrape_static()
    await bench_grace_period_comparison()
    await bench_consecutive_different_domains()
    js_p50, js_p95 = await bench_js_heavy_page()
    mem_before, mem_after, mem_final = await bench_memory()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Cold start:           p50={cold_p50:.3f}s  p95={cold_p95:.3f}s")
    print(f"  Full scrape (static): p50={static_p50:.3f}s  p95={static_p95:.3f}s")
    print(f"  Full scrape (JS):     p50={js_p50:.3f}s  p95={js_p95:.3f}s")
    print(f"  Memory (peak):        {mem_final:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
