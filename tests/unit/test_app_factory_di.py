from src.app_factory_di import AppModule
from src.settings import Settings

def test_app_module_instantiation():
    settings = Settings()
    module = AppModule(settings)
    assert isinstance(module, AppModule)
