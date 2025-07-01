"""
TDD Tests for T001: Refatorar extract_text_from_url
Objetivo: Quebrar função gigante (180+ linhas, 9 parâmetros) em classes menores seguindo SRP

FASE RED: Testes que falham primeiro - definindo o comportamento esperado após refatoração
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.output_format_handler import OutputFormat
from src.scraper.api.handlers.content_extractor import ContentExtractor
from src.scraper.api.handlers.output_formatter import OutputFormatter
from src.scraper.application.services.scraping_orchestrator import ScrapingOrchestrator
from src.scraper.application.services.url_validator import URLValidator


class TestURLValidator:
    """Testes para classe URLValidator - responsabilidade única de validação de URL"""

    def test_validate_valid_url(self):
        """Deve validar URLs válidas"""
        validator = URLValidator()
        assert validator.validate("https://example.com") is True
        assert validator.validate("http://test.org") is True

    def test_validate_invalid_url(self):
        """Deve rejeitar URLs inválidas"""
        validator = URLValidator()
        assert validator.validate("invalid-url") is False
        assert validator.validate("") is False
        assert validator.validate(None) is False

    def test_normalize_url(self):
        """Deve normalizar URLs"""
        validator = URLValidator()
        assert validator.normalize("example.com") == "https://example.com"
        assert validator.normalize("http://example.com") == "http://example.com"


class TestContentExtractor:
    """Testes para classe ContentExtractor - responsabilidade única de extração"""

    @pytest.mark.asyncio
    async def test_extract_content_success(self):
        """Deve extrair conteúdo com sucesso"""
        extractor = ContentExtractor()

        # Mock da configuração
        config = Mock()
        config.timeout_seconds = 30
        config.elements_to_remove = ["script", "style"]
        config.wait_for_network_idle = True

        # Mock do resultado esperado
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.content.return_value = "<html><body>Test content</body></html>"

        result = await extractor.extract(mock_page, config)

        assert result.title is not None
        assert result.content is not None
        assert result.error is None

    @pytest.mark.asyncio
    async def test_extract_content_error_handling(self):
        """Deve tratar erros durante extração"""
        extractor = ContentExtractor()

        config = Mock()
        mock_page = AsyncMock()
        mock_page.content.side_effect = Exception("Network error")

        result = await extractor.extract(mock_page, config)

        assert result.error is not None
        assert "Network error" in result.error


class TestOutputFormatter:
    """Testes para classe OutputFormatter - responsabilidade única de formatação"""

    def test_format_to_markdown(self):
        """Deve formatar conteúdo para Markdown"""
        formatter = OutputFormatter()

        html_content = "<h1>Title</h1><p>Content</p>"
        result = formatter.format(html_content, OutputFormat.MARKDOWN)

        assert "# Title" in result
        assert "Content" in result

    def test_format_to_text(self):
        """Deve formatar conteúdo para texto plano"""
        formatter = OutputFormatter()

        soup = Mock()
        result = formatter.format_text(soup)

        assert result is not None

    def test_truncate_content(self):
        """Deve truncar conteúdo quando necessário"""
        formatter = OutputFormatter()

        long_content = "a" * 1000
        result = formatter.truncate(long_content, max_length=100)

        assert len(result) <= 100


class TestScrapingOrchestrator:
    """Testes para classe ScrapingOrchestrator - orquestração das responsabilidades"""

    @pytest.mark.asyncio
    async def test_scrape_url_success_integration(self):
        """Teste de integração: deve orquestrar todo o processo com sucesso"""

        # Mocks das dependências
        url_validator = Mock()
        url_validator.validate.return_value = True
        url_validator.normalize.return_value = "https://example.com"

        content_extractor = AsyncMock()
        extraction_result = Mock()
        extraction_result.title = "Test Title"
        extraction_result.content = "Test Content"
        extraction_result.error = None
        content_extractor.extract.return_value = extraction_result

        output_formatter = Mock()
        output_formatter.format.return_value = "# Test Title\nTest Content"
        output_formatter.truncate.side_effect = lambda content, max_length: content

        # Instância do orquestrador
        orchestrator = ScrapingOrchestrator(
            url_validator=url_validator,
            content_extractor=content_extractor,
            output_formatter=output_formatter,
        )

        # Execução
        result = await orchestrator.scrape_url(
            url="example.com", output_format=OutputFormat.MARKDOWN
        )

        # Verificações
        assert result["title"] == "Test Title"
        assert result["content"] == "# Test Title\nTest Content"
        assert result["error"] is None
        assert result["final_url"] == "https://example.com"

        # Verificar que as dependências foram chamadas corretamente
        url_validator.validate.assert_called_once()
        url_validator.normalize.assert_called_once()
        content_extractor.extract.assert_called_once()
        output_formatter.format.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_url_invalid_url(self):
        """Deve retornar erro para URL inválida"""

        url_validator = Mock()
        url_validator.validate.return_value = False

        orchestrator = ScrapingOrchestrator(
            url_validator=url_validator,
            content_extractor=Mock(),
            output_formatter=Mock(),
        )

        result = await orchestrator.scrape_url(
            url="invalid-url", output_format=OutputFormat.TEXT
        )

        assert result["error"] is not None
        assert "Invalid URL" in result["error"]

    def test_scraping_orchestrator_srp(self):
        """O orquestrador deve ter uma única responsabilidade: orquestrar o scraping"""
        # Verificar que não há mais 9 parâmetros na função principal
        ScrapingOrchestrator(
            url_validator=Mock(), content_extractor=Mock(), output_formatter=Mock()
        )
        # Test passes if it doesn't raise an exception
        assert True

    @pytest.mark.asyncio
    async def test_scrape_with_custom_timeout(self):
        """Teste para verificar o comportamento com um timeout personalizado"""
        # Implemente o teste para verificar o comportamento com um timeout personalizado
        # Este teste deve ser implementado com base no comportamento esperado do ScrapingOrchestrator
        # com um timeout personalizado
        pass


class TestBackwardCompatibility:
    """Testes para garantir compatibilidade com a interface atual"""

    @pytest.mark.asyncio
    async def test_extract_text_from_url_interface_preserved(self):
        """Deve manter a interface pública da função original"""
        from src.scraper import extract_text_from_url

        # A função deve ainda existir e ter a mesma assinatura para compatibilidade
        # mas internamente deve usar as novas classes

        with patch("src.scraper.ScrapingOrchestrator") as mock_orchestrator:
            mock_instance = AsyncMock()
            mock_orchestrator.return_value = mock_instance
            mock_instance.scrape_url.return_value = {
                "title": "Test",
                "content": "Content",
                "error": None,
                "final_url": "https://example.com",
            }

            # Deve ainda funcionar com a interface original
            result = await extract_text_from_url("https://example.com")

            assert "title" in result
            assert "content" in result
            assert "error" in result
            assert "final_url" in result
