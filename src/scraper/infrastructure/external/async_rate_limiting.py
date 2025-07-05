from __future__ import annotations

import asyncio
import time
from logging import Logger
from typing import Dict, Optional
from urllib.parse import urlparse

from src.logger import get_logger
from src.settings import DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS


class AsyncRateLimiter:
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or get_logger(__name__)
        self._last_request_times: Dict[str, float] = {}
        self.min_seconds_between_requests = DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS

    async def get_domain_from_url_async(self, url: str) -> Optional[str]:
        try:
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                return parsed_url.netloc
            return None
        except Exception:
            return None

    async def apply_rate_limiting(self, url: str):
        if not self.enabled:
            return

        domain = await self.get_domain_from_url_async(url)
        if not domain:
            return

        current_time = time.time()
        last_request_time = self._last_request_times.get(domain, 0)
        time_since_last = current_time - last_request_time

        if time_since_last < self.min_seconds_between_requests:
            sleep_duration = self.min_seconds_between_requests - time_since_last
            self.logger.debug(
                f"Rate limiting domain '{domain}': sleeping for {sleep_duration:.2f}s"
            )
            await asyncio.sleep(sleep_duration)

        self._last_request_times[domain] = time.time()

    @property
    def enabled(self) -> bool:
        # Placeholder
        return True
