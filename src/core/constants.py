"""
Constants module for the scraper.

This module centralizes all magic numbers and strings into named constants
with clear meanings, improving code readability and maintainability.
"""

# =============================================================================
# TIMEOUT CONSTANTS
# =============================================================================

MAX_TIMEOUT_SECONDS = 240
DEFAULT_CONFIG_TIMEOUT = 30  # Default timeout for Playwright operations
DEFAULT_FALLBACK_TIMEOUT = 15  # Default timeout for HTTPX fallback
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60  # Default recovery timeout for circuit breaker

DEFAULT_CLICK_TIMEOUT_MS = 3000
MILLISECONDS_PER_SECOND = 1000

# Timeout for network to be idle (in milliseconds)
NETWORK_IDLE_TIMEOUT_MS = 500

# Timeout for clicking selectors (in milliseconds) - replaces magic number 5000
SELECTOR_CLICK_TIMEOUT_MS = 5000


# =============================================================================

# HTTP success status - replaces magic number 200
HTTP_SUCCESS_STATUS = 200

# HTTP client error threshold - replaces magic number 400
HTTP_CLIENT_ERROR_THRESHOLD = 400


# =============================================================================


# Maximum timeout for MCP validation (in seconds) - replaces magic number 30

# Maximum grace period for MCP validation (in seconds) - replaces magic number 120


# =============================================================================
# =============================================================================

# Memory unit conversions
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024
MB_PER_KB = 1024

# =============================================================================
# PROCESSING CONSTANTS
# =============================================================================

# Maximum number of nodes to process in a single chunk
DEFAULT_CHUNK_NODE_LIMIT = 50

# HTML size threshold to trigger chunked processing (in bytes)
DEFAULT_CHUNK_SIZE_THRESHOLD = 100_000  # 100 KB

# Memory threshold multiplier for safety checks
MEMORY_THRESHOLD_MULTIPLIER = 1.2


# =============================================================================
# CONTENT CONSTANTS
# =============================================================================

MAX_CONTENT_LENGTH = 1_000_000  # 1 MB limit for scraped content

# Threshold for considering content "large" (in KB)


# =============================================================================
# BROWSER CONSTANTS
# =============================================================================

# Default browser viewports for randomization
DEFAULT_BROWSER_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
    {"width": 1280, "height": 800},
]

# Default user agents for randomization
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Default accept languages for randomization
DEFAULT_ACCEPT_LANGUAGES = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7"]


# =============================================================================
# ERROR PATTERN CONSTANTS
# =============================================================================

# Patterns that indicate a 404 or "not found" page
NOT_FOUND_PATTERNS = [
    r"404 Not Found",
    r"Page Not Found",
    r"couldn't find this page",
    r"can't find page",
    r"doesn't exist",
    r"Oops! Nothing was found",
]

# Patterns that indicate a Cloudflare challenge page
CLOUDFLARE_PATTERNS = [
    r"Attention Required! \| Cloudflare",
    r"cf-browser-verification",
    r"Checking your browser before accessing",
    r"Please enable JavaScript and Cookies to continue",
    r"Cloudflare Ray ID",
    r"cloudflare.com/speedtest",
    r"Why do I have to complete a CAPTCHA?",
]


# =============================================================================
# HTML ELEMENT CONSTANTS
# =============================================================================

# Default HTML elements to remove during processing
DEFAULT_ELEMENTS_TO_REMOVE = [
    "script",
    "style",
    "nav",
    "footer",
    "aside",
    "header",
    "form",
    "button",
    "input",
    "select",
    "textarea",
    "label",
    "iframe",
    "figure",
    "figcaption",
]

# Noise selectors for extra cleanup
NOISE_SELECTORS = [
    "nav",
    "header",
    "footer",
    "aside",
    "sidebar",
    ".nav",
    ".navigation",
    ".header",
    ".footer",
    ".sidebar",
    ".advertisement",
    ".ads",
    ".banner",
    ".social-media",
    ".comments",
    ".related",
    ".recommended",
]

# Content area patterns for identification
CONTENT_AREA_PATTERNS = [
    "content",
    "article",
    "post",
    "entry",
    "main",
    "body",
    "text",
    "story",
]

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Maximum timeout for MCP validation (in seconds) - replaces magic number 30
MAX_TIMEOUT_VALIDATION = 30

# Maximum grace period for MCP validation (in seconds) - replaces magic number 120
MAX_GRACE_PERIOD_VALIDATION = 120

# Threshold for considering content "large" (in KB)
LARGE_CONTENT_THRESHOLD_KB = 500


# =============================================================================
# BROWSER CONSTANTS
# =============================================================================
