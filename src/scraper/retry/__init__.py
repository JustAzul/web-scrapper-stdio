"""
Retry Strategy Implementation for Web Scraper MCP.

This module implements intelligent retry strategies for handling transient failures
following T025 requirements:

1. Exponential backoff with jitter
2. Circuit breaker pattern
3. Retry policies per error type
4. Maximum retry limits and timeouts
5. Retry metrics and monitoring

TDD Implementation: GREEN phase - comprehensive retry system.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

from src.logger import get_logger
from src.scraper.domain.exceptions import (
    ContentExtractionError,
    NetworkError,
    ScraperError,
    TimeoutError,
)

logger = get_logger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    backoff_multiplier: float = 2.0
    timeout: Optional[float] = None

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""

    attempt_number: int
    delay: float
    exception: Optional[Exception] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class RetryResult:
    """Result of retry operation."""

    success: bool
    result: Any = None
    attempts: List[RetryAttempt] = None
    total_duration: float = 0.0
    final_exception: Optional[Exception] = None

    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 60.0

    def __post_init__(self):
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be at least 1")


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.logger = get_logger(__name__)

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if time.time() - self.last_failure_time >= self.config.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.logger.info("Circuit breaker moved to HALF_OPEN state")
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Record a successful execution."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.info("Circuit breaker moved to CLOSED state")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.logger.warning("Circuit breaker moved to OPEN state")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning("Circuit breaker moved back to OPEN state")


class RetryManager:
    """Manages retry logic and circuit breakers."""

    def __init__(self):
        self.default_config = RetryConfig()
        self.error_configs: Dict[Type[Exception], RetryConfig] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger(__name__)

    def configure_error_retry(self, error_type: Type[Exception], config: RetryConfig):
        """Configure retry behavior for specific error types."""
        self.error_configs[error_type] = config

    def get_circuit_breaker(
        self, key: str, config: CircuitBreakerConfig = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker for a key."""
        if key not in self.circuit_breakers:
            cb_config = config or CircuitBreakerConfig()
            self.circuit_breakers[key] = CircuitBreaker(cb_config)
        return self.circuit_breakers[key]

    def _get_retry_config(self, exception: Exception) -> RetryConfig:
        """Get retry configuration for an exception."""
        for error_type, config in self.error_configs.items():
            if isinstance(exception, error_type):
                return config
        return self.default_config

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt
        else:
            delay = config.base_delay

        # Apply maximum delay limit
        delay = min(delay, config.max_delay)

        # Add jitter if enabled
        if config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            # Use secrets for cryptographically secure jitter
            import secrets

            delay += secrets.SystemRandom().uniform(-jitter_amount, jitter_amount)

        delay = max(0, delay)  # Ensure non-negative

        return delay

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        config: Optional[RetryConfig] = None,
        circuit_breaker_key: Optional[str] = None,
        **kwargs,
    ) -> RetryResult:
        """Execute function with retry logic."""
        retry_config = config or self.default_config
        attempts = []
        start_time = time.time()

        # Check circuit breaker if specified
        circuit_breaker = None
        if circuit_breaker_key:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_key)
            if not circuit_breaker.can_execute():
                return RetryResult(
                    success=False,
                    attempts=attempts,
                    total_duration=time.time() - start_time,
                    final_exception=Exception("Circuit breaker is OPEN"),
                )

        for attempt_num in range(1, retry_config.max_attempts + 1):
            try:
                # Execute function with timeout if specified
                if retry_config.timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=retry_config.timeout
                    )
                else:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_duration=time.time() - start_time,
                )

            except Exception as e:
                # Record attempt
                delay = (
                    self._calculate_delay(attempt_num, retry_config)
                    if attempt_num < retry_config.max_attempts
                    else 0
                )
                attempts.append(
                    RetryAttempt(attempt_number=attempt_num, delay=delay, exception=e)
                )

                # Check if we should retry this exception
                if not self._should_retry(e):
                    self.logger.info(f"Not retrying exception type: {type(e).__name__}")
                    break

                # If this is the last attempt, don't delay
                if attempt_num >= retry_config.max_attempts:
                    break

                # Log retry attempt
                self.logger.warning(
                    f"Attempt {attempt_num} failed: {str(e)}. Retrying in {delay:.2f}s"
                )

                # Wait before retry
                if delay > 0:
                    await asyncio.sleep(delay)

        # All attempts failed
        if circuit_breaker:
            circuit_breaker.record_failure()

        final_exception = (
            attempts[-1].exception if attempts else Exception("No attempts made")
        )
        return RetryResult(
            success=False,
            attempts=attempts,
            total_duration=time.time() - start_time,
            final_exception=final_exception,
        )

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should be retried."""
        # Retry network and timeout errors
        if isinstance(
            exception, (NetworkError, TimeoutError, ConnectionError, OSError)
        ):
            return True

        # Don't retry content extraction errors (usually permanent)
        if isinstance(exception, ContentExtractionError):
            return False

        # Retry generic scraper errors
        if isinstance(exception, ScraperError):
            return True

        # Don't retry programming errors
        if isinstance(exception, (ValueError, TypeError, AttributeError)):
            return False

        # Default: retry unknown exceptions
        return True


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    circuit_breaker_key: Optional[str] = None,
):
    """Decorator for adding retry logic to functions."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_manager = RetryManager()
            config = RetryConfig(
                max_attempts=max_attempts, base_delay=base_delay, strategy=strategy
            )

            result = await retry_manager.execute_with_retry(
                func,
                *args,
                config=config,
                circuit_breaker_key=circuit_breaker_key,
                **kwargs,
            )

            if result.success:
                return result.result
            else:
                raise result.final_exception

        return wrapper

    return decorator


# Export all retry components
__all__ = [
    "RetryStrategy",
    "RetryConfig",
    "RetryAttempt",
    "RetryResult",
    "CircuitBreakerState",
    "CircuitBreakerConfig",
    "CircuitBreaker",
    "RetryManager",
    "retry",
]
