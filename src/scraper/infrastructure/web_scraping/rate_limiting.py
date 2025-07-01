import asyncio
import time
from typing import Optional
from urllib.parse import urlparse

from src.config import DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS
from src.logger import Logger

logger = Logger(__name__)

_domain_access_times = {}
_domain_lock = asyncio.Lock()
MIN_SECONDS_BETWEEN_REQUESTS = DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS


def get_domain_from_url(url: str) -> Optional[str]:
    """Extracts the network location (domain) from a URL."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        # An invalid URL may parse with no scheme and no netloc
        if not parsed.scheme or not parsed.netloc:
            logger.warning(f"Could not parse domain from invalid URL: {url}")
            return None
        netloc = parsed.netloc
        if netloc.startswith("www."):
            return netloc[4:]
        return netloc
    except ValueError:
        logger.warning(f"Could not parse domain from invalid URL: {url}")
        return None


async def apply_rate_limiting(url: str):
    """Sleeps to enforce a minimum delay between requests to the same domain."""
    domain = get_domain_from_url(url)
    if not domain:
        return

    async with _domain_lock:
        current_time = time.time()
        last_access_time = _domain_access_times.get(domain)

        if last_access_time:
            time_since_last = current_time - last_access_time
            if time_since_last < MIN_SECONDS_BETWEEN_REQUESTS:
                sleep_duration = MIN_SECONDS_BETWEEN_REQUESTS - time_since_last
                logger.info(
                    f"Rate limiting {domain}: Sleeping for {sleep_duration:.2f}s"
                )
                await asyncio.sleep(sleep_duration)

        _domain_access_times[domain] = time.time()
