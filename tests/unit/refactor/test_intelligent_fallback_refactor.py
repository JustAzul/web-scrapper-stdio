"""
TDD Tests for T003: Refatorar IntelligentFallbackScraper
Objetivo: Quebrar God Class (375 linhas) em classes menores seguindo SRP

FASE RED: Testes que falham primeiro - definindo comportamento esperado após refatoração
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import ScrapingRequest for updated test methods
from src.scraper.application.services.scraping_request import ScrapingRequest


class TestCircuitBreakerPattern:
    """Testes para CircuitBreakerPattern - responsabilidade única de circuit breaker"""

    def test_circuit_breaker_initialization(self):
        """Deve inicializar circuit breaker com configurações"""
        from src.scraper.infrastructure.circuit_breaker_pattern import (
            CircuitBreakerPattern,
        )

        breaker = CircuitBreakerPattern(failure_threshold=5, recovery_timeout=60)
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    def test_circuit_breaker_records_failure(self):
        """Deve registrar falhas e abrir quando atingir threshold"""
        from src.scraper.infrastructure.circuit_breaker_pattern import (
            CircuitBreakerPattern,
        )

        breaker = CircuitBreakerPattern(failure_threshold=3, recovery_timeout=60)

        # Registra falhas até o threshold
        breaker.record_failure()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 1

        breaker.record_failure()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 2

        breaker.record_failure()  # Deve abrir o circuit breaker
        assert breaker.state == "OPEN"
        assert breaker.is_open is True

    def test_circuit_breaker_records_success(self):
        """Deve registrar sucesso e resetar contador"""
        from src.scraper.infrastructure.circuit_breaker_pattern import (
            CircuitBreakerPattern,
        )

        breaker = CircuitBreakerPattern(failure_threshold=3, recovery_timeout=60)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2

        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == "CLOSED"

    def test_circuit_breaker_half_open_recovery(self):
        """Deve transicionar para HALF_OPEN após timeout de recovery"""
        from src.scraper.infrastructure.circuit_breaker_pattern import (
            CircuitBreakerPattern,
        )

        # Mock time to control it precisely
        with patch("time.time") as mock_time:
            # 1. Initialize breaker and set initial time
            mock_time.return_value = 100.0
            breaker = CircuitBreakerPattern(failure_threshold=2, recovery_timeout=5)

            # 2. Force the circuit to open
            breaker.record_failure()
            breaker.record_failure()
            assert breaker.state == "OPEN"
            assert breaker.last_failure_time == 100.0

            # 3. Check that it's open before recovery timeout
            mock_time.return_value = 104.0  # 4 seconds later
            assert breaker.is_open is True
            assert breaker.state == "OPEN"  # State should not change yet

            # 4. Move time past the recovery timeout
            mock_time.return_value = 105.1  # 5.1 seconds later
            assert breaker.is_open is False  # Should now be HALF_OPEN

            # 5. Verify the state transitioned
            assert breaker.state == "HALF_OPEN"


class TestRetryStrategyPattern:
    """Testes para RetryStrategyPattern - responsabilidade única de retry com backoff"""

    @pytest.mark.asyncio
    async def test_retry_strategy_success_first_attempt(self):
        """Deve executar com sucesso na primeira tentativa"""
        from src.scraper.infrastructure.retry_strategy_pattern import (
            RetryStrategyPattern,
        )

        strategy = RetryStrategyPattern(max_retries=3, initial_delay=0.1)

        async def successful_operation():
            return "success"

        result = await strategy.execute_async(successful_operation)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_strategy_success_after_retries(self):
        """Deve tentar novamente e ter sucesso após falhas"""
        from src.scraper.infrastructure.retry_strategy_pattern import (
            RetryStrategyPattern,
        )

        strategy = RetryStrategyPattern(
            max_retries=3, initial_delay=0.01
        )  # Delay curto para teste

        attempt_count = 0

        async def failing_then_success():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return "success_after_retries"

        result = await strategy.execute_async(failing_then_success)
        assert result == "success_after_retries"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_strategy_max_retries_exceeded(self):
        """Deve falhar após esgotar todas as tentativas"""
        from src.scraper.infrastructure.retry_strategy_pattern import (
            RetryStrategyPattern,
        )

        strategy = RetryStrategyPattern(max_retries=2, initial_delay=0.01)

        async def always_failing():
            raise Exception("Always fails")

        with pytest.raises(Exception, match="Always fails"):
            await strategy.execute_async(always_failing)

    @pytest.mark.asyncio
    async def test_retry_strategy_uses_exponential_backoff(self, caplog):
        """Test that the retry strategy uses exponential backoff and fails after max retries."""
        from src.scraper.infrastructure.retry_strategy_pattern import (
            RetryStrategyPattern,
        )

        # Mock do scraping strategy para teste
        scraping_strategy = AsyncMock()
        scraping_strategy.scrape_url.side_effect = Exception("Strategy failed")

        # Mock do retry strategy para teste
        retry_strategy = RetryStrategyPattern(max_retries=3, initial_delay=0.1)

        # A operação deve falhar após todas as tentativas
        with pytest.raises(
            Exception, match="All 4 attempts failed. Last error: Strategy failed"
        ):
            await retry_strategy.execute_async(
                scraping_strategy.scrape_url, "https://example.com"
            )

        # Verifica se as tentativas foram logadas com backoff exponencial
        assert "Attempt 1 failed: Strategy failed. Retrying in 0.10s..." in caplog.text
        assert "Attempt 2 failed: Strategy failed. Retrying in 0.20s..." in caplog.text
        assert "Attempt 3 failed: Strategy failed. Retrying in 0.40s..." in caplog.text
        assert "Final attempt 4 failed: Strategy failed" in caplog.text


class TestScrapingMetricsCollector:
    """Testes para ScrapingMetricsCollector - responsabilidade única de coleta de métricas"""

    def test_metrics_initialization(self):
        """Deve inicializar coletor de métricas"""
        from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
            ScrapingMetricsCollector,
        )

        collector = ScrapingMetricsCollector(enabled=True)
        assert collector.enabled is True
        assert collector.last_metrics == {}

    def test_start_operation_timing(self):
        """Deve iniciar cronometragem de operação"""
        from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
            ScrapingMetricsCollector,
        )

        collector = ScrapingMetricsCollector(enabled=True)
        start_time = collector.start_operation()

        assert isinstance(start_time, float)
        assert start_time > 0

    def test_record_scraping_success(self):
        """Deve registrar métricas de sucesso de scraping"""
        from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
            ScrapingMetricsCollector,
        )

        collector = ScrapingMetricsCollector(enabled=True)
        start_time = collector.start_operation()

        collector.record_scraping_success(
            start_time=start_time,
            strategy_used="playwright_optimized",
            attempts=1,
            final_url="https://example.com",
        )

        metrics = collector.get_last_metrics()
        assert metrics["success"] is True
        assert metrics["strategy_used"] == "playwright_optimized"
        assert metrics["attempts"] == 1
        assert "total_time" in metrics

    def test_record_scraping_failure(self):
        """Deve registrar métricas de falha de scraping"""
        from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
            ScrapingMetricsCollector,
        )

        collector = ScrapingMetricsCollector(enabled=True)
        start_time = collector.start_operation()

        collector.record_scraping_failure(
            start_time=start_time, error_message="Test error", attempts=3
        )

        metrics = collector.get_last_metrics()
        assert metrics["success"] is False
        assert metrics["error_message"] == "Test error"
        assert metrics["attempts"] == 3


class TestPlaywrightScrapingStrategy:
    """Testes para PlaywrightScrapingStrategy - responsabilidade única de scraping com Playwright"""

    @pytest.mark.asyncio
    async def test_playwright_strategy_initialization(self):
        """Deve inicializar estratégia Playwright com configuração"""
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
        )
        from src.scraper.infrastructure.web_scraping.playwright_scraping_strategy import (
            PlaywrightScrapingStrategy,
        )

        config = FallbackConfig(
            playwright_timeout=30,
            enable_resource_blocking=True,
            blocked_resource_types=["image", "stylesheet"],
        )

        strategy = PlaywrightScrapingStrategy(config)
        assert strategy.config == config
        assert strategy.timeout == 30
        assert strategy.enable_resource_blocking is True

    @pytest.mark.asyncio
    async def test_playwright_strategy_scrape_url(self):
        """Deve fazer scraping de URL com Playwright"""
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
        )
        from src.scraper.infrastructure.web_scraping.playwright_scraping_strategy import (
            PlaywrightScrapingStrategy,
        )

        config = FallbackConfig(playwright_timeout=30)
        strategy = PlaywrightScrapingStrategy(config)

        # Mock do Playwright para teste
        with patch(
            "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.async_playwright"
        ) as mock_playwright:
            mock_page = AsyncMock()
            mock_page.content.return_value = "<html><body>Test content</body></html>"
            mock_page.goto.return_value = AsyncMock(status=200)

            mock_context = AsyncMock()
            mock_context.new_page.return_value = mock_page

            mock_browser = AsyncMock()
            mock_browser.new_context.return_value = mock_context

            mock_p = AsyncMock()
            mock_p.chromium.launch.return_value = mock_browser

            mock_playwright.return_value.__aenter__.return_value = mock_p

            # Create ScrapingRequest object instead of passing string
            request = ScrapingRequest(url="https://example.com")
            result = await strategy.scrape_url(request)

            assert "Test content" in result
            mock_page.goto.assert_called_once()


class TestRequestsScrapingStrategy:
    """Testes para RequestsScrapingStrategy - responsabilidade única de scraping com HTTP requests"""

    @pytest.mark.asyncio
    async def test_requests_strategy_initialization(self):
        """Deve inicializar estratégia de requests com configuração"""
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
        )
        from src.scraper.infrastructure.web_scraping.requests_scraping_strategy import (
            RequestsScrapingStrategy,
        )

        config = FallbackConfig(requests_timeout=15)
        strategy = RequestsScrapingStrategy(config)

        assert strategy.config == config
        assert strategy.timeout == 15

    @pytest.mark.asyncio
    async def test_requests_strategy_scrape_url(self):
        """Deve fazer scraping de URL com HTTP requests"""
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
        )
        from src.scraper.infrastructure.web_scraping.requests_scraping_strategy import (
            RequestsScrapingStrategy,
        )

        config = FallbackConfig(requests_timeout=15)
        strategy = RequestsScrapingStrategy(config)

        # Mock do httpx para teste
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.text = "<html><body>HTTP content</body></html>"
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            # Create ScrapingRequest object instead of passing string
            request = ScrapingRequest(url="https://example.com")
            result = await strategy.scrape_url(request)

            assert "HTTP content" in result


class TestFallbackOrchestrator:
    """Testes para FallbackOrchestrator - orquestração das estratégias e padrões"""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization_with_dependency_injection(self):
        """Deve inicializar com injeção de dependências"""
        from src.scraper.application.services.fallback_orchestrator import (
            FallbackOrchestrator,
        )
        from src.scraper.infrastructure.circuit_breaker_pattern import (
            CircuitBreakerPattern,
        )
        from src.scraper.infrastructure.retry_strategy_pattern import (
            RetryStrategyPattern,
        )

        circuit_breaker = CircuitBreakerPattern(
            failure_threshold=5, recovery_timeout=60
        )
        retry_strategy = RetryStrategyPattern(max_retries=3, initial_delay=1.0)

        orchestrator = FallbackOrchestrator(
            circuit_breaker=circuit_breaker, retry_strategy=retry_strategy
        )

        assert orchestrator.circuit_breaker == circuit_breaker
        assert orchestrator.retry_strategy == retry_strategy
        assert orchestrator.playwright_strategy is not None
        assert orchestrator.requests_strategy is not None
        assert orchestrator.metrics_collector is not None

    @pytest.mark.asyncio
    async def test_orchestrator_scrape_url_success(self):
        """Deve fazer scraping com sucesso usando primeira estratégia"""
        from src.scraper.application.services.fallback_orchestrator import (
            FallbackOrchestrator,
        )
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
        )

        config = FallbackConfig()
        orchestrator = FallbackOrchestrator(config=config)

        # Mock da estratégia Playwright para sucesso
        orchestrator.playwright_strategy = AsyncMock()
        orchestrator.playwright_strategy.scrape_url.return_value = (
            "<html>Success</html>"
        )

        # Create ScrapingRequest object instead of passing string
        request = ScrapingRequest(url="https://example.com")
        result = await orchestrator.scrape_url(request)

        assert result.success is True
        assert "Success" in result.content
        assert result.strategy_used.value == "playwright_optimized"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_to_requests(self):
        """Deve usar fallback para requests quando Playwright falha"""
        from src.scraper.application.services.fallback_orchestrator import (
            FallbackOrchestrator,
        )
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
        )

        config = FallbackConfig()
        orchestrator = FallbackOrchestrator(config=config)

        # Mock Playwright para falhar
        orchestrator.playwright_strategy = AsyncMock()
        orchestrator.playwright_strategy.scrape_url.side_effect = Exception(
            "Playwright failed"
        )

        # Mock requests para sucesso
        orchestrator.requests_strategy = AsyncMock()
        orchestrator.requests_strategy.scrape_url.return_value = (
            "<html>Fallback success</html>"
        )

        # Create ScrapingRequest object instead of passing string
        request = ScrapingRequest(url="https://example.com")
        result = await orchestrator.scrape_url(request)

        assert result.success is True
        assert "Fallback success" in result.content
        assert result.strategy_used.value == "requests_fallback"
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_orchestrator_circuit_breaker_open(self):
        """Deve abortar quando circuit breaker estiver aberto"""
        from src.scraper.application.services.fallback_orchestrator import (
            FallbackOrchestrator,
        )

        # Circuit breaker que está aberto
        circuit_breaker = Mock()
        circuit_breaker.is_open = True

        orchestrator = FallbackOrchestrator(circuit_breaker=circuit_breaker)

        # Create ScrapingRequest object instead of passing string
        request = ScrapingRequest(url="https://example.com")
        result = await orchestrator.scrape_url(request)

        assert result.success is False
        assert "Circuit breaker is open" in result.error
        assert result.strategy_used.value == "all_failed"


class TestBackwardCompatibility:
    """Testes para garantir compatibilidade com interface original"""

    @pytest.mark.asyncio
    async def test_intelligent_fallback_scraper_interface_preserved(self):
        """Deve manter interface original mas usar classes refatoradas internamente"""
        from src.scraper.infrastructure.web_scraping.intelligent_fallback_scraper import (
            FallbackConfig,
            IntelligentFallbackScraper,
        )

        config = FallbackConfig()
        scraper = IntelligentFallbackScraper(config)

        # Interface deve ser mantida
        assert hasattr(scraper, "scrape_url")
        assert hasattr(scraper, "config")

        # Mas internamente deve usar o orquestrador refatorado
        assert hasattr(scraper, "_orchestrator")  # Deve delegar para orquestrador

    def test_single_responsibility_compliance(self):
        """Deve verificar que cada classe tem responsabilidade única"""
        from src.scraper.infrastructure.circuit_breaker_pattern import (
            CircuitBreakerPattern,
        )
        from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
            ScrapingMetricsCollector,
        )
        from src.scraper.infrastructure.retry_strategy_pattern import (
            RetryStrategyPattern,
        )

        # CircuitBreakerPattern - apenas circuit breaker
        breaker = CircuitBreakerPattern(failure_threshold=5, recovery_timeout=60)
        assert hasattr(breaker, "record_failure")
        assert hasattr(breaker, "record_success")
        assert hasattr(breaker, "is_open")
        assert not hasattr(
            breaker, "scrape_url"
        )  # Não deve ter outras responsabilidades

        # RetryStrategyPattern - apenas retry
        strategy = RetryStrategyPattern(max_retries=3, initial_delay=1.0)
        assert hasattr(strategy, "execute_async")
        assert not hasattr(
            strategy, "can_execute"
        )  # Não deve ter responsabilidade de circuit breaker

        # ScrapingMetricsCollector - apenas métricas
        collector = ScrapingMetricsCollector(enabled=True)
        assert hasattr(collector, "record_scraping_success")
        assert hasattr(collector, "record_scraping_failure")
        assert not hasattr(
            collector, "execute"
        )  # Não deve ter outras responsabilidades
