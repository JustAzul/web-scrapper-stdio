"""
FallbackOrchestrator - Orquestração das responsabilidades de fallback scraping
Parte da refatoração T003 - Quebrar IntelligentFallbackScraper seguindo SRP
"""

import time
from typing import Any, Dict, Optional

import httpx
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from src.logger import Logger

from ...infrastructure.circuit_breaker_pattern import CircuitBreakerPattern
from ...infrastructure.monitoring.scraping_metrics_collector import (
    ScrapingMetricsCollector,
)
from ...infrastructure.retry_strategy_pattern import RetryStrategyPattern
from ...infrastructure.web_scraping.intelligent_fallback_scraper import (
    FallbackConfig,
    FallbackStrategy,
    ScrapingResult,
)
from ...infrastructure.web_scraping.playwright_scraping_strategy import (
    PlaywrightScrapingStrategy,
)
from ...infrastructure.web_scraping.requests_scraping_strategy import (
    RequestsScrapingStrategy,
)
from .scraping_request import ScrapingRequest

logger = Logger(__name__)


class FallbackOrchestrator:
    """Orquestra estratégias de fallback seguindo SRP e Dependency Injection"""

    def __init__(
        self,
        config: Optional[FallbackConfig] = None,
        circuit_breaker: Optional[CircuitBreakerPattern] = None,
        retry_strategy: Optional[RetryStrategyPattern] = None,
        metrics_collector: Optional[ScrapingMetricsCollector] = None,
        playwright_strategy: Optional[PlaywrightScrapingStrategy] = None,
        requests_strategy: Optional[RequestsScrapingStrategy] = None,
    ):
        """
        Inicializa orquestrador com injeção de dependências

        Args:
            config: Configuração de fallback
            circuit_breaker: Padrão circuit breaker (injetado)
            retry_strategy: Estratégia de retry (injetado)
            metrics_collector: Coletor de métricas (injetado)
            playwright_strategy: Estratégia Playwright (injetado)
            requests_strategy: Estratégia requests (injetado)
        """
        self.config = config or FallbackConfig()

        # Dependency Injection - permite mocking para testes
        self.circuit_breaker = circuit_breaker or CircuitBreakerPattern(
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery_seconds,
        )

        self.retry_strategy = retry_strategy or RetryStrategyPattern(
            max_retries=self.config.max_retries, initial_delay=1.0
        )

        self.metrics_collector = metrics_collector or ScrapingMetricsCollector(
            enabled=True
        )

        self.playwright_strategy = playwright_strategy or PlaywrightScrapingStrategy(
            self.config
        )

        self.requests_strategy = requests_strategy or RequestsScrapingStrategy(
            self.config
        )

    async def scrape_url(self, request: ScrapingRequest) -> ScrapingResult:
        """
        Executa scraping com fallback inteligente

        Args:
            request: Objeto com todos os parâmetros da requisição

        Returns:
            Resultado do scraping com metadados
        """
        start_time = self.metrics_collector.start_operation()
        attempts = 0

        # Monta headers a partir do request
        custom_headers = {}
        if request.user_agent:
            custom_headers["User-Agent"] = request.user_agent

        # Verifica circuit breaker
        if self.circuit_breaker.is_open:
            error_msg = "Circuit breaker is open. Service is temporarily unavailable."

            self.metrics_collector.record_scraping_failure(
                start_time=start_time, error_message=error_msg, attempts=attempts
            )

            return ScrapingResult(
                success=False,
                content=None,
                strategy_used=FallbackStrategy.ALL_FAILED,
                attempts=attempts,
                error=error_msg,
                performance_metrics={"total_time": time.time() - start_time},
            )

        # Estratégia 1: Playwright
        try:
            attempts += 1
            content = await self.playwright_strategy.scrape_url(request, custom_headers)
            self.circuit_breaker.record_success()

            self.metrics_collector.record_scraping_success(
                start_time=start_time,
                strategy_used="playwright_optimized",
                attempts=attempts,
                final_url=request.url,
                content_size=len(content) if content else 0,
            )

            return ScrapingResult(
                success=True,
                content=content,
                strategy_used=FallbackStrategy.PLAYWRIGHT_OPTIMIZED,
                attempts=attempts,
                performance_metrics={"total_time": time.time() - start_time},
                final_url=request.url,
            )

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            logger.warning(f"Playwright strategy failed for {request.url}: {e}")
            self.circuit_breaker.record_failure()
        except ImportError as e:
            logger.error(f"Playwright not available: {e}")
            self.circuit_breaker.record_failure()
        except Exception as e:
            logger.error(
                f"Unexpected error in Playwright strategy for {request.url}: {e}"
            )
            self.circuit_breaker.record_failure()

        # Estratégia 2: Fallback para requests
        try:
            attempts += 1
            content = await self.requests_strategy.scrape_url(
                request.url, custom_headers
            )
            self.circuit_breaker.record_success()

            self.metrics_collector.record_scraping_success(
                start_time=start_time,
                strategy_used="requests_fallback",
                attempts=attempts,
                final_url=request.url,
                content_size=len(content) if content else 0,
            )

            return ScrapingResult(
                success=True,
                content=content,
                strategy_used=FallbackStrategy.REQUESTS_FALLBACK,
                attempts=attempts,
                performance_metrics={"total_time": time.time() - start_time},
                final_url=request.url,
            )
        except httpx.HTTPStatusError as e:
            self.circuit_breaker.record_failure()
            error_msg = f"HTTP error {e.response.status_code} for url {e.request.url}"
            logger.warning(error_msg)
            return ScrapingResult(
                success=False,
                content=None,
                strategy_used=FallbackStrategy.ALL_FAILED,
                attempts=attempts,
                error=error_msg,
                performance_metrics={"total_time": time.time() - start_time},
            )

        except Exception as e:
            self.circuit_breaker.record_failure()
            error_msg = str(e)

            self.metrics_collector.record_scraping_failure(
                start_time=start_time, error_message=error_msg, attempts=attempts
            )

            return ScrapingResult(
                success=False,
                content=None,
                strategy_used=FallbackStrategy.ALL_FAILED,
                attempts=attempts,
                error=error_msg,
                performance_metrics={"total_time": time.time() - start_time},
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas da última operação"""
        return self.metrics_collector.get_last_metrics()

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Retorna status do circuit breaker"""
        return {
            "state": self.circuit_breaker.get_state(),
            "failure_count": self.circuit_breaker.get_failure_count(),
            "is_open": self.circuit_breaker.is_open,
        }
