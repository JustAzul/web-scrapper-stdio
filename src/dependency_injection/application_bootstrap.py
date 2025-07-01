"""
Application Bootstrap
Responsabilidade única: Configurar e inicializar toda a aplicação com DI
"""

from typing import Any

from mcp.server import Server
from mcp.types import Prompt, PromptArgument, Tool

from src.logger import Logger

# Importa o container global
from . import container as global_container
from .service_factory import ServiceFactory


class ApplicationBootstrap:
    """Bootstrap para configuração da aplicação com Dependency Injection"""

    def __init__(self):
        self.logger = Logger(__name__)

    def configure_dependencies(self) -> None:
        """
        Configura todas as dependências no container DI global
        """
        # Registra implementações concretas como singletons
        global_container.register_singleton(
            "IBrowserFactory", lambda: self._create_browser_factory()
        )

        global_container.register_singleton(
            "IContentProcessingService",
            lambda: self._create_content_processing_service(),
        )

        global_container.register_singleton(
            "IScrapingConfigurationService",
            lambda: self._create_scraping_configuration_service(),
        )

        # Registra o orquestrador como um serviço central
        global_container.register_singleton(
            "FallbackOrchestrator", lambda: self._create_fallback_orchestrator()
        )

        # Registra serviços compostos
        global_container.register_singleton(
            "IWebScrapingService",
            lambda: self._create_web_scraping_service_with_dependencies(),
        )

        # Registra componentes MCP
        global_container.register_singleton(
            "IMCPParameterValidator", lambda: self._create_mcp_parameter_validator()
        )

        global_container.register_singleton(
            "IMCPResponseFormatter", lambda: self._create_mcp_response_formatter()
        )

        # Marca o container como configurado
        global_container.set_configured()

    def get_scraping_orchestrator(self) -> Any:
        """Retorna a instância do orquestrador de scraping."""
        return global_container.resolve("FallbackOrchestrator")

    def _create_browser_factory(self):
        """Cria instância de FallbackBrowserFactory"""
        from src.scraper.infrastructure.web_scraping.fallback_browser_automation import (
            FallbackBrowserFactory,
        )

        return FallbackBrowserFactory()

    def _create_content_processing_service(self):
        """Cria instância de ContentProcessingService"""
        from src.scraper.application.services.content_processing_service import (
            ContentProcessingService,
        )

        return ContentProcessingService()

    def _create_scraping_configuration_service(self):
        """Cria instância de ScrapingConfigurationService"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        return ScrapingConfigurationService()

    def _create_fallback_orchestrator(self):
        """Cria uma instância singleton do FallbackOrchestrator."""
        from src.scraper.application.services.fallback_orchestrator import (
            FallbackOrchestrator,
        )

        return FallbackOrchestrator()

    def _create_web_scraping_service_with_dependencies(self):
        """Cria WebScrapingService com dependências resolvidas"""
        factory = ServiceFactory(global_container)
        return factory.create_web_scraping_service()

    def _create_mcp_parameter_validator(self):
        """Cria instância de MCPParameterValidator"""
        from src.mcp_server_refactored import MCPParameterValidator

        return MCPParameterValidator()

    def _create_mcp_response_formatter(self):
        """Cria instância de MCPResponseFormatter"""
        from src.mcp_server_refactored import MCPResponseFormatter

        return MCPResponseFormatter()

    async def create_server(self) -> Server:
        """
        Cria servidor MCP com todas as dependências configuradas

        Returns:
            Servidor MCP configurado e pronto para uso
        """
        self.logger.info("Inicializando servidor MCP com Dependency Injection")

        # Configura o container global
        self.configure_dependencies()

        # Cria factory para serviços complexos
        factory = ServiceFactory(global_container)

        # Cria servidor MCP
        server = Server("mcp-web-scrapper")

        # Cria request handler com dependências injetadas
        request_handler = factory.create_mcp_request_handler()

        # Registra tools
        @server.list_tools()
        async def handle_list_tools():
            return [
                Tool(
                    name="scrape_web",
                    description="Extract and clean text content from a web page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to scrape"},
                            "output_format": {
                                "type": "string",
                                "enum": ["text", "markdown", "html"],
                                "default": "markdown",
                                "description": "Output format for the extracted content",
                            },
                            "max_length": {
                                "type": "integer",
                                "description": "Maximum length of extracted content",
                            },
                            "elements_to_remove": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "CSS selectors for elements to remove",
                            },
                            "custom_timeout": {
                                "type": "number",
                                "description": "Custom timeout in seconds",
                            },
                            "user_agent": {
                                "type": "string",
                                "description": "Custom User-Agent string",
                            },
                            "grace_period_seconds": {
                                "type": "number",
                                "description": "Grace period to wait for dynamic content",
                            },
                            "wait_for_network_idle": {
                                "type": "boolean",
                                "description": "Whether to wait for network idle",
                            },
                            "click_selector": {
                                "type": "string",
                                "description": "CSS selector to click before extraction",
                            },
                        },
                        "required": ["url"],
                    },
                )
            ]

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            if name == "scrape_web":
                return await request_handler.handle_tool_request(name, arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        # Registra prompts
        @server.list_prompts()
        async def handle_list_prompts():
            return [
                Prompt(
                    name="scrape",
                    description="Scrape content from a web page",
                    arguments=[
                        PromptArgument(
                            name="url", description="URL to scrape", required=True
                        ),
                        PromptArgument(
                            name="output_format",
                            description="Output format (text, markdown, html)",
                            required=False,
                        ),
                    ],
                )
            ]

        @server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict):
            if name == "scrape":
                return await request_handler.handle_prompt_request(name, arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")

        self.logger.info("Servidor MCP configurado com sucesso via DI")
        return server
