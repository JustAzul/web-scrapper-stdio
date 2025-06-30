import asyncio
import random
from typing import List, Optional

from playwright.async_api import async_playwright

from src.config import (
    DEFAULT_MIN_CONTENT_LENGTH,
    DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP,
    DEFAULT_TIMEOUT_SECONDS,
)
from src.logger import Logger
from src.output_format_handler import (
    OutputFormat,
    to_markdown,
    to_text,
    truncate_content,
)

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

__all__ = [
    "extract_text_from_url",
    "extract_clean_html",
    "ChunkedHTMLProcessor",
    "OutputFormat",
]

logger = Logger(__name__)


def extract_clean_html(html_content, elements_to_remove, url):
    """Clean and parse HTML and return sanitized body HTML and plain text.

    REFATORADO T005: Agora usa CentralizedHTMLExtractor para eliminar duplicação
    Mantém compatibilidade com interface original

    Parameters
    ----------
    html_content : str
        Raw HTML string from the page.
    elements_to_remove : list
        Tags to strip from the HTML before parsing.
    url : str
        Source URL, used for logging.

    Returns
    -------
    tuple
        A tuple of ``(title, clean_html, text_content, error, soup)`` where ``error`` is ``None`` when extraction succeeds.
    """
    # REFATORAÇÃO: Usar implementação centralizada
    from .domain.value_objects.extraction_config import ExtractionConfig
    from .infrastructure.web_scraping.centralized_html_extractor import (
        get_centralized_extractor,
    )

    # Criar configuração compatível com interface original
    config = ExtractionConfig(
        elements_to_remove=elements_to_remove,
        use_chunked_processing=True,  # Manter comportamento otimizado
        enable_fallback=True,
    )

    # Usar extrator centralizado
    extractor = get_centralized_extractor()
    title, clean_html, text_content, error, soup = extractor.extract_clean_html(
        html_content, url, config
    )

    # Manter compatibilidade: converter valores vazios para None quando há erro
    if error:
        return None, None, None, error, soup

    # Manter compatibilidade: verificar conteúdo vazio
    if not clean_html and not text_content:
        logger.warning(f"Could not find body tag for {url}")
        return None, None, None, "[ERROR] Could not find body tag in HTML.", soup

    return title, clean_html, text_content, None, soup


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

    REFATORADO T001: Agora usa ScrapingOrchestrator seguindo SRP
    Mantém compatibilidade com interface original

    Parameters
    ----------
    url : str
        Page URL to scrape.
    custom_elements_to_remove : list, optional
        Additional HTML tags to discard before extraction.
    custom_timeout : int, optional
        Override the default timeout value in seconds.
    grace_period_seconds : float, optional
        Time to wait after navigation before reading the page.
    max_length : Optional[int], optional
        If provided, truncate the extracted content to this number of characters.
    user_agent : Optional[str], optional
        Custom User-Agent string. A random one is used if not provided.
    wait_for_network_idle : bool, optional
        Whether to wait for network activity to settle before extracting content.
    output_format : OutputFormat, optional
        Desired output format for the returned content.
    click_selector : Optional[str], optional
        If provided, click the element matching this selector after navigation and before extraction.

    Returns
    -------
    dict
        Dictionary with ``title``, ``final_url``, ``content`` and an
        ``error`` message if one occurred.
    """
    # REFATORAÇÃO: Usar ScrapingOrchestrator ao invés de código monolítico
    from .application.services.scraping_orchestrator import ScrapingOrchestrator

    orchestrator = ScrapingOrchestrator()

    return await orchestrator.scrape_url(
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
