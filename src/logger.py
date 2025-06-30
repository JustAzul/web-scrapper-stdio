import logging
import os
import sys
from typing import Any


class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

        # Always ensure handler is present for new loggers or when forced
        if not self.logger.hasHandlers() or not hasattr(self, "_handler_configured"):
            self._configure_handler()
            self._handler_configured = True

        # Set level based on current environment (dynamic)
        debug_enabled = os.getenv("DEBUG_LOGS_ENABLED", "false").lower() == "true"
        self.logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)

    def _configure_handler(self):
        """Configure logging handler with proper formatting."""
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, message: str, *args: Any, **kwargs: Any):
        """Log message with INFO level, supporting string formatting."""
        self.logger.info(message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any):
        """Log debug message with string formatting support."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any):
        """Log info message with string formatting support."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any):
        """Log warning message with string formatting support."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any):
        """Log error message with string formatting support."""
        self.logger.error(message, *args, **kwargs)
