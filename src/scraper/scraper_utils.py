from src.logger import get_logger

logger = get_logger(__name__)


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
        A tuple of ``(title, clean_html, text_content, error, soup)`` where
        ``error`` is ``None`` when extraction succeeds.
    """
    # REFATORAÇÃO: Usar implementação centralizada
    from .domain.value_objects.extraction_config import ExtractionConfig
    from .infrastructure.web_scraping.html_extractor import (
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
