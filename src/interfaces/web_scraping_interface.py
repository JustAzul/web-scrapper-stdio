"""
Interface abstrata para Web Scraping Service
Responsabilidade: Definir contrato para serviços de web scraping
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IWebScrapingService(ABC):
    """Interface abstrata para serviço de web scraping"""

    @abstractmethod
    async def scrape_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza scraping de uma URL

        Args:
            url: URL a ser processada
            **kwargs: Parâmetros adicionais

        Returns:
            Resultado do scraping
        """
        pass

    @abstractmethod
    async def extract_content(
        self, url: str, config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Extrai conteúdo de uma URL

        Args:
            url: URL a ser processada
            config: Configurações opcionais

        Returns:
            Conteúdo extraído
        """
        pass
