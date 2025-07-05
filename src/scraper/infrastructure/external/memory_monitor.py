from __future__ import annotations
import psutil
from typing import Optional
from logging import Logger

from src.logger import get_logger


class MemoryMonitor:
    def __init__(
        self, memory_limit_mb: int, enabled: bool, logger: Optional[Logger] = None
    ):
        self.memory_limit_mb = memory_limit_mb
        self.enabled = enabled
        self.logger = logger or get_logger(__name__)

    def __enter__(self):
        if not self.enabled:
            return self
        self.logger.debug("Entering memory monitoring context.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.enabled:
            return
        self.logger.debug("Exiting memory monitoring context.")

    def get_memory_usage(self) -> float:
        # Placeholder implementation
        return 0.0
