from urllib.parse import urlparse


def discover_rss_feeds(domain_url: str) -> list[str]:
    """Tries to discover RSS feeds for the given domain URL.
    Returns a list of discovered RSS feed URLs, ordered by likelihood of success."""
    parsed_url = urlparse(domain_url)
    domain_root = parsed_url.netloc
    base_domain = domain_root.replace("www.", "")

    # Domain-specific known feeds with higher priority
    domain_specific_feeds = {
        # NOTE: Forbes does not provide a public RSS feed for Innovation as of 2025-06-08.
        'fortune.com': ['https://fortune.com/feed/'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'techcrunch.com': ['https://techcrunch.com/feed/'],  # VALID: RSS XML (Playwright, checked 2025-06-06)
        'wired.com': ['https://www.wired.com/feed/rss'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'engadget.com': ['https://www.engadget.com/rss.xml'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'medium.com': ['https://medium.com/feed/', 'https://medium.com/feed/tag/technology'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'dev.to': ['https://dev.to/feed/', 'https://dev.to/feed/top'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'tomsguide.com': ['https://www.tomsguide.com/feeds/news.xml', 'https://www.tomsguide.com/feeds/all-news.xml'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'xda-developers.com': ['https://www.xda-developers.com/feed/'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
        'dmnews.com': ['https://www.dmnews.com/feed/'],  # VALID: RSS XML (Playwright, checked 2025-06-08)
    }

    # Common RSS feed paths to check if no domain-specific feed matches
    common_paths = [
        "/feed",
        "/rss",
        "/feed/",
        "/rss/",
        "/feed.xml",
        "/rss.xml",
        "/atom.xml",
        "/feeds/posts/default",
        "/index.xml",
        "/index.rss",
        "/rss/index.rss",
        "/feed/rss",
        "/blog/feed",
        "/blog/rss",
        "/news/feed",
        "/articles/feed",
    ]

    # Check domain-specific feeds first
    discovered_feeds = []

    # Add domain-specific feeds if available
    for domain, feeds in domain_specific_feeds.items():
        if domain in base_domain:
            discovered_feeds.extend(feeds)
            break  # Only use the first matching domain's feeds

    # If no domain-specific feeds found, try common paths
    if not discovered_feeds:
        for path in common_paths:
            feed_url = f"{parsed_url.scheme}://{domain_root}{path}"
            discovered_feeds.append(feed_url)

    return discovered_feeds


def verify_rss_feed(feed_data):
    """Verify if the parsed feed data is a valid RSS feed"""
    # Check for essential RSS feed elements
    if not hasattr(feed_data, 'feed') or not hasattr(feed_data, 'entries'):
        return False

    # Check if the feed has a title (most valid feeds do)
    if not hasattr(feed_data.feed, 'title'):
        return False

    # Check if there are entries
    if not feed_data.entries:
        return False

    # Verify at least one entry has a link
    for entry in feed_data.entries:
        if hasattr(entry, 'link') and entry.link:
            return True

    return False


def extract_article_from_feed(feed_data):
    """Extract a valid article link from feed data"""
    if not feed_data.entries:
        return None

    # Try to find an entry with title, link and preferably a summary
    for entry in feed_data.entries:
        if hasattr(entry, 'link') and entry.link and urlparse(entry.link).scheme in ['http', 'https']:
            # Prioritize entries that have a title and summary/content
            if hasattr(entry, 'title') and (hasattr(entry, 'summary') or hasattr(entry, 'content')):
                return entry.link

    # Fall back to any entry with a valid link
    for entry in feed_data.entries:
        if hasattr(entry, 'link') and entry.link and urlparse(entry.link).scheme in ['http', 'https']:
            return entry.link

    return None 