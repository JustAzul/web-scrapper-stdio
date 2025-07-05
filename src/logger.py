import logging
import os
import sys

def get_logger(name="mcp-web-scrapper"):
    """
    Configures and returns a standardized logger instance.
    This replaces the complex singleton class with a simple factory function.
    """
    logger = logging.getLogger(name)

    # Set level from environment variable, default to INFO
    if os.environ.get("DEBUG_LOGS_ENABLED", "false").lower() == "true":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Configure handler only if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# For backward compatibility, create a "default" logger instance
# that other modules can import and use directly.
Logger = get_logger
