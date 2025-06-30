"""
ContentExtractor - Responsabilidade única: Extração de conteúdo de páginas web
Parte da refatoração T001 - Quebrar extract_text_from_url seguindo SRP
"""

import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional

from playwright.async_api import Page

from src.config import DEFAULT_MIN_CONTENT_LENGTH, DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP
from src.logger import Logger
from src.scraper import extract_clean_html
from src.core.constants import DEFAULT_CLICK_TIMEOUT_MS
from src.scraper.infrastructure.external.content_selectors import _wait_for_content_stabilization
from src.scraper.infrastructure.external.errors import _handle_cloudflare_block
from src.scraper.infrastructure.external.html_utils import _is_content_too_short

logger = Logger(__name__)


@dataclass
class ExtractionConfig:
    """Configuração para extração de conteúdo"""

    timeout_seconds: int = 30
    grace_period_seconds: float = 2.0
    elements_to_remove: List[str] = None
    wait_for_network_idle: bool = True
    click_selector: Optional[str] = None
    min_content_length: Optional[int] = None

    def __post_init__(self):
        if self.elements_to_remove is None:
            self.elements_to_remove = [
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


@dataclass
class ExtractionResult:
    """Resultado da extração de conteúdo"""

    title: Optional[str] = None
    content: Optional[str] = None
    clean_html: Optional[str] = None
    final_url: Optional[str] = None
    error: Optional[str] = None
    soup: Optional[Any] = None


class ContentExtractor:
    """Extrai conteúdo de páginas web seguindo Single Responsibility Principle"""

    def __init__(self):
        self.logger = logger

    async def extract(self, page: Page, config: ExtractionConfig) -> ExtractionResult:
        """
        Extrai conteúdo da página

        Args:
            page: Instância da página Playwright
            config: Configuração da extração

        Returns:
            Resultado da extração
        """
        try:
            # Aguardar estabilização do conteúdo
            content_found = await self._wait_for_content(page, config)
            if not content_found:
                return ExtractionResult(
                    final_url=page.url, error="[ERROR] <body> tag not found."
                )

            # Clicar em elemento se especificado
            if config.click_selector:
                await self._click_element(page, config.click_selector)

            # Aguardar período de graça
            await asyncio.sleep(config.grace_period_seconds)

            # Obter conteúdo HTML
            html_content = await page.content()

            # Verificar bloqueio Cloudflare
            is_blocked, cf_error = _handle_cloudflare_block(html_content, page.url)
            if is_blocked:
                return ExtractionResult(final_url=page.url, error=cf_error)

            # Extrair e limpar HTML
            result = await self._extract_and_clean_content(
                html_content, config, page.url
            )

            return result

        except Exception as e:
            self.logger.error(f"Erro durante extração de {page.url}: {e}")
            return ExtractionResult(
                final_url=page.url,
                error=f"[ERROR] Erro inesperado durante extração: {str(e)}",
            )

    async def _wait_for_content(self, page: Page, config: ExtractionConfig) -> bool:
        """Aguarda conteúdo estabilizar na página"""
        try:
            from src.scraper.infrastructure.web_scraping.rate_limiting import get_domain_from_url

            domain = get_domain_from_url(page.url)

            content_found = await _wait_for_content_stabilization(
                page, domain, config.timeout_seconds, config.wait_for_network_idle
            )

            return content_found

        except Exception as e:
            self.logger.warning(f"Erro aguardando estabilização em {page.url}: {e}")
            return False

    async def _click_element(self, page: Page, selector: str) -> None:
        """Clica em elemento se especificado"""
        try:
            self.logger.debug(f"Tentando clicar no seletor: {selector}")
            await page.click(selector, timeout=DEFAULT_CLICK_TIMEOUT_MS)
            self.logger.debug(f"Clicou no seletor: {selector}")
        except Exception as e:
            self.logger.warning(f"Não foi possível clicar no seletor '{selector}': {e}")

    async def _extract_and_clean_content(
        self, html_content: str, config: ExtractionConfig, url: str
    ) -> ExtractionResult:
        """Extrai e limpa conteúdo HTML"""
        try:
            # Usar função existente para compatibilidade
            page_title, clean_html, text_content, content_error, soup = (
                extract_clean_html(html_content, config.elements_to_remove, url)
            )

            if content_error:
                return ExtractionResult(final_url=url, error=content_error)

            # Verificar se conteúdo é muito curto
            min_length = self._get_min_content_length(url, config)
            if _is_content_too_short(text_content, min_length):
                self.logger.warning(
                    f"Conteúdo muito curto extraído (< {min_length}) em {url}"
                )
                return ExtractionResult(
                    title=page_title,
                    final_url=url,
                    error=f"[ERROR] Conteúdo muito curto (menos de {min_length} caracteres).",
                )

            return ExtractionResult(
                title=page_title,
                content=text_content,
                clean_html=clean_html,
                final_url=url,
                soup=soup,
            )

        except Exception as e:
            self.logger.error(f"Erro processando HTML de {url}: {e}")
            return ExtractionResult(
                final_url=url, error=f"[ERROR] Erro processando HTML: {str(e)}"
            )

    def _get_min_content_length(self, url: str, config: ExtractionConfig) -> int:
        """Determina comprimento mínimo baseado na URL"""
        if config.min_content_length is not None:
            return config.min_content_length

        from src.scraper.infrastructure.web_scraping.rate_limiting import get_domain_from_url

        domain = get_domain_from_url(url)

        return (
            DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP
            if domain and "search.app" in domain
            else DEFAULT_MIN_CONTENT_LENGTH
        )
