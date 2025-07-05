import pytest
from src.app_factory import create_app_dependencies
from src.settings import Settings

@pytest.mark.asyncio
async def test_create_app_dependencies_returns_tuple(monkeypatch):
    class DummyOrchestrator:
        async def initialize(self): pass
    class DummyWebScrapingService:
        orchestrator = DummyOrchestrator()
    class DummyInjector:
        def get(self, cls): return DummyWebScrapingService()
    monkeypatch.setattr("src.app_factory.Injector", lambda *a, **k: DummyInjector())
    monkeypatch.setattr("src.app_factory.AppModule", lambda s: None)
    settings = Settings()
    web_scraper, returned_settings = await create_app_dependencies(settings)
    assert returned_settings is settings
