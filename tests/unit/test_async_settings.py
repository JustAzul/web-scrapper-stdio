import pytest
from src.async_settings import AsyncSettings

@pytest.mark.asyncio
async def test_async_settings_load_and_reload():
    settings = AsyncSettings()
    assert not settings.is_loaded
    await settings.load_config_async()
    assert settings.is_loaded
    await settings.reload_settings_async()
    assert settings.is_loaded
