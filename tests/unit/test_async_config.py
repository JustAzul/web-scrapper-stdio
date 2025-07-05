import pytest
import asyncio
from src.async_config import AsyncConfigLoader

@pytest.mark.asyncio
async def test_async_config_loader_loads_config():
    loader = AsyncConfigLoader()
    config = await loader.load_config_async()
    assert hasattr(config, "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS")
    assert loader.is_loaded()
