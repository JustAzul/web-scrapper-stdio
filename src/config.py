import os


def _get_env_int(var, default):
    try:
        return int(os.getenv(var, default))
    except Exception:
        return default


def _get_env_float(var, default):
    try:
        return float(os.getenv(var, default))
    except Exception:
        return default


# Timeout for page loads and navigation (in seconds)
DEFAULT_TIMEOUT_SECONDS = _get_env_int("DEFAULT_TIMEOUT_SECONDS", 30)
# Minimum content length required for extracted text (in characters)
DEFAULT_MIN_CONTENT_LENGTH = _get_env_int("DEFAULT_MIN_CONTENT_LENGTH", 100)
# Lower minimum content length for search.app domains (in characters)
DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP = 30
# Minimum delay between requests to the same domain (in seconds)
DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = _get_env_float(
    "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS", 2)
# Timeout for test requests (in seconds)
DEFAULT_TEST_REQUEST_TIMEOUT = _get_env_int("DEFAULT_TEST_REQUEST_TIMEOUT", 10)
# Threshold for skipping artificial delays in tests (in seconds)
DEFAULT_TEST_NO_DELAY_THRESHOLD = _get_env_float(
    "DEFAULT_TEST_NO_DELAY_THRESHOLD", 0.5)

# Debug logging toggle
DEBUG_LOGS_ENABLED = os.getenv("DEBUG_LOGS_ENABLED", "false").lower() == "true"

# Grace period: time to wait for JS rendering after navigation (in seconds)
DEFAULT_GRACE_PERIOD_SECONDS = _get_env_float(
    "DEFAULT_GRACE_PERIOD_SECONDS", 0.5)

# Browser pool settings
BROWSER_POOL_ENABLED = os.getenv(
    "BROWSER_POOL_ENABLED", "true").lower() == "true"
BROWSER_POOL_SIZE = _get_env_int("BROWSER_POOL_SIZE", 2)

# Transport settings
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_HTTP_PORT = _get_env_int("MCP_HTTP_PORT", 8080)
MCP_HTTP_HOST = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
