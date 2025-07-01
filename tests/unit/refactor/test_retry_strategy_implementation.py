"""
Test suite for T025: Retry Strategy Implementation.

TDD Implementation: RED-GREEN-REFACTOR cycle tests for retry system.
"""

import pytest

from src.scraper.domain.exceptions import NetworkError, TimeoutError
from src.scraper.retry import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    RetryConfig,
    RetryManager,
    RetryStrategy,
    retry,
)


class TestRetryConfig:
    """Test RetryConfig validation."""

    def test_retry_config_creation(self):
        """Test basic retry config creation."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        )

        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_retry_config_validation(self):
        """Test retry config validation."""
        with pytest.raises(ValueError):
            RetryConfig(max_attempts=0)

        with pytest.raises(ValueError):
            RetryConfig(base_delay=-1.0)

        with pytest.raises(ValueError):
            RetryConfig(base_delay=10.0, max_delay=5.0)


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""

    def test_circuit_breaker_creation(self):
        """Test circuit breaker initialization."""
        config = CircuitBreakerConfig(
            failure_threshold=3, success_threshold=2, timeout=30.0
        )
        cb = CircuitBreaker(config)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(CircuitBreakerConfig())

        assert cb.can_execute() is True

        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_open_state(self):
        """Test circuit breaker transition to open state."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config)

        # Record failures to trigger open state
        cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_execute() is False


class TestRetryManager:
    """Test RetryManager functionality."""

    def test_retry_manager_creation(self):
        """Test retry manager initialization."""
        manager = RetryManager()

        assert manager.default_config is not None
        assert isinstance(manager.error_configs, dict)
        assert isinstance(manager.circuit_breakers, dict)

    def test_delay_calculation_exponential(self):
        """Test exponential backoff delay calculation."""
        manager = RetryManager()
        config = RetryConfig(
            base_delay=1.0,
            backoff_multiplier=2.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=False,
        )

        delay1 = manager._calculate_delay(1, config)
        delay2 = manager._calculate_delay(2, config)
        delay3 = manager._calculate_delay(3, config)

        assert delay1 == 1.0  # 1.0 * 2^0
        assert delay2 == 2.0  # 1.0 * 2^1
        assert delay3 == 4.0  # 1.0 * 2^2

    def test_delay_calculation_fixed(self):
        """Test fixed delay calculation."""
        manager = RetryManager()
        config = RetryConfig(
            base_delay=2.0, strategy=RetryStrategy.FIXED_DELAY, jitter=False
        )

        delay1 = manager._calculate_delay(1, config)
        delay2 = manager._calculate_delay(2, config)
        delay3 = manager._calculate_delay(3, config)

        assert delay1 == 2.0
        assert delay2 == 2.0
        assert delay3 == 2.0

    def test_should_retry_logic(self):
        """Test retry decision logic."""
        manager = RetryManager()

        # Should retry network errors
        assert manager._should_retry(NetworkError("Network failed")) is True
        assert manager._should_retry(TimeoutError("Timeout")) is True
        assert manager._should_retry(ConnectionError("Connection failed")) is True

        # Should not retry programming errors
        assert manager._should_retry(ValueError("Invalid value")) is False
        assert manager._should_retry(TypeError("Type error")) is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution with retry."""
        manager = RetryManager()

        async def success_func():
            return "success"

        result = await manager.execute_with_retry(success_func)

        assert result.success is True
        assert result.result == "success"
        assert len(result.attempts) == 0  # No retries needed

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_then_success(self):
        """Test execution that fails then succeeds."""
        manager = RetryManager()
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("Network failed")
            return "success"

        config = RetryConfig(max_attempts=3, base_delay=0.01)  # Fast retry for testing
        result = await manager.execute_with_retry(flaky_func, config=config)

        assert result.success is True
        assert result.result == "success"
        assert len(result.attempts) == 1  # One failed attempt
        assert call_count == 2  # Called twice


class TestRetryDecorator:
    """Test retry decorator functionality."""

    @pytest.mark.asyncio
    async def test_retry_decorator_success(self):
        """Test retry decorator with successful function."""

        @retry(max_attempts=3, base_delay=0.01)
        async def success_func():
            return "decorated success"

        result = await success_func()
        assert result == "decorated success"

    @pytest.mark.asyncio
    async def test_retry_decorator_failure_then_success(self):
        """Test retry decorator with flaky function."""
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("Network failed")
            return "eventual success"

        result = await flaky_func()
        assert result == "eventual success"
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
