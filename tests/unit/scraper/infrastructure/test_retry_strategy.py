import pytest
import asyncio
from src.scraper.infrastructure.retry_strategy import RetryStrategy

@pytest.mark.asyncio
async def test_retry_strategy_retries_and_succeeds():
    strategy = RetryStrategy(max_retries=3, initial_delay=0.01)
    attempts = []
    async def flaky():
        if len(attempts) < 2:
            attempts.append(1)
            raise Exception("fail")
        return "ok"
    result = await strategy.execute_async(flaky)
    assert result == "ok"
    assert len(attempts) == 2

@pytest.mark.asyncio
async def test_retry_strategy_fails_after_max_attempts():
    strategy = RetryStrategy(max_retries=2, initial_delay=0.01)
    async def always_fail():
        raise Exception("fail")
    with pytest.raises(Exception):
        await strategy.execute_async(always_fail)
