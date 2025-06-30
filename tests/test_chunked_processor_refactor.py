"""
TDD Tests for T002: Refatorar ChunkedHTMLProcessor
Objetivo: Quebrar God Class (511 linhas) em classes menores seguindo SRP

FASE GREEN: Implementar classes que ainda não existem
"""

from bs4 import BeautifulSoup


class TestChunkingStrategy:
    """Testes para ChunkingStrategy - responsabilidade única de estratégia de chunking"""

    def test_should_use_chunked_processing_small_content(self):
        """Deve retornar False para conteúdo pequeno"""
        from src.scraper.infrastructure.external.chunking_strategy import (
            ChunkingStrategy,
        )

        strategy = ChunkingStrategy(chunk_size_threshold=100000, enable_chunking=True)
        small_html = "<html><body>Small content</body></html>"

        assert strategy.should_use_chunked_processing(small_html) is False

    def test_should_use_chunked_processing_large_content(self):
        """Deve retornar True para conteúdo grande"""
        from src.scraper.infrastructure.external.chunking_strategy import (
            ChunkingStrategy,
        )

        strategy = ChunkingStrategy(chunk_size_threshold=100, enable_chunking=True)
        large_html = "x" * 200

        assert strategy.should_use_chunked_processing(large_html) is True

    def test_chunking_disabled(self):
        """Deve retornar False quando chunking está desabilitado"""
        from src.scraper.infrastructure.external.chunking_strategy import (
            ChunkingStrategy,
        )

        strategy = ChunkingStrategy(chunk_size_threshold=100, enable_chunking=False)
        large_html = "x" * 200

        assert strategy.should_use_chunked_processing(large_html) is False


class TestContentProcessor:
    """Testes para ContentProcessor - responsabilidade única de processamento de conteúdo"""

    def test_extract_title_with_title(self):
        """Deve extrair título quando presente"""
        from src.scraper.infrastructure.external.content_processor import (
            ContentProcessor,
        )

        processor = ContentProcessor()
        html = "<html><head><title>Test Title</title></head><body>Content</body></html>"
        soup = BeautifulSoup(html, "html.parser")

        title = processor.extract_title(soup)
        assert title == "Test Title"

    def test_extract_title_without_title(self):
        """Deve retornar string vazia quando título ausente"""
        from src.scraper.infrastructure.external.content_processor import (
            ContentProcessor,
        )

        processor = ContentProcessor()
        html = "<html><body>Content</body></html>"
        soup = BeautifulSoup(html, "html.parser")

        title = processor.extract_title(soup)
        assert title == ""


class TestFallbackHandler:
    """Testes para FallbackHandler - responsabilidade única de fallback"""

    def test_execute_with_fallback_success(self):
        """Deve retornar resultado da operação principal quando bem-sucedida"""
        from src.scraper.infrastructure.external.fallback_handler import FallbackHandler

        handler = FallbackHandler(enabled=True)

        def successful_operation():
            return "success"

        def fallback_operation():
            return "fallback"

        result = handler.execute_with_fallback(successful_operation, fallback_operation)
        assert result == "success"

    def test_execute_with_fallback_failure(self):
        """Deve usar fallback quando operação principal falha"""
        from src.scraper.infrastructure.external.fallback_handler import FallbackHandler

        handler = FallbackHandler(enabled=True)

        def failing_operation():
            raise Exception("Test error")

        def fallback_operation():
            return "fallback"

        result = handler.execute_with_fallback(failing_operation, fallback_operation)
        assert result == "fallback"


class TestMemoryMonitor:
    """Testes para MemoryMonitor"""

    def test_memory_monitor_initialization(self):
        """Deve inicializar monitor"""
        # Este teste deve falhar - classe não existe ainda
        from src.scraper.infrastructure.monitoring.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor(memory_limit_mb=150)
        assert monitor.memory_limit_mb == 150


class TestRefactoredChunkedHTMLProcessor:
    """Testes para RefactoredChunkedHTMLProcessor - orquestração das responsabilidades"""

    def test_processor_initialization_with_dependency_injection(self):
        """Deve inicializar com injeção de dependências"""
        from src.scraper.infrastructure.external.refactored_chunked_processor import (
            RefactoredChunkedHTMLProcessor,
        )
        from src.scraper.infrastructure.monitoring.memory_monitor import MemoryMonitor
        from src.scraper.infrastructure.monitoring.processing_metrics import (
            ProcessingMetrics,
        )

        memory_monitor = MemoryMonitor(memory_limit_mb=200)
        metrics = ProcessingMetrics(enabled=True)

        processor = RefactoredChunkedHTMLProcessor(
            memory_monitor=memory_monitor, metrics=metrics
        )

        assert processor.memory_monitor == memory_monitor
        assert processor.metrics == metrics
        assert processor.chunking_strategy is not None
        assert processor.content_processor is not None
        assert processor.fallback_handler is not None

    def test_extract_content_small_html(self):
        """Deve processar HTML pequeno sem chunking"""
        from src.scraper.infrastructure.external.refactored_chunked_processor import (
            RefactoredChunkedHTMLProcessor,
        )

        processor = RefactoredChunkedHTMLProcessor()

        html = "<html><head><title>Test</title></head><body><p>Small content</p></body></html>"
        elements_to_remove = ["script", "style"]
        url = "https://example.com"

        title, clean_html, text_content, error, soup = processor.extract_content(
            html, elements_to_remove, url
        )

        assert title == "Test"
        assert "Small content" in text_content
        assert error is None
        assert soup is not None

    def test_get_processing_metrics(self):
        """Deve retornar métricas do último processamento"""
        from src.scraper.infrastructure.external.refactored_chunked_processor import (
            RefactoredChunkedHTMLProcessor,
        )

        processor = RefactoredChunkedHTMLProcessor()

        # Processa algum conteúdo primeiro
        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        processor.extract_content(html, [], "https://example.com")

        metrics = processor.get_last_processing_metrics()

        assert isinstance(metrics, dict)
        assert "processing_time" in metrics
        assert "content_size_mb" in metrics


class TestBackwardCompatibility:
    """Testes para garantir compatibilidade com interface original"""

    def test_extract_clean_html_optimized_interface_preserved(self):
        """Deve manter interface da função original mas usar classes refatoradas"""
        from src.scraper.infrastructure.external.refactored_chunked_processor import (
            extract_clean_html_optimized,
        )

        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        elements_to_remove = ["script", "style"]
        url = "https://example.com"

        result = extract_clean_html_optimized(html, elements_to_remove, url)

        assert len(result) == 5  # title, clean_html, text_content, error, soup
        assert result[0] == "Test"  # title
        assert "Content" in result[2]  # text_content
        assert result[3] is None  # no error

    def test_create_chunked_processor_factory(self):
        """Deve manter função factory mas retornar processor refatorado"""
        from src.scraper.infrastructure.external.refactored_chunked_processor import (
            create_chunked_processor,
        )

        processor = create_chunked_processor(
            enable_chunking=True, chunk_size_threshold=50000, memory_limit_mb=200
        )

        assert processor is not None
        assert hasattr(processor, "extract_content")
        assert hasattr(processor, "get_last_processing_metrics")

    def test_single_responsibility_compliance(self):
        """Deve verificar que cada classe tem responsabilidade única"""
        from src.scraper.infrastructure.external.chunking_strategy import (
            ChunkingStrategy,
        )
        from src.scraper.infrastructure.external.content_processor import (
            ContentProcessor,
        )
        from src.scraper.infrastructure.external.fallback_handler import FallbackHandler
        from src.scraper.infrastructure.monitoring.memory_monitor import MemoryMonitor
        from src.scraper.infrastructure.monitoring.processing_metrics import (
            ProcessingMetrics,
        )

        # MemoryMonitor - apenas monitoramento de memória
        monitor = MemoryMonitor(memory_limit_mb=150)
        assert hasattr(monitor, "check_memory_limit")
        assert hasattr(monitor, "get_memory_usage")
        assert not hasattr(
            monitor, "extract_content"
        )  # Não deve ter outras responsabilidades

        # ProcessingMetrics - apenas coleta de métricas
        metrics = ProcessingMetrics(enabled=True)
        assert hasattr(metrics, "record_processing_success")
        assert hasattr(metrics, "record_processing_error")
        assert not hasattr(
            metrics, "check_memory_limit"
        )  # Não deve ter outras responsabilidades

        # ChunkingStrategy - apenas estratégia de chunking
        strategy = ChunkingStrategy()
        assert hasattr(strategy, "should_use_chunked_processing")
        assert hasattr(strategy, "identify_content_areas")
        assert not hasattr(
            strategy, "record_processing_success"
        )  # Não deve ter outras responsabilidades

        # ContentProcessor - apenas processamento de conteúdo
        processor = ContentProcessor()
        assert hasattr(processor, "extract_title")
        assert hasattr(processor, "extract_content_original")
        assert not hasattr(
            processor, "check_memory_limit"
        )  # Não deve ter outras responsabilidades

        # FallbackHandler - apenas gerenciamento de fallback
        handler = FallbackHandler()
        assert hasattr(handler, "execute_with_fallback")
        assert hasattr(handler, "is_enabled")
        assert not hasattr(
            handler, "extract_title"
        )  # Não deve ter outras responsabilidades
