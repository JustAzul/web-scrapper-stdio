import os
# Default configuration values
# Timeout for page loads and navigation (in seconds)
DEFAULT_TIMEOUT_SECONDS = 30
# Minimum content length required for extracted text (in characters)
DEFAULT_MIN_CONTENT_LENGTH = 100
# Lower minimum content length for search.app domains (in characters)
DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP = 30
# Minimum delay between requests to the same domain (in seconds)
DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = 2
# Wait time for domain-specific selectors to appear (in milliseconds)
DEFAULT_SELECTOR_WAIT_DOMAIN_MS = 3000
# Wait time for generic selectors to appear (in milliseconds)
DEFAULT_SELECTOR_WAIT_GENERIC_MS = 2000
# Short grace period to allow JS to finish rendering (in seconds)
DEFAULT_GRACE_PERIOD_SECONDS = 1
# Timeout for test requests (in seconds)
DEFAULT_TEST_REQUEST_TIMEOUT = 10
# Threshold for skipping artificial delays in tests (in seconds)
DEFAULT_TEST_NO_DELAY_THRESHOLD = 0.5
# Maximum allowed content length for extracted text (in characters)
DEFAULT_MAX_CONTENT_LENGTH = 5000

# Debug logging toggle
DEBUG_LOGS_ENABLED = os.getenv("DEBUG_LOGS_ENABLED", "false").lower() == "true"
