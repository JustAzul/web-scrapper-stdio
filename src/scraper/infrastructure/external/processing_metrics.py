import time
from logging import Logger
from typing import Any, Dict, Optional

from src.logger import get_logger


class ProcessingMetrics:
    def __init__(self, enabled: bool, logger: Optional[Logger] = None):
        self.enabled = enabled
        self.logger = logger or get_logger(__name__)
        self.last_metrics: Dict[str, Any] = {}

    def start_processing(self) -> float:
        if not self.enabled:
            return 0.0
        return time.time()

    def record_processing_success(self, start_time: float, **kwargs):
        if not self.enabled:
            return

        processing_time = time.time() - start_time
        self.last_metrics = {**kwargs, "processing_time": processing_time}
        self.logger.debug(f"Processing success metrics recorded: {self.last_metrics}")

    def record_processing_error(self, start_time: float, **kwargs):
        if not self.enabled:
            return

        processing_time = time.time() - start_time
        self.last_metrics = {**kwargs, "processing_time": processing_time}
        self.logger.debug(f"Processing error metrics recorded: {self.last_metrics}")

    def get_last_metrics(self) -> Dict[str, Any]:
        return self.last_metrics
