import logging

from .chunked_processor import ChunkedHTMLProcessor


def extract_clean_html(html_content: str, elements_to_remove: list, url: str):
    """
    REFATORADO T005: Agora usa CentralizedHTMLExtractor para eliminar duplicação
    Mantém compatibilidade com interface helpers
    """
    # REFATORAÇÃO: Usar implementação centralizada
    from ...domain.value_objects.extraction_config import ExtractionConfig
    from ..web_scraping.centralized_html_extractor import get_centralized_extractor

    # Criar configuração compatível
    config = ExtractionConfig(
        elements_to_remove=elements_to_remove,
        use_chunked_processing=True,
        enable_fallback=True,
    )

    # Usar extrator centralizado
    extractor = get_centralized_extractor()
    return extractor.extract_clean_html(html_content, url, config)
