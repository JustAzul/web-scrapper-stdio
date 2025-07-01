"""
TDD Tests for T004: Implementar Inversão de Dependência main.py
Objetivo: Eliminar dependências hardcoded e implementar DIP

FASE RED: Testes que falham primeiro - definindo comportamento esperado após refatoração
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestDependencyInterfaces:
    """Testes para interfaces abstratas - responsabilidade única de contratos"""

    def test_browser_factory_interface_exists(self):
        """Deve existir interface abstrata para BrowserFactory"""
        from src.interfaces.browser_factory_interface import IBrowserFactory

        # Interface deve ter métodos abstratos
        assert hasattr(IBrowserFactory, "create_browser")
        assert hasattr(IBrowserFactory, "configure_browser")

        # Deve ser uma interface (Protocol ou ABC)
        assert hasattr(IBrowserFactory, "__abstractmethods__") or hasattr(
            IBrowserFactory, "_is_protocol"
        )

    def test_content_processing_interface_exists(self):
        """Deve existir interface abstrata para ContentProcessingService"""
        from src.interfaces.content_processing_interface import (
            IContentProcessingService,
        )

        assert hasattr(IContentProcessingService, "process_content")
        assert hasattr(IContentProcessingService, "extract_text")

    def test_scraping_configuration_interface_exists(self):
        """Deve existir interface abstrata para ScrapingConfigurationService"""
        from src.interfaces.scraping_configuration_interface import (
            IScrapingConfigurationService,
        )

        assert hasattr(IScrapingConfigurationService, "get_configuration")
        assert hasattr(IScrapingConfigurationService, "validate_parameters")

    def test_web_scraping_interface_exists(self):
        """Deve existir interface abstrata para WebScrapingService"""
        from src.interfaces.web_scraping_interface import IWebScrapingService

        assert hasattr(IWebScrapingService, "scrape_url")
        assert hasattr(IWebScrapingService, "extract_content")


class TestDependencyInjectionContainer:
    """Testes para DI Container - responsabilidade única de gerenciamento de dependências"""

    def test_di_container_initialization(self):
        """Deve inicializar container de DI"""
        from src.dependency_injection.di_container import DIContainer

        container = DIContainer()
        assert container is not None
        assert hasattr(container, "register")
        assert hasattr(container, "resolve")
        assert hasattr(container, "register_singleton")

    def test_di_container_register_transient(self):
        """Deve registrar dependências transientes"""
        from src.dependency_injection.di_container import DIContainer
        from src.interfaces.browser_factory_interface import IBrowserFactory

        container = DIContainer()

        # Mock implementation
        mock_factory = Mock(spec=IBrowserFactory)

        # Registra dependência
        container.register(IBrowserFactory, lambda: mock_factory)

        # Resolve dependência
        resolved = container.resolve(IBrowserFactory)
        assert resolved == mock_factory

    def test_di_container_register_singleton(self):
        """Deve registrar dependências singleton"""
        from src.dependency_injection.di_container import DIContainer
        from src.interfaces.content_processing_interface import (
            IContentProcessingService,
        )

        container = DIContainer()
        mock_service = Mock(spec=IContentProcessingService)

        # Registra como singleton
        container.register_singleton(IContentProcessingService, lambda: mock_service)

        # Resolve múltiplas vezes - deve retornar a mesma instância
        resolved1 = container.resolve(IContentProcessingService)
        resolved2 = container.resolve(IContentProcessingService)

        assert resolved1 == resolved2
        assert resolved1 == mock_service

    def test_di_container_resolve_with_dependencies(self):
        """Deve resolver dependências com injeção automática"""
        from src.dependency_injection.di_container import DIContainer
        from src.interfaces.browser_factory_interface import IBrowserFactory
        from src.interfaces.web_scraping_interface import IWebScrapingService

        container = DIContainer()

        mock_browser_factory = Mock(spec=IBrowserFactory)
        mock_web_service = Mock(spec=IWebScrapingService)

        # Registra dependências
        container.register(IBrowserFactory, lambda: mock_browser_factory)
        container.register(IWebScrapingService, lambda: mock_web_service)

        # Resolve com injeção automática
        resolved_service = container.resolve(IWebScrapingService)
        assert resolved_service == mock_web_service


class TestServiceFactory:
    """Testes para ServiceFactory - responsabilidade única de criação de serviços"""

    def test_service_factory_initialization(self):
        """Deve inicializar factory com DI container"""
        from src.dependency_injection.di_container import DIContainer
        from src.dependency_injection.service_factory import ServiceFactory

        container = DIContainer()
        factory = ServiceFactory(container)

        assert factory.container == container
        assert hasattr(factory, "create_web_scraping_service")
        assert hasattr(factory, "create_mcp_request_handler")

    def test_service_factory_create_web_scraping_service(self):
        """Deve criar WebScrapingService com dependências injetadas"""
        from src.dependency_injection.di_container import DIContainer
        from src.dependency_injection.service_factory import ServiceFactory

        container = DIContainer()
        factory = ServiceFactory(container)

        # Mock das dependências
        mock_browser_factory = Mock()
        mock_content_processor = Mock()
        mock_config_service = Mock()

        # Registra dependências no container
        container.register("IBrowserFactory", lambda: mock_browser_factory)
        container.register("IContentProcessingService", lambda: mock_content_processor)
        container.register("IScrapingConfigurationService", lambda: mock_config_service)

        # Cria serviço via factory
        service = factory.create_web_scraping_service()

        # Verifica se as dependências foram injetadas
        assert service is not None
        # Verifica se é uma instância que implementa a interface
        assert hasattr(service, "scrape_url")

    def test_service_factory_create_mcp_request_handler(self):
        """Deve criar MCPRequestHandler com dependências injetadas"""
        from src.dependency_injection.di_container import DIContainer
        from src.dependency_injection.service_factory import ServiceFactory

        container = DIContainer()
        factory = ServiceFactory(container)

        # Mock das dependências MCP
        mock_web_service = Mock()
        mock_validator = Mock()
        mock_formatter = Mock()

        container.register("IWebScrapingService", lambda: mock_web_service)
        container.register("IMCPParameterValidator", lambda: mock_validator)
        container.register("IMCPResponseFormatter", lambda: mock_formatter)

        # Cria handler via factory
        handler = factory.create_mcp_request_handler()

        assert handler is not None
        assert hasattr(handler, "handle_tool_request")
        assert hasattr(handler, "handle_prompt_request")


class TestApplicationBootstrap:
    """Testes para ApplicationBootstrap - responsabilidade única de inicialização da aplicação"""

    def test_application_bootstrap_initialization(self):
        """Deve inicializar bootstrap com configuração de DI"""
        from src.dependency_injection.application_bootstrap import ApplicationBootstrap

        bootstrap = ApplicationBootstrap()
        assert bootstrap is not None
        assert hasattr(bootstrap, "configure_dependencies")
        assert hasattr(bootstrap, "create_server")

    def test_application_bootstrap_configure_dependencies(self):
        """Deve configurar todas as dependências no container"""
        from src.dependency_injection.application_bootstrap import ApplicationBootstrap
        from src.dependency_injection.di_container import DIContainer

        bootstrap = ApplicationBootstrap()
        container = DIContainer()

        # Configura dependências
        bootstrap.configure_dependencies(container)

        # Verifica se todas as interfaces foram registradas
        browser_factory = container.resolve("IBrowserFactory")
        content_service = container.resolve("IContentProcessingService")
        config_service = container.resolve("IScrapingConfigurationService")
        web_service = container.resolve("IWebScrapingService")

        assert browser_factory is not None
        assert content_service is not None
        assert config_service is not None
        assert web_service is not None

    @pytest.mark.asyncio
    async def test_application_bootstrap_create_server(self):
        """Deve criar servidor MCP com dependências injetadas"""
        from src.dependency_injection.application_bootstrap import ApplicationBootstrap

        bootstrap = ApplicationBootstrap()

        # Cria servidor via bootstrap
        server = await bootstrap.create_server()

        assert server is not None
        # Verifica se é uma instância do MCP Server
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")
        assert hasattr(server, "list_prompts")
        assert hasattr(server, "get_prompt")


class TestRefactoredMain:
    """Testes para main.py refatorado - deve usar DI ao invés de dependências hardcoded"""

    @pytest.mark.asyncio
    async def test_main_serve_uses_dependency_injection(self):
        """Deve usar DI container ao invés de instanciar dependências diretamente"""
        from src.main import serve

        # Mock do bootstrap e container
        with patch("src.main.ApplicationBootstrap") as mock_bootstrap_class:
            mock_bootstrap = Mock()
            mock_server = Mock()

            # Configura mocks - create_server deve ser AsyncMock
            mock_bootstrap_class.return_value = mock_bootstrap
            mock_bootstrap.create_server = AsyncMock(return_value=mock_server)
            mock_server.run = AsyncMock()

            # Mock do stdio_server
            with patch("src.main.stdio_server") as mock_stdio:
                mock_stdio.return_value.__aenter__.return_value = (Mock(), Mock())

                # Executa serve
                await serve()

                # Verifica se bootstrap foi usado
                mock_bootstrap_class.assert_called_once()
                mock_bootstrap.create_server.assert_called_once()

    def test_main_no_hardcoded_dependencies(self):
        """Deve verificar que main.py não tem mais dependências hardcoded"""
        # Lê o arquivo main.py refatorado
        with open("src/main.py", "r") as f:
            main_content = f.read()

        # Verifica que não há mais instanciações diretas
        hardcoded_patterns = [
            "FallbackBrowserFactory()",
            "ScrapingConfigurationService()",
            "ContentProcessingService()",
            "WebScrapingService(",
            "MCPParameterValidator()",
            "MCPResponseFormatter()",
            "MCPRequestHandler(",
        ]

        for pattern in hardcoded_patterns:
            assert pattern not in main_content, (
                f"Dependência hardcoded encontrada: {pattern}"
            )

    def test_main_uses_bootstrap_pattern(self):
        """Deve usar padrão Bootstrap para inicialização"""
        with open("src/main.py", "r") as f:
            main_content = f.read()

        # Verifica se usa ApplicationBootstrap
        assert "ApplicationBootstrap" in main_content
        assert (
            "configure_dependencies" in main_content or "create_server" in main_content
        )


class TestBackwardCompatibility:
    """Testes para garantir compatibilidade com funcionalidade existente"""

    @pytest.mark.asyncio
    async def test_server_tools_still_work(self):
        """Deve manter funcionalidade de tools após refatoração DIP"""
        from src.main import serve

        # Mock completo para teste de integração
        with (
            patch("src.main.ApplicationBootstrap") as mock_bootstrap_class,
            patch("src.main.stdio_server") as mock_stdio,
        ):
            mock_bootstrap = Mock()
            mock_server = Mock()

            # Configura mocks - create_server deve ser AsyncMock
            mock_bootstrap_class.return_value = mock_bootstrap
            mock_bootstrap.create_server = AsyncMock(return_value=mock_server)
            mock_server.run = AsyncMock()
            mock_stdio.return_value.__aenter__.return_value = (Mock(), Mock())

            # Simula que server tem os handlers registrados
            mock_server.list_tools = Mock()
            mock_server.call_tool = Mock()
            mock_server.list_prompts = Mock()
            mock_server.get_prompt = Mock()

            # Executa serve
            await serve()

            # Verifica que servidor foi criado e executado
            mock_bootstrap.create_server.assert_called_once()
            mock_server.run.assert_called_once()

    def test_dip_compliance_achieved(self):
        """Deve verificar que DIP foi implementado corretamente"""
        from src.dependency_injection.application_bootstrap import ApplicationBootstrap
        from src.dependency_injection.di_container import DIContainer

        # Verifica que abstrações existem
        bootstrap = ApplicationBootstrap()
        container = DIContainer()

        # Configura dependências
        bootstrap.configure_dependencies(container)

        # Verifica que dependências são resolvidas via abstrações
        assert container.resolve("IBrowserFactory") is not None
        assert container.resolve("IContentProcessingService") is not None
        assert container.resolve("IScrapingConfigurationService") is not None
        assert container.resolve("IWebScrapingService") is not None
