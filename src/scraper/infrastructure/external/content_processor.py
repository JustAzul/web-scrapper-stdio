"""
ContentProcessor - Responsabilidade única: Processamento de conteúdo HTML
Parte da refatoração T002 - Quebrar ChunkedHTMLProcessor seguindo SRP
"""

import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from src.core.constants import NOISE_SELECTORS
from .html_utils import remove_elements


class ContentProcessor:
    """Processa conteúdo HTML seguindo Single Responsibility Principle"""

    def __init__(self, parser: str = "html.parser", extra_noise_cleanup: bool = False):
        self.parser = parser
        self.extra_noise_cleanup = extra_noise_cleanup
        self.noise_selectors = NOISE_SELECTORS

    def extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extrai título do HTML

        Args:
            soup: BeautifulSoup object do HTML

        Returns:
            Título da página ou string vazia se não encontrado
        """
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return ""

    def remove_unwanted_elements(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> None:
        """
        Remove elementos indesejados do HTML

        Args:
            soup: BeautifulSoup object para modificar
            elements_to_remove: Lista de tags para remover
        """
        remove_elements(soup, elements_to_remove)

        if self.extra_noise_cleanup:
            remove_elements(soup, self.noise_selectors)

    def extract_clean_content(self, element: Tag) -> Tuple[str, str]:
        """
        Extrai conteúdo limpo de um elemento

        Args:
            element: Elemento Tag para processar

        Returns:
            Tupla de (clean_html, text_content)
        """
        clean_html = str(element)
        text_content = element.get_text(separator="\n", strip=True)

        # Aplica normalização de texto igual ao html_utils original
        text_content = re.sub(r"\n\s*\n", "\n\n", text_content).strip()

        return clean_html, text_content

    def extract_content_chunked(
        self, soup: BeautifulSoup, elements_to_remove: List[str], chunking_strategy
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extrai conteúdo usando processamento chunked

        Args:
            soup: BeautifulSoup object do HTML
            elements_to_remove: Elementos para remover
            chunking_strategy: Estratégia de chunking a usar

        Returns:
            Tupla de (title, clean_html, text_content, error)
        """
        try:
            # Extrai título primeiro
            title = self.extract_title(soup)

            # Remove elementos indesejados
            self.remove_unwanted_elements(soup, elements_to_remove)

            # Identifica áreas de conteúdo
            content_areas = chunking_strategy.identify_content_areas(soup)

            all_text_chunks = []
            all_html_chunks = []

            # Processa cada área em chunks
            for area in content_areas:
                text_chunks, html_chunks = chunking_strategy.create_chunks_from_area(
                    area
                )
                all_text_chunks.extend(text_chunks)
                all_html_chunks.extend(html_chunks)

            # Combina todos os chunks
            combined_text = "\n\n".join(all_text_chunks)
            combined_html = "\n".join(all_html_chunks)

            return title, combined_html, combined_text, None

        except Exception as e:
            return None, None, None, f"Chunked processing failed: {str(e)}"

    def extract_content_original(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extrai conteúdo usando método original (não-chunked)

        Args:
            soup: BeautifulSoup object do HTML
            elements_to_remove: Elementos para remover

        Returns:
            Tupla de (title, clean_html, text_content, error)
        """
        try:
            # Extrai título primeiro
            title = self.extract_title(soup)

            # Remove elementos indesejados
            self.remove_unwanted_elements(soup, elements_to_remove)

            # Encontra elemento target (body ou html)
            target_element = soup.body if soup.body else soup

            if not target_element:
                return title, "", "", "[ERROR] Could not find body tag in HTML."

            # Extrai conteúdo limpo
            clean_html, text_content = self.extract_clean_content(target_element)

            return title, clean_html, text_content, None

        except Exception as e:
            return None, None, None, f"Original processing failed: {str(e)}"
