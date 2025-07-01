"""
RefactoredChunkedHTMLProcessor - Orquestração das responsabilidades refatoradas
Parte da refatoração T002 - Quebrar ChunkedHTMLProcessor seguindo SRP
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from src.core.constants import BYTES_PER_MB, DEFAULT_CHUNK_SIZE_THRESHOLD
from src.logger import Logger

from .chunking_strategy import ChunkingStrategy
from .content_processor import ContentProcessor
from .fallback_handler import FallbackHandler
from .memory_monitor import MemoryMonitor
from .processing_metrics import ProcessingMetrics


class RefactoredChunkedHTMLProcessor:
    def __init__(
        self,
        parser: str = "lxml",
        extra_noise_cleanup: bool = False,
        memory_limit_mb: int = 150,
        enable_chunking: bool = True,
        chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
        fallback_enabled: bool = True,
        memory_monitor: Optional[MemoryMonitor] = None,
        metrics: Optional[ProcessingMetrics] = None,
        chunking_strategy: Optional[ChunkingStrategy] = None,
        content_processor: Optional[ContentProcessor] = None,
        fallback_handler: Optional[FallbackHandler] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initializes the processor with dependency injection.
        Args:
            parser: HTML parser to use.
            extra_noise_cleanup: Whether to perform extra noise cleanup.
            memory_limit_mb: Memory limit in MB.
            enable_chunking: Whether to enable chunking.
            chunk_size_threshold: Threshold to use chunking.
            fallback_enabled: Whether to enable fallback handler.
            memory_monitor: Injected memory monitor.
            metrics: Injected metrics collector.
            chunking_strategy: Injected chunking strategy.
            content_processor: Injected content processor.
            fallback_handler: Injected fallback handler.
            logger: Injected logger.
        """
        # Configurações básicas
        self.parser = parser
        self.extra_noise_cleanup = extra_noise_cleanup

        # Dependency Injection - permite mocking para testes
        self.memory_monitor = memory_monitor or MemoryMonitor(
            memory_limit_mb=memory_limit_mb, enabled=True
        )
        self.metrics = metrics or ProcessingMetrics(enabled=True)
        self.chunking_strategy = chunking_strategy or ChunkingStrategy(
            chunk_size_threshold=chunk_size_threshold, enable_chunking=enable_chunking
        )
        self.content_processor = content_processor or ContentProcessor(
            parser=parser, extra_noise_cleanup=extra_noise_cleanup
        )
        self.fallback_handler = fallback_handler or FallbackHandler(
            enabled=fallback_enabled
        )

        # Para compatibilidade com interface original
        self.enable_chunking = enable_chunking
        self.fallback_enabled = fallback_enabled

        self.logger = logger or Logger(__name__)

    def extract_content(
        self, html_content: str, elements_to_remove: List[str], url: str
    ) -> Tuple[
        Optional[str],
        Optional[str],
        Optional[str],
        Optional[BeautifulSoup],
    ]:
        """
        Extrai conteúdo mantendo interface original do ChunkedHTMLProcessor

        Args:
            html_content: HTML para processar
            elements_to_remove: Elementos para remover
            url: URL sendo processada

        Returns:
            Tupla de (title, clean_html, text_content, error, soup)
        """
        start_time = self.metrics.start_processing()
        content_size_mb = len(html_content.encode("utf-8")) / BYTES_PER_MB

        try:
            # Handle empty HTML
            if not html_content or not html_content.strip():
                return "", "", "", None, None

            # Parse HTML
            soup = BeautifulSoup(html_content, self.parser)

            # Determina se deve usar chunking
            use_chunked = self.chunking_strategy.should_use_chunked_processing(
                html_content
            )

            if use_chunked:
                self.logger.debug(
                    f"Using chunked processing for {url} (size: {content_size_mb:.2f}MB)"
                )

                # Usa fallback handler para tentar chunked primeiro, depois original
                def primary_operation():
                    return self._extract_content_chunked(soup, elements_to_remove)

                def fallback_operation():
                    return self._extract_content_original(soup, elements_to_remove)

                title, clean_html, text_content, error = (
                    self.fallback_handler.execute_with_fallback(
                        primary_operation, fallback_operation
                    )
                )
                use_chunked = error is None  # Se erro, significa que usou fallback

            else:
                self.logger.debug(
                    f"Using original processing for {url} (size: {content_size_mb:.2f}MB)"
                )
                title, clean_html, text_content, error = self._extract_content_original(
                    soup, elements_to_remove
                )

            # Registra métricas de sucesso
            if error is None:
                self.metrics.record_processing_success(
                    start_time=start_time,
                    content_size_mb=content_size_mb,
                    used_chunked_processing=use_chunked,
                    memory_peak_mb=self.memory_monitor.get_memory_usage(),
                    chunks_processed=getattr(self, "_chunks_processed", 0),
                )

            self.logger.debug(
                f"Content extraction completed for {url} in {time.time() - start_time:.2f}s"
            )

            return title or "", clean_html or "", text_content or "", error, soup

        except Exception as e:
            error_msg = f"Content extraction failed: {str(e)}"
            self.logger.error(f"Error processing {url}: {error_msg}")

            # Registra métricas de erro
            self.metrics.record_processing_error(
                start_time=start_time,
                content_size_mb=content_size_mb,
                error_message=error_msg,
            )

            return "", "", "", error_msg, None

    def _extract_content_chunked(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extrai conteúdo usando processamento chunked"""
        try:
            # Monitora memória durante processamento
            with self.memory_monitor:
                return self.content_processor.extract_content_chunked(
                    soup, elements_to_remove, self.chunking_strategy
                )
        except Exception as e:
            raise Exception(f"Chunked processing failed: {str(e)}")

    def _extract_content_original(
        self, soup: BeautifulSoup, elements_to_remove: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extrai conteúdo usando método original"""
        return self.content_processor.extract_content_original(soup, elements_to_remove)

    def get_last_processing_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do último processamento"""
        return self.metrics.get_last_metrics()

    async def extract_content_async(
        self, html_content: str, elements_to_remove: List[str], url: str
    ):
        """Wrapper assíncrono para compatibilidade"""
        return self.extract_content(html_content, elements_to_remove, url)

    # Propriedades para compatibilidade com interface original
    @property
    def noise_selectors(self):
        """Compatibilidade com interface original"""
        return self.content_processor.noise_selectors

    def _should_use_chunked_processing(self, html_content: str) -> bool:
        """Compatibilidade com interface original"""
        return self.chunking_strategy.should_use_chunked_processing(html_content)


# Funções de compatibilidade com interface original
def extract_clean_html_optimized(
    html_content: str, elements_to_remove: List[str], url: str, **processor_kwargs
) -> Tuple[str, str, str, Optional[str], Optional[BeautifulSoup]]:
    """
    Função de compatibilidade que usa o processor refatorado
    """
    processor = RefactoredChunkedHTMLProcessor(**processor_kwargs)
    return processor.extract_content(html_content, elements_to_remove, url)


def create_chunked_processor(
    enable_chunking: bool = True,
    chunk_size_threshold: int = DEFAULT_CHUNK_SIZE_THRESHOLD,
    memory_limit_mb: int = 150,
) -> RefactoredChunkedHTMLProcessor:
    """
    Factory function de compatibilidade
    """
    return RefactoredChunkedHTMLProcessor(
        enable_chunking=enable_chunking,
        chunk_size_threshold=chunk_size_threshold,
        memory_limit_mb=memory_limit_mb,
    )
