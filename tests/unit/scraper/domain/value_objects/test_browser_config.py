from src.scraper.domain.value_objects.browser_config import BrowserConfig

def test_browser_config_creation_and_properties():
    config = BrowserConfig(
        user_agent="test-agent",
        wait_for_network_idle=False
    )
    assert config.user_agent == "test-agent"
    assert config.wait_for_network_idle is False
    assert config.has_custom_user_agent is True
    assert config.should_wait_for_network is False
    assert config.get_effective_user_agent("default") == "test-agent"
    assert "test-agent" in str(config)

def test_browser_config_with_user_agent_and_network_wait():
    config = BrowserConfig()
    new_config = config.with_user_agent("ua")
    assert new_config.user_agent == "ua"
    assert new_config.wait_for_network_idle == config.wait_for_network_idle
    new_config2 = config.with_network_wait(False)
    assert new_config2.wait_for_network_idle is False
