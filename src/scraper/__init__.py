import asyncio
import random
from typing import List, Optional

from playwright.async_api import async_playwright

from src.config import (
    DEFAULT_MIN_CONTENT_LENGTH,
    DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP,
    DEFAULT_TIMEOUT_SECONDS,
)

# Imports for DI
from src.dependency_injection import container as global_container
from src.dependency_injection.application_bootstrap import ApplicationBootstrap
from src.enums import OutputFormat
from src.logger import Logger

from .api.handlers.content_extractor import ContentExtractor
from .api.handlers.output_formatter import OutputFormatter
from .application.services.scraping_orchestrator import ScrapingOrchestrator
from .application.services.url_validator import URLValidator
from .infrastructure.external.chunked_processor import (
    ChunkedHTMLProcessor,
    extract_clean_html_optimized,
)
from .infrastructure.external.content_selectors import _wait_for_content_stabilization
from .infrastructure.external.errors import (
    _handle_cloudflare_block,
    _navigate_and_handle_errors,
)
from .infrastructure.external.html_utils import (
    _extract_and_clean_html,
    _is_content_too_short,
)

# Updated imports for new Clean Architecture structure
from .infrastructure.web_scraping.rate_limiting import (
    apply_rate_limiting,
    get_domain_from_url,
)
from .utils import extract_clean_html

__all__ = [
    "extract_text_from_url",
    "extract_clean_html",
    "ChunkedHTMLProcessor",
    "OutputFormat",
    "ScrapingOrchestrator",
]

logger = Logger(__name__)

# Configure DI container on module load
if not global_container.is_configured():
    bootstrap = ApplicationBootstrap()
    bootstrap.configure_dependencies()


async def extract_text_from_url(
    url: str,
    custom_elements_to_remove: Optional[List[str]] = None,
    custom_timeout: Optional[int] = None,
    grace_period_seconds: float = 2.0,
    max_length: Optional[int] = None,
    user_agent: Optional[str] = None,
    wait_for_network_idle: bool = True,
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    click_selector: Optional[str] = None,
) -> dict:
    """Return primary text content from a web page.

    REFATORADO T002: Agora usa o sistema de Injeção de Dependência para obter
    o WebScrapingService, garantindo que o FallbackOrchestrator com a lógica
    de tratamento de erro correta seja usado.
    """
    try:
        # Resolve o serviço principal a partir do container de DI
        scraping_service = global_container.resolve("IWebScrapingService")

        # Delega a chamada para o serviço, que agora orquestra o processo
        return await scraping_service.scrape_url(
            url=url,
            custom_elements_to_remove=custom_elements_to_remove,
            custom_timeout=custom_timeout,
            grace_period_seconds=grace_period_seconds,
            max_length=max_length,
            user_agent=user_agent,
            wait_for_network_idle=wait_for_network_idle,
            output_format=output_format,
            click_selector=click_selector,
        )
    except Exception as e:
        logger.error(f"Error during DI-based scraping for {url}: {e}")
        return {
            "error": f"A critical error occurred: {e}",
            "final_url": url,
            "content": None,
            "title": None,
        }
