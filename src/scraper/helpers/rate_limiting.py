import asyncio
import time
from urllib.parse import urlparse
from src.logger import Logger
from src.config import DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS

logger = Logger(__name__)

_domain_access_times = {}
_domain_lock = asyncio.Lock()
MIN_SECONDS_BETWEEN_REQUESTS = DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS


def get_domain_from_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        if not domain:
            return None

        return domain.replace("www.", "")
    except ValueError:
        logger.warning(f"Could not parse domain from URL: {url}")

        return None


async def apply_rate_limiting(url: str):
    domain = get_domain_from_url(url)

    if not domain:
        logger.warning(f"No valid domain for rate limiting: {url}")
        return
    async with _domain_lock:
        current_time = time.time()
        last_access_time = _domain_access_times.get(domain)

        if last_access_time:
            time_since_last = current_time - last_access_time

            if time_since_last < MIN_SECONDS_BETWEEN_REQUESTS:
                sleep_duration = MIN_SECONDS_BETWEEN_REQUESTS - time_since_last

                logger.warning(
                    f"Rate limiting {domain}: Sleeping for {sleep_duration:.2f}s")
                await asyncio.sleep(sleep_duration)
                current_time = time.time()

        _domain_access_times[domain] = current_time
