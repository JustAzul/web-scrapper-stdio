"""
PlaywrightScrapingStrategy - Responsabilidade única: Scraping com Playwright
Parte da refatoração T003 - Quebrar IntelligentFallbackScraper seguindo SRP
"""

from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from playwright.async_api import Page, Route, async_playwright


class PlaywrightScrapingStrategy:
    """Estratégia de scraping usando Playwright seguindo SRP"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.timeout = config.playwright_timeout
        self.enable_resource_blocking = config.enable_resource_blocking
        self.blocked_resource_types = config.blocked_resource_types

    async def scrape_url(
        self, url: str, headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Faz scraping de URL usando Playwright

        Args:
            url: URL para fazer scraping
            headers: Headers opcionais

        Returns:
            Conteúdo HTML limpo
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
            )

            try:
                context = await browser.new_context()
                page = await context.new_page()

                if self.enable_resource_blocking:
                    await self._setup_resource_blocking(page)

                response = await page.goto(
                    url, wait_until="domcontentloaded", timeout=self.timeout * 1000
                )

                if not response or response.status >= 400:
                    raise Exception(
                        f"HTTP {response.status if response else 'Unknown'}"
                    )

                content = await page.content()
                return self._clean_html_content(content)

            finally:
                await browser.close()

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
