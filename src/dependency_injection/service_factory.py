"""
Service Factory
Responsabilidade única: Criar serviços complexos com dependências injetadas
"""

from typing import Any

from .di_container import DIContainer


class ServiceFactory:
    """Factory para criação de serviços com dependências injetadas"""

    def __init__(self, container: DIContainer):
        self.container = container

    def create_web_scraping_service(self) -> Any:
        """
        Cria WebScrapingService com dependências injetadas

        Returns:
            Instância do WebScrapingService configurado
        """
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        # Resolve dependências
        browser_factory = self.container.resolve("IBrowserFactory")
        content_processor = self.container.resolve("IContentProcessingService")
        configuration_service = self.container.resolve("IScrapingConfigurationService")
        orchestrator = self.container.resolve("FallbackOrchestrator")

        # Cria serviço com dependências injetadas
        return WebScrapingService(
            content_processor=content_processor,
            orchestrator=orchestrator,
        )

    def create_mcp_request_handler(self) -> Any:
        """
        Cria MCPRequestHandler com dependências injetadas

        Returns:
            Instância do MCPRequestHandler configurado
        """
        from src.mcp_server_refactored import MCPRequestHandler

        # Resolve dependências
        web_service = self.container.resolve("IWebScrapingService")
        validator = self.container.resolve("IMCPParameterValidator")
        formatter = self.container.resolve("IMCPResponseFormatter")

        # Cria handler com dependências injetadas
        return MCPRequestHandler(
            scraper_service=web_service, validator=validator, formatter=formatter
        )

    def create_mcp_parameter_validator(self) -> Any:
        """
        Cria MCPParameterValidator

        Returns:
            Instância do MCPParameterValidator
        """
        from src.mcp_server_refactored import MCPParameterValidator

        return MCPParameterValidator()

    def create_mcp_response_formatter(self) -> Any:
        """
        Cria MCPResponseFormatter

        Returns:
            Instância do MCPResponseFormatter
        """
        from src.mcp_server_refactored import MCPResponseFormatter

        return MCPResponseFormatter()
