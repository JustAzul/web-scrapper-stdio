"""
ScrapingMetricsCollector - Responsabilidade única: Coleta de métricas de scraping
Parte da refatoração T003 - Quebrar IntelligentFallbackScraper seguindo SRP
"""

import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional


class ScrapingMetricsCollector:
    """Coleta métricas de operações de scraping seguindo Single Responsibility Principle"""

    def __init__(self, enabled: bool = True):
        """
        Inicializa coletor de métricas

        Args:
            enabled: Se coleta de métricas está habilitada
        """
        self.enabled = enabled
        self.last_metrics: Dict[str, Any] = {}
        self._metrics_lock = threading.Lock()

    def start_operation(self) -> float:
        """
        Inicia cronometragem de uma operação

        Returns:
            Timestamp de início da operação
        """
        return time.time()

    def record_scraping_success(
        self,
        start_time: float,
        strategy_used: str,
        attempts: int,
        final_url: Optional[str] = None,
        content_size: Optional[int] = None,
    ) -> None:
        """
        Registra métricas de sucesso de scraping

        Args:
            start_time: Timestamp de início da operação
            strategy_used: Estratégia utilizada (playwright_optimized, requests_fallback, etc.)
            attempts: Número de tentativas realizadas
            final_url: URL final após redirecionamentos
            content_size: Tamanho do conteúdo obtido em bytes
        """
        if not self.enabled:
            return

        total_time = time.time() - start_time

        with self._metrics_lock:
            self.last_metrics = {
                "success": True,
                "total_time": total_time,
                "strategy_used": strategy_used,
                "attempts": attempts,
                "final_url": final_url,
                "content_size": content_size,
                "timestamp": time.time(),
                "error_message": None,
            }

    def record_scraping_failure(
        self,
        start_time: float,
        error_message: str,
        attempts: int,
        strategy_attempted: Optional[str] = None,
    ) -> None:
        """
        Registra métricas de falha de scraping

        Args:
            start_time: Timestamp de início da operação
            error_message: Mensagem de erro
            attempts: Número de tentativas realizadas
            strategy_attempted: Estratégia que foi tentada
        """
        if not self.enabled:
            return

        total_time = time.time() - start_time

        with self._metrics_lock:
            self.last_metrics = {
                "success": False,
                "total_time": total_time,
                "strategy_used": strategy_attempted,
                "attempts": attempts,
                "final_url": None,
                "content_size": None,
                "timestamp": time.time(),
                "error_message": error_message,
            }

    def get_last_metrics(self) -> Dict[str, Any]:
        """
        Retorna cópia das métricas da última operação

        Returns:
            Dicionário com métricas da última operação
        """
        if not self.enabled:
            return {}

        with self._metrics_lock:
            return self.last_metrics.copy()

    def clear_metrics(self) -> None:
        """Limpa métricas armazenadas"""
        with self._metrics_lock:
            self.last_metrics.clear()

    def is_enabled(self) -> bool:
        """
        Verifica se coleta de métricas está habilitada

        Returns:
            True se habilitada, False caso contrário
        """
        return self.enabled

    def enable(self) -> None:
        """Habilita coleta de métricas"""
        self.enabled = True

    def disable(self) -> None:
        """Desabilita coleta de métricas"""
        self.enabled = False
        self.clear_metrics()

    @contextmanager
    def operation_context(self, operation_name: str):
        """
        Context manager para medição automática de operações

        Args:
            operation_name: Nome da operação sendo medida

        Yields:
            Context object com métodos success() e failure()
        """
        start_time = self.start_operation()

        class OperationContext:
            def __init__(self, metrics_collector, start_time, operation_name):
                self.metrics = metrics_collector
                self.start_time = start_time
                self.operation_name = operation_name
                self.completed = False

            def success(self, strategy_used: str, attempts: int = 1, **kwargs):
                if not self.completed:
                    self.metrics.record_scraping_success(
                        self.start_time, strategy_used, attempts, **kwargs
                    )
                    self.completed = True

            def failure(self, error_message: str, attempts: int = 1, **kwargs):
                if not self.completed:
                    self.metrics.record_scraping_failure(
                        self.start_time, error_message, attempts, **kwargs
                    )
                    self.completed = True

        context = OperationContext(self, start_time, operation_name)

        try:
            yield context
        except Exception as e:
            if not context.completed:
                context.failure(str(e))
            raise

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo de performance da última operação

        Returns:
            Resumo de performance
        """
        metrics = self.get_last_metrics()
        if not metrics:
            return {}

        return {
            "operation_successful": metrics.get("success", False),
            "total_time_seconds": metrics.get("total_time", 0),
            "strategy_used": metrics.get("strategy_used"),
            "attempts_made": metrics.get("attempts", 0),
            "has_error": metrics.get("error_message") is not None,
        }

    def __repr__(self) -> str:
        """Representação string do coletor de métricas"""
        return f"ScrapingMetricsCollector(enabled={self.enabled})"
