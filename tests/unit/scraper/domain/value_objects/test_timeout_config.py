from src.scraper.domain.value_objects.timeout_config import TimeoutConfig
from src.scraper.domain.value_objects.value_objects import TimeoutValue

def test_timeout_config_creation_and_properties():
    config = TimeoutConfig(
        page_timeout=TimeoutValue(10),
        grace_period=TimeoutValue(2.5)
    )
    assert config.page_timeout.seconds == 10
    assert config.grace_period.seconds == 2.5
    assert config.page_timeout_milliseconds == 10000
    assert config.grace_period_milliseconds == 2500
    assert config.total_timeout.seconds == 12.5

def test_timeout_config_defaults():
    config = TimeoutConfig()
    assert config.page_timeout.seconds > 0
    assert config.grace_period.seconds > 0
    assert isinstance(config.page_timeout, TimeoutValue)
    assert isinstance(config.grace_period, TimeoutValue)
