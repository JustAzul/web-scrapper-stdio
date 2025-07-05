"""
PlaywrightScrapingStrategy - Responsabilidade única: Scraping com Playwright
Parte da refatoração T003 - Quebrar IntelligentFallbackScraper seguindo SRP
"""

from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, Route, async_playwright

from ...application.services.scraping_request import ScrapingRequest
from .scraping_strategy import ScrapingStrategy


class PlaywrightScrapingStrategy(ScrapingStrategy):
    """Estratégia de scraping usando Playwright seguindo SRP"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.timeout = config.playwright_timeout
        self.enable_resource_blocking = config.enable_resource_blocking
        self.blocked_resource_types = config.blocked_resource_types
        self._playwright = None
        self._browser: Optional[Browser] = None

    async def initialize(self):
        """Initializes the Playwright browser instance."""
        if not self._browser:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
            )

    async def shutdown(self):
        """Shuts down the Playwright browser instance."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def scrape_url(
        self, request: ScrapingRequest, headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Faz scraping de URL usando Playwright

        Args:
            request: Objeto com todos os parâmetros da requisição
            headers: Headers opcionais

        Returns:
            Conteúdo HTML limpo
        """
        if not self._browser:
            raise Exception("Playwright browser is not initialized.")

        try:
            context = await self._browser.new_context(extra_http_headers=headers)
            page = await context.new_page()

            if self.enable_resource_blocking:
                await self._setup_resource_blocking(page)

            response = await page.goto(
                request.url,
                wait_until="domcontentloaded",
                timeout=self.timeout * 1000,
            )

            if response and response.status >= 400:
                # Cria uma request e response mock para o erro
                mock_request = httpx.Request("GET", request.url)
                mock_response = httpx.Response(
                    status_code=response.status,
                    request=mock_request,
                    text=await response.text(),
                )
                raise httpx.HTTPStatusError(
                    f"HTTP error {response.status}",
                    request=mock_request,
                    response=mock_response,
                )

            if not response:
                raise Exception("Playwright failed to get a response.")

            content = await page.content()
            return self._clean_html_content(content)

        finally:
            if 'context' in locals() and context:
                await context.close()

    async def _setup_resource_blocking(self, page: Page) -> None:
        """Configura bloqueio de recursos para performance"""

        async def handle_route(route: Route) -> None:
            resource_type = route.request.resource_type
            if resource_type in self.blocked_resource_types:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", handle_route)

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
