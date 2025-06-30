"""
RequestsScrapingStrategy - Responsabilidade única: Scraping com HTTP requests
Parte da refatoração T003 - Quebrar IntelligentFallbackScraper seguindo SRP
"""

from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup


class RequestsScrapingStrategy:
    """Estratégia de scraping usando HTTP requests seguindo SRP"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.timeout = config.requests_timeout

    async def scrape_url(
        self, url: str, headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Faz scraping de URL usando HTTP requests

        Args:
            url: URL para fazer scraping
            headers: Headers opcionais

        Returns:
            Conteúdo HTML limpo
        """
        default_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; IntelligentScraper/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=default_headers)
            response.raise_for_status()

            return self._clean_html_content(response.text)

    def _clean_html_content(self, html_content: str) -> str:
        """Limpa conteúdo HTML removendo elementos indesejados"""
        soup = BeautifulSoup(html_content, "html.parser")

        unwanted_tags = [
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
        ]

        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        return str(soup)
