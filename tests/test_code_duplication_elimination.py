"""
TDD Tests for T005: Eliminar Duplicação extract_clean_html
Objetivo: Centralizar lógica duplicada em uma implementação parametrizada

FASE RED: Testes que falham primeiro - definindo comportamento esperado após refatoração
"""

from unittest.mock import Mock, patch


class TestCentralizedHTMLExtractor:
    """Testes para extrator HTML centralizado - responsabilidade única"""

    def test_centralized_html_extractor_exists(self):
        """Deve existir uma classe CentralizedHTMLExtractor"""
        from src.scraper.infrastructure.web_scraping.centralized_html_extractor import (
            CentralizedHTMLExtractor,
        )

        # Deve poder ser instanciada
        extractor = CentralizedHTMLExtractor()
        assert extractor is not None
        assert hasattr(extractor, "extract_clean_html")

    def test_centralized_extractor_single_responsibility(self):
        """Deve ter responsabilidade única de extração HTML"""
        from src.scraper.infrastructure.web_scraping.centralized_html_extractor import (
            CentralizedHTMLExtractor,
        )

        extractor = CentralizedHTMLExtractor()

        # Deve ter apenas métodos relacionados à extração
        [method for method in dir(extractor) if not method.startswith("_")]
        expected_methods = ["extract_clean_html", "configure"]

        for method in expected_methods:
            assert hasattr(extractor, method)


class TestExtractionConfig:
    """Testes para configuração de extração - responsabilidade única de configuração"""

    def test_extraction_config_initialization(self):
        """Deve criar configuração com valores padrão"""
        from src.scraper.domain.value_objects.extraction_config import ExtractionConfig

        config = ExtractionConfig()

        # Deve ter valores padrão sensatos
        assert config.elements_to_remove is not None
        assert isinstance(config.elements_to_remove, list)
        assert config.use_chunked_processing is not None
        assert config.memory_limit_mb > 0


class TestBackwardCompatibilityLayer:
    """Testes para camada de compatibilidade - preservar interfaces existentes"""

    def test_original_extract_clean_html_interface_preserved(self):
        """Deve manter interface original de extract_clean_html"""
        from src.scraper import extract_clean_html

        # Interface original deve funcionar
        result = extract_clean_html(
            html_content="<html><body><h1>Test</h1></body></html>",
            elements_to_remove=["script"],
            url="https://example.com",
        )

        # Deve retornar formato original
        assert isinstance(result, tuple)
        assert len(result) == 5
        title, clean_html, text_content, error, soup = result
        assert error is None

    def test_all_interfaces_use_central_implementation(self):
        """Todas as interfaces devem usar implementação central"""
        from src.scraper import extract_clean_html

        html = "<html><body><h1>Test</h1></body></html>"
        elements = ["script"]
        url = "https://example.com"

        # Deve usar implementação central (mock do singleton getter)
        with patch(
            "src.scraper.infrastructure.web_scraping.centralized_html_extractor.get_centralized_extractor"
        ) as mock_getter:
            mock_instance = Mock()
            mock_getter.return_value = mock_instance
            mock_instance.extract_clean_html.return_value = (
                "Title",
                "<h1>Test</h1>",
                "Test",
                None,
                Mock(),
            )

            # Chamar interface
            extract_clean_html(html, elements, url)

            # Deve ter usado a implementação central
            assert mock_getter.called
            assert mock_instance.extract_clean_html.called
