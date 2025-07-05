"""
TDD Tests for T003: Refatorar IntelligentFallbackScraper
Objetivo: Quebrar God Class (375 linhas) em classes menores seguindo SRP

FASE RED: Testes que falham primeiro - definindo comportamento esperado após refatoração
"""

import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from injector import Injector, singleton

from src.scraper.application.services.fallback_orchestrator import (
    FallbackOrchestrator,
)
from src.scraper.application.services.scraping_request import ScrapingRequest
from src.scraper.infrastructure.circuit_breaker_pattern import CircuitBreakerPattern
from src.scraper.infrastructure.monitoring.scraping_metrics_collector import (
    ScrapingMetricsCollector,
)
from src.scraper.infrastructure.retry_strategy_pattern import RetryStrategyPattern
from src.scraper.infrastructure.web_scraping.fallback_scraper import (
    FallbackConfig,
    IntelligentFallbackScraper,
    ScrapingResult,
)
from src.scraper.infrastructure.web_scraping.playwright_scraping_strategy import (
    PlaywrightScrapingStrategy,
)
from src.scraper.infrastructure.web_scraping.requests_scraping_strategy import (
    RequestsScrapingStrategy,
)


@pytest.fixture
def injector():
    i = Injector()
    circuit_breaker_mock = Mock()
    circuit_breaker_mock.is_open = False  # Default to closed
    i.binder.bind(CircuitBreakerPattern, to=circuit_breaker_mock, scope=singleton)
    i.binder.bind(RetryStrategyPattern, to=Mock(), scope=singleton)
    i.binder.bind(
        ScrapingMetricsCollector,
        to=Mock(start_operation=Mock(return_value=time.time())),
        scope=singleton,
    )
    i.binder.bind(PlaywrightScrapingStrategy, to=AsyncMock(), scope=singleton)
    i.binder.bind(RequestsScrapingStrategy, to=AsyncMock(), scope=singleton)
    i.binder.bind(FallbackOrchestrator, scope=singleton)
    return i


@pytest.fixture
def fallback_orchestrator(injector: Injector):
    return injector.get(FallbackOrchestrator)


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
            assert breaker.get_state() == "OPEN"
            assert breaker.last_failure_time == 100.0

            # 3. Check that it's open before recovery timeout
            mock_time.return_value = 104.0  # 4 seconds later
            assert breaker.is_open is True
            assert breaker.get_state() == "OPEN"  # State should not change yet

            # 4. Move time past the recovery timeout
            mock_time.return_value = 105.1  # 5.1 seconds later
            assert breaker.is_open is False  # is_open is now False

            # 5. Verify the state transitioned by calling get_state()
            assert breaker.get_state() == "HALF-OPEN"
            assert breaker.state == "HALF-OPEN"  # Check internal state


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
            start_time=start_time,
            strategy_attempted="playwright_optimized",
            attempts=3,
            error_message="Test error",
        )

        metrics = collector.get_last_metrics()
        assert not metrics["success"]
        assert metrics["strategy_used"] == "playwright_optimized"
        assert metrics["attempts"] == 3
        assert metrics["error_message"] == "Test error"

    @pytest.mark.asyncio
    async def test_requests_strategy_scrape_url_http_error(self, httpserver):
        """Should raise HTTPStatusError for non-2xx responses"""
        server_url = httpserver.url_for("/")
        httpserver.expect_request("/").respond_with_data("Error", status=404)

        strategy = RequestsScrapingStrategy(FallbackConfig())
        request = ScrapingRequest(url=server_url)
        with pytest.raises(httpx.HTTPStatusError):
            await strategy.scrape_url(request)


class TestPlaywrightScrapingStrategy:
    """Testes para PlaywrightScrapingStrategy - responsabilidade de scraping com Playwright"""

    @pytest.mark.asyncio
    async def test_playwright_strategy_initialization(self):
        """Deve inicializar estratégia Playwright com configuração"""
        from src.scraper.infrastructure.web_scraping.playwright_scraping_strategy import (
            PlaywrightScrapingStrategy,
        )

        config = FallbackConfig()
        strategy = PlaywrightScrapingStrategy(config)
        assert strategy.config == config

    @pytest.mark.asyncio
    async def test_playwright_strategy_scrape_url(self, mocker):
        """Deve fazer scraping de URL com Playwright e retornar conteúdo limpo"""
        config = FallbackConfig(playwright_timeout=10, enable_resource_blocking=False)
        strategy = PlaywrightScrapingStrategy(config)
        request = ScrapingRequest(url="https://example.com")

        # Mock completo da hierarquia do Playwright
        mock_page = mocker.AsyncMock()
        mock_page.goto.return_value.status = 200
        mock_page.content.return_value = (
            "<html><head><style>.hide{display:none}</style></head>"
            "<body><nav>Menu</nav><main>Main content</main><footer>Footer</footer></body></html>"
        )

        mock_context = mocker.AsyncMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = mocker.AsyncMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright_instance = mocker.AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser

        mock_async_playwright = mocker.patch(
            "src.scraper.infrastructure.web_scraping.playwright_scraping_strategy.async_playwright"
        )
        mock_async_playwright.return_value.start = mocker.AsyncMock(
            return_value=mock_playwright_instance
        )

        await strategy.initialize()
        content = await strategy.scrape_url(request)
        await strategy.shutdown()

        assert "<nav>" not in content
        assert "<main>Main content</main>" in content


class TestRequestsScrapingStrategy:
    """Testes para RequestsScrapingStrategy - responsabilidade de scraping com requests"""

    @pytest.mark.asyncio
    async def test_requests_strategy_initialization(self):
        """Deve inicializar estratégia de requests com configuração"""
        strategy = RequestsScrapingStrategy(FallbackConfig())
        assert isinstance(strategy.config, FallbackConfig)

    @pytest.mark.asyncio
    async def test_requests_strategy_scrape_url(self):
        """Deve fazer scraping de URL com HTTP requests"""
        strategy = RequestsScrapingStrategy(FallbackConfig())

        # Mock do httpx para não fazer requisição real
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Requests content</body></html>"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )
            # Create a ScrapingRequest object as required by the method signature
            request = ScrapingRequest(url="https://example.com")
            result = await strategy.scrape_url(request, {})
            assert result == "<html><body>Requests content</body></html>"


class TestFallbackOrchestrator:
    """Testes para FallbackOrchestrator após refatoração"""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization_with_dependency_injection(
        self, fallback_orchestrator
    ):
        """Deve inicializar com dependências injetadas (mocks)"""
        assert fallback_orchestrator is not None
        assert fallback_orchestrator.circuit_breaker is not None
        assert fallback_orchestrator.metrics_collector is not None
        assert fallback_orchestrator.playwright_strategy is not None
        assert fallback_orchestrator.requests_strategy is not None

    @pytest.mark.asyncio
    async def test_orchestrator_scrape_url_success(self, fallback_orchestrator):
        """Deve ter sucesso com a primeira estratégia (Playwright)"""
        # Configure the mock that's actually used by the orchestrator
        fallback_orchestrator.playwright_strategy.scrape_url.return_value = "Playwright success"

        request = ScrapingRequest(url="https://example.com")
        result = await fallback_orchestrator.scrape_url(request)

        assert result.success is True
        assert result.content == "Playwright success"
        fallback_orchestrator.playwright_strategy.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_to_requests(self, fallback_orchestrator):
        """Deve fazer fallback para requests quando Playwright falha"""
        fallback_orchestrator.playwright_strategy.scrape_url.side_effect = Exception("Playwright failed")
        fallback_orchestrator.requests_strategy.scrape_url.return_value = "Requests success"

        request = ScrapingRequest(url="https://example.com")
        result = await fallback_orchestrator.scrape_url(request)

        assert result.success is True
        assert result.content == "Requests success"
        fallback_orchestrator.playwright_strategy.scrape_url.assert_called_once()
        fallback_orchestrator.requests_strategy.scrape_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrator_circuit_breaker_open(self, fallback_orchestrator):
        """Deve falhar imediatamente se o circuit breaker estiver aberto"""
        fallback_orchestrator.circuit_breaker.is_open = True

        request = ScrapingRequest(url="https://example.com")
        result = await fallback_orchestrator.scrape_url(request)

        assert result.success is False
        assert "Circuit breaker is open" in result.error


@pytest.mark.asyncio
class TestFallbackScraperRefactor:
    """Testes para garantir que a classe wrapper antiga ainda funciona"""

    async def test_single_responsibility_compliance(self, mocker):
        """
        Testa se o IntelligentFallbackScraper delega a chamada para o orquestrador
        e não realiza o trabalho de scraping diretamente.
        """
        # 1. Preparação
        # Cria um mock que espelha a interface do FallbackOrchestrator
        mock_orchestrator = mocker.create_autospec(
            FallbackOrchestrator, instance=True, spec_set=False
        )
        mock_orchestrator.scrape_url.return_value = ScrapingResult(
            success=True,
            content="<p>Success</p>",
            strategy_used="mock_strategy",
            attempts=1,
            final_url="https://example.com",
        )
        # Add the circuit_breaker attribute that IntelligentFallbackScraper expects
        mock_orchestrator.circuit_breaker = mocker.Mock()

        # 2. Execução
        # Injeta o mock diretamente no construtor
        scraper = IntelligentFallbackScraper(
            config=FallbackConfig(), orchestrator=mock_orchestrator
        )
        request = ScrapingRequest(url="https://example.com")
        result = await scraper.scrape_url(request.url)

        # 3. Verificação
        mock_orchestrator.scrape_url.assert_called_once_with(request)
        assert result.success is True
        assert result.content == "<p>Success</p>"
