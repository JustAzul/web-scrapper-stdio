from src.logger import Logger
from .rate_limiting import apply_rate_limiting, get_domain_from_url
from .content_selectors import _wait_for_content_stabilization
from .errors import _navigate_and_handle_errors

logger = Logger(__name__)


async def navigate_page(page, url, timeout_seconds, wait_for_network_idle=True):
    await apply_rate_limiting(url)
    logger.debug(f"Navigating to URL: {url}")
    response, nav_error = await _navigate_and_handle_errors(page, url, timeout_seconds)
    if nav_error:
        return None, nav_error

    logger.debug(f"Waiting for content to stabilize on {page.url}")
    domain = get_domain_from_url(page.url)
    content_found = await _wait_for_content_stabilization(
        page, domain, timeout_seconds, wait_for_network_idle
    )
    if not content_found:
        logger.warning(f"<body> tag not found for {page.url}")
        return None, "[ERROR] <body> tag not found."

    return response, None
