"""
CentralizedHTMLExtractor - Responsabilidade única: Extração centralizada de HTML
Elimina duplicação de extract_clean_html em múltiplos locais
"""

from typing import Any, Optional, Tuple

from bs4 import BeautifulSoup

from src.logger import get_logger

from ...domain.value_objects.extraction_config import ExtractionConfig


class CentralizedHTMLExtractor:
    """Extrator HTML centralizado que elimina duplicação de código"""

    def __init__(self, extraction_strategy: Optional[Any] = None):
        """
        Inicializa extrator com estratégia opcional

        Args:
            extraction_strategy: Estratégia de extração injetada (para testes)
        """
        self.logger = get_logger(__name__)
        self._extraction_strategy = extraction_strategy

    def extract_clean_html(
        self, html_content: str, url: str, config: Optional[ExtractionConfig] = None
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """
        Extrai HTML limpo usando configuração parametrizada

        Args:
            html_content: Conteúdo HTML para processar
            url: URL sendo processada
            config: Configuração de extração (usa padrão se None)

        Returns:
            Tupla de (title, clean_html, text_content, error, soup)
        """
        if config is None:
            config = ExtractionConfig()

        try:
            # Validar entrada
            if not html_content or not html_content.strip():
                return "", "", "", None, None

            # Determinar estratégia de extração
            if config.use_chunked_processing and self._should_use_chunked(
                html_content, config
            ):
                return self._extract_using_chunked_strategy(html_content, url, config)
            else:
                return self._extract_using_original_strategy(html_content, url, config)

        except Exception as e:
            error_msg = f"[ERROR] HTML extraction failed: {str(e)}"
            self.logger.error(f"Error extracting from {url}: {error_msg}")
            return "", "", "", error_msg, None

    def configure(self, config: ExtractionConfig) -> None:
        """
        Configura extrator com nova configuração

        Args:
            config: Nova configuração a aplicar
        """
        # Valida configuração
        config.__post_init__()
        self.logger.debug(f"Extractor configured with: {config}")

    def _should_use_chunked(self, html_content: str, config: ExtractionConfig) -> bool:
        """Determina se deve usar processamento chunked"""
        content_size = len(html_content.encode("utf-8"))
        return content_size > config.chunk_size_threshold

    def _extract_using_chunked_strategy(
        self, html_content: str, url: str, config: ExtractionConfig
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """Extrai usando estratégia chunked"""
        try:
            # Usar processor chunked refatorado existente
            from src.scraper.infrastructure.external.refactored_chunked_processor import (
                extract_clean_html,
            )

            self.logger.debug(f"Using chunked processing for {url}")

            result = extract_clean_html(
                html_content,
                elements_to_remove=config.elements_to_remove,
                url=url,
                enable_chunking=True,
                memory_limit_mb=config.memory_limit_mb,
                chunk_size_threshold=config.chunk_size_threshold,
                parser=config.parser,
                extra_noise_cleanup=config.extra_noise_cleanup,
                fallback_enabled=config.enable_fallback,
            )

            return result

        except Exception as e:
            if config.enable_fallback:
                self.logger.warning(
                    f"Chunked processing failed for {url}, falling back: {e}"
                )
                return self._extract_using_original_strategy(html_content, url, config)
            else:
                raise

    def _extract_using_original_strategy(
        self, html_content: str, url: str, config: ExtractionConfig
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """Extrai usando estratégia original"""
        try:
            # Usar lógica original consolidada
            from src.scraper.infrastructure.external.html_utils import (
                _extract_and_clean_html,
            )

            self.logger.debug(f"Using original processing for {url}")

            soup, target_element = _extract_and_clean_html(
                html_content, config.elements_to_remove
            )

            if not target_element:
                return "", "", "", "[ERROR] Could not find body tag in HTML.", soup

            # Extrair título
            page_title = ""
            if soup.title and soup.title.string:
                page_title = soup.title.string.strip()

            # Extrair conteúdo
            clean_html = str(target_element)
            text_content = target_element.get_text(separator="\n", strip=True)

            # Normalizar texto (mesmo que implementações originais)
            import re

            text_content = re.sub(r"\n\s*\n", "\n\n", text_content).strip()

            return page_title, clean_html, text_content, None, soup

        except Exception as e:
            error_msg = f"Original processing failed: {str(e)}"
            self.logger.error(f"Error in original processing for {url}: {error_msg}")
            return "", "", "", error_msg, None

# Instância singleton para evitar recriação desnecessária
_extractor_instance: Optional[CentralizedHTMLExtractor] = None

def get_centralized_extractor() -> CentralizedHTMLExtractor:
    """
    Retorna instância singleton do extrator centralizado

    Returns:
        Instância do CentralizedHTMLExtractor
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = CentralizedHTMLExtractor()
    return _extractor_instance
