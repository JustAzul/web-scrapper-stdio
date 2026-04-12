# Benchmark Results

## Phase 0: Baseline (2026-04-12)

No optimizations. Current codebase as-is.

| Metric | p50 | p95 | Notes |
|--------|-----|-----|-------|
| Cold start (PW + Chromium + context) | 0.345s | 0.458s | Per-request overhead |
| Full scrape — static (example.com, grace=2.0) | 3.175s | 3.392s | Dominated by grace period + cold start |
| Full scrape — JS-heavy (Wikipedia, grace=2.0) | 4.614s | 4.726s | Network + rendering adds ~1.4s over static |
| Memory (peak RSS after 4 scrapes) | 75.5 MB | — | No leak observed |

### Grace Period Impact (static page, example.com)

| grace_period | p50 | p95 | Delta vs 2.0 |
|-------------|-----|-----|-------------|
| 2.0s | 3.078s | 3.890s | baseline |
| 1.0s | 2.103s | 2.119s | -0.975s |
| 0.5s | 1.999s | 2.033s | -1.079s |
| 0.1s | 1.999s | 3.892s | -1.079s (p50), unstable p95 due to rate limiter overlap |

### Consecutive Scrapes (different domains, grace=2.0)

| URL | Time |
|-----|------|
| example.com | 3.920s |
| example.org | 3.409s |
| httpbin.org/html | 6.463s |
| **Total** | **13.792s** |

### Key Observations

1. **Cold start is ~0.35s** — not as bad as feared, but still paid every single request
2. **Grace period is the dominant waste** — reducing from 2.0s to 0.5s saves ~1s per request on static pages
3. **Total per-request cost breakdown (static, grace=2.0):**
   - Cold start: ~0.35s
   - Navigation + networkidle: ~0.8s
   - Grace period sleep: ~2.0s (the biggest chunk!)
   - Total: ~3.15s
4. **Memory is stable** at 75.5 MB — no leak across requests (expected since browser is destroyed per call)
5. **Rate limiter adds variance** — when consecutive requests hit same domain within 2s, adds 0.4-2.7s delay

---

## Phase 1: Smart Grace Period + MutationObserver (2026-04-12)

Replaced `asyncio.sleep(grace_period)` with MutationObserver-based DOM stability detection.
Default grace_period changed from 2.0s to 0.5s. `grace_period_seconds=0` now allowed.

| Metric | Baseline | Phase 1 | Change |
|--------|----------|---------|--------|
| Cold start | 0.345s | 0.348s | ~same |
| Full scrape — static (grace=2.0 passed) | 3.175s | 2.005s | **-37%** |
| Full scrape — JS-heavy (Wikipedia) | 4.614s | 2.789s | **-40%** |
| Consecutive scrapes (3 domains) | 13.792s | 4.968s | **-64%** |
| Memory (peak) | 75.5 MB | 75.8 MB | ~same |

### Key Observations

1. **MutationObserver resolves in ~200ms on static pages** — even with `grace_period=2.0` passed, the observer detects no DOM mutations and resolves after 200ms idle threshold
2. **Grace period comparison shows ~2.0s across all values** — rate limiter (2s/domain) dominates when benchmarking same domain. The actual grace period savings is masked.
3. **JS-heavy page improved 40%** — MutationObserver waits for actual rendering to finish rather than an arbitrary fixed delay
4. **Consecutive different-domain scrapes massively improved** — no rate limiting between domains, and MutationObserver exits quickly on each

---

## Phase 2: Persistent Browser Pool (2026-04-12)

Added BrowserPool singleton that keeps Chromium instances alive across requests.
Each request gets a fresh BrowserContext (isolated cookies/storage) but reuses the browser process.

| Metric | Baseline | Phase 1 | Phase 2 | Total change |
|--------|----------|---------|---------|-------------|
| Full scrape — static (grace=2.0) | 3.175s | 2.005s | 1.999s | **-37%** |
| Full scrape — JS-heavy | 4.614s | 2.789s | 2.441s | **-47%** |
| Consecutive scrapes (3 domains) | 13.792s | 4.968s | 4.339s | **-69%** |
| Memory (peak) | 75.5 MB | 75.8 MB | 88.8 MB | +13.3 MB |

### Key Observations

1. **Pool adds ~13 MB overhead** for persistent Chromium process — acceptable tradeoff
2. **First request includes pool init** (1.295s), subsequent requests skip browser launch entirely
3. **JS-heavy scrape further improved** from 2.789s to 2.441s — ~350ms saved from skipping Chromium launch
4. **Rate limiter (2s/domain) now dominates** the per-request cost for same-domain requests. The actual scraping overhead (navigate + render + extract) is well under 1s.
