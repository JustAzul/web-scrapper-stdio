from src.scraper.domain.value_objects.url_config import URLConfig
import pytest

def test_url_config_creation_and_properties():
    config = URLConfig(
        url="http://Example.com/Path?query=1#frag"
    )
    assert config.url == "http://Example.com/Path?query=1#frag"
    assert config.is_valid is True
    assert config.domain == "example.com"
    assert config.scheme == "http"
    assert config.normalized_url.startswith("http://example.com")
    assert str(config) == config.normalized_url

def test_url_config_invalid_url():
    with pytest.raises(ValueError):
        URLConfig(url="not-a-valid-url")

def test_url_config_empty_url():
    with pytest.raises(ValueError):
        URLConfig(url="")
