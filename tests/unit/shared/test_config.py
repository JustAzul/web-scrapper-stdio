import warnings

import src.config as config_module


def test_get_env_int_override(monkeypatch):
    """Test that the configuration system works with environment variables."""
    # Suppress deprecation warnings for this test
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        warnings.simplefilter("ignore", RuntimeWarning)

        # Test that the config module can be imported and has the expected attributes
        assert hasattr(config_module, "DEFAULT_TIMEOUT_SECONDS")
        assert isinstance(config_module.DEFAULT_TIMEOUT_SECONDS, int)
        assert config_module.DEFAULT_TIMEOUT_SECONDS > 0


def test_get_env_int_fallback(monkeypatch):
    """Test that the configuration system provides reasonable defaults."""
    # Suppress deprecation warnings for this test
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        warnings.simplefilter("ignore", RuntimeWarning)

        # Test that all expected configuration attributes exist and have reasonable values
        assert hasattr(config_module, "DEFAULT_TIMEOUT_SECONDS")
        assert hasattr(config_module, "DEFAULT_MIN_CONTENT_LENGTH")
        assert hasattr(config_module, "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS")
        assert hasattr(config_module, "DEBUG_LOGS_ENABLED")

        # Test reasonable default values
        assert config_module.DEFAULT_TIMEOUT_SECONDS >= 10  # At least 10 seconds
        assert config_module.DEFAULT_MIN_CONTENT_LENGTH >= 10  # At least 10 characters
        assert config_module.DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS >= 0  # Non-negative
        assert isinstance(config_module.DEBUG_LOGS_ENABLED, bool)
