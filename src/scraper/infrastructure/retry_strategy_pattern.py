"""
RetryStrategyPattern - Responsabilidade única: Implementação de retry com exponential backoff
Parte da refatoração T003 - Quebrar IntelligentFallbackScraper seguindo SRP
"""

import asyncio
import time
import warnings
from typing import Awaitable, Callable, TypeVar

from src.logger import Logger

logger = Logger(__name__)
T = TypeVar("T")


class RetryStrategyPattern:
    """Implementa estratégia de retry com exponential backoff seguindo SRP."""

    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        """
        Inicializa estratégia de retry.
        Args:
            max_retries: Número máximo de tentativas.
            initial_delay: Delay inicial em segundos.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.logger = logger

    async def execute_async(
        self, async_func: Callable[..., Awaitable[T]], *args, **kwargs
    ) -> T:
        """
        Executa uma função assíncrona com a estratégia de retry.
        Raises:
            Exception: A última exceção se todas as tentativas falharem.
        """
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Attempt {attempt + 1}/{self.max_retries + 1}")
                return await async_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt >= self.max_retries:
                    self.logger.error(f"Final attempt {attempt + 1} failed: {e}")
                    break
                delay = self.initial_delay * (2**attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        raise Exception(
            f"All {self.max_retries + 1} attempts failed. Last error: {last_exception}"
        ) from last_exception

    def execute_sync(self, sync_func: Callable[..., T], *args, **kwargs) -> T:
        """
        DEPRECATED: Use execute_async instead.
        Executes a synchronous function with retry logic.
        """
        warnings.warn(
            "execute_sync is deprecated, use execute_async for consistent async patterns.",
            DeprecationWarning,
            stacklevel=2,
        )
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Sync attempt {attempt + 1}/{self.max_retries + 1}")
                return sync_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt >= self.max_retries:
                    self.logger.error(f"Final sync attempt {attempt + 1} failed: {e}")
                    break
                delay = self.initial_delay * (2**attempt)
                self.logger.warning(
                    f"Sync attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
        raise last_exception

    def get_max_retries(self) -> int:
        """Retorna número máximo de tentativas configurado."""
        return self.max_retries

    def get_initial_delay(self) -> float:
        """Retorna delay inicial configurado."""
        return self.initial_delay

    def calculate_total_max_time(self) -> float:
        """Calcula tempo máximo total considerando todos os delays."""
        total_time = 0.0
        for attempt in range(self.max_retries):
            total_time += self.initial_delay * (2**attempt)
        return total_time

    def __repr__(self) -> str:
        """Representação string da estratégia de retry."""
        return (
            f"RetryStrategyPattern(max_retries={self.max_retries}, "
            f"initial_delay={self.initial_delay}s, "
            f"max_total_time={self.calculate_total_max_time():.1f}s)"
        )
