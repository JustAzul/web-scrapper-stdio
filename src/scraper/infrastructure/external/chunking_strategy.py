"""
ChunkingStrategy - Responsabilidade única: Estratégia de chunking de conteúdo
Parte da refatoração T002 - Quebrar ChunkedHTMLProcessor seguindo SRP
"""

from typing import List

from bs4 import BeautifulSoup, Tag

from src.core.constants import CONTENT_AREA_PATTERNS, DEFAULT_CHUNK_SIZE_THRESHOLD


class ChunkingStrategy:
    """Determina estratégia de chunking para processamento de conteúdo seguindo SRP"""

    def __init__(
        self,
        chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
        enable_chunking: bool = True,
    ):
        self.chunk_size_threshold = chunk_size_threshold
        self.enable_chunking = enable_chunking

    def should_use_chunked_processing(self, html_content: str) -> bool:
        """
        Determina se deve usar processamento chunked

        Args:
            html_content: Conteúdo HTML para analisar

        Returns:
            True se deve usar chunking, False caso contrário
        """
        if not self.enable_chunking:
            return False

        return len(html_content) > self.chunk_size_threshold

    def identify_content_areas(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Identifica áreas de conteúdo no HTML

        Args:
            soup: BeautifulSoup object do HTML

        Returns:
            Lista de elementos Tag representando áreas de conteúdo
        """
        content_areas = []

        # Primeiro, procura elementos semânticos de conteúdo principal
        main_elements = soup.find_all(["main", "article"])
        if main_elements:
            content_areas.extend(main_elements)

        # Procura áreas de conteúdo por padrões de class/id
        for pattern in CONTENT_AREA_PATTERNS:
            # Busca por class
            elements = soup.find_all(class_=lambda x: x and pattern in x.lower())
            content_areas.extend(elements)

            # Busca por id
            elements = soup.find_all(id=lambda x: x and pattern in x.lower())
            content_areas.extend(elements)

        # Se não encontrou áreas de conteúdo, usa body ou soup inteiro
        if not content_areas:
            if soup.body:
                content_areas.append(soup.body)
            else:
                content_areas.append(soup)

        # Remove duplicatas preservando ordem
        seen = set()
        unique_areas = []
        for area in content_areas:
            if area not in seen:
                seen.add(area)
                unique_areas.append(area)

        return unique_areas

    def create_chunks_from_area(self, area: Tag) -> tuple[List[str], List[str]]:
        """
        Cria chunks de texto e HTML a partir de uma área de conteúdo

        Args:
            area: Elemento Tag para processar

        Returns:
            Tupla de (text_chunks, html_chunks)
        """
        text_chunks = []
        html_chunks = []
        current_chunk_size = 0
        current_chunk_elements = []

        def process_current_chunk():
            if current_chunk_elements:
                # Cria novo soup para o chunk
                chunk_soup = BeautifulSoup("<div></div>", "html.parser")
                chunk_div = chunk_soup.div

                # Adiciona todos elementos ao chunk
                for element in current_chunk_elements:
                    # Cria cópia para evitar modificar original
                    element_copy = BeautifulSoup(str(element), "html.parser").contents[
                        0
                    ]
                    chunk_div.append(element_copy)

                # Extrai texto e HTML
                text_chunks.append(chunk_div.get_text(separator="\n", strip=True))
                html_chunks.append(str(chunk_div))

                # Limpa chunk atual
                current_chunk_elements.clear()
                nonlocal current_chunk_size
                current_chunk_size = 0

        # Processa cada filho direto da área
        for element in area.children:
            if isinstance(element, Tag):
                element_size = len(str(element))

                # Se adicionar este elemento excederia o tamanho do chunk,
                # processa chunk atual
                if current_chunk_size + element_size > self.chunk_size_threshold:
                    process_current_chunk()

                # Adiciona elemento ao chunk atual
                current_chunk_elements.append(element)
                current_chunk_size += element_size

        # Processa elementos restantes
        if current_chunk_elements:
            process_current_chunk()

        return text_chunks, html_chunks
