"""
Tests for the Pydantic-based settings management system.
"""

import pytest

from src.settings import get_settings, reload_settings


class TestSettings:
    """
    Tests the application's ability to load configuration from environment
    variables using the Pydantic settings system.
    """

    def setup_method(self):
        """Ensure settings are reloaded before each test."""
        reload_settings()

    def teardown_method(self):
        """Ensure settings are reloaded after each test to avoid side effects."""
        reload_settings()

    def test_default_settings_load_correctly(self):
        """
        Tests that default values are loaded when no environment variables are set.
        """
        settings = get_settings()
        assert settings.default_timeout_seconds == 30
        assert settings.debug_logs_enabled is False

    def test_timeout_from_environment_variable(self, monkeypatch):
        """
        Verify that settings are correctly overridden by environment variables.
        """
        monkeypatch.setenv("DEFAULT_TIMEOUT_SECONDS", "15")

        # Reload settings to pick up the new environment variable
        reload_settings()
        settings = get_settings()

        assert settings.default_timeout_seconds == 15

    def test_debug_logs_enabled_from_env(self, monkeypatch):
        """
        Tests that boolean fields are correctly parsed from string environment variables.
        """
        monkeypatch.setenv("DEBUG_LOGS_ENABLED", "true")

        reload_settings()
        settings = get_settings()

        assert settings.debug_logs_enabled is True

    def test_invalid_boolean_env_var_raises_error(self, monkeypatch):
        """
        Tests that the custom boolean validator raises an error for invalid values.
        """
        monkeypatch.setenv("DEBUG_LOGS_ENABLED", "invalid-value")

        with pytest.raises(ValueError, match="Invalid boolean value"):
            reload_settings()
            get_settings()

    def test_settings_are_cached(self, monkeypatch):
        """
        Tests that the get_settings() function returns a cached instance unless reloaded.
        """
        # Get initial settings
        settings1 = get_settings()
        assert settings1.default_timeout_seconds == 30

        # Change environment variable, but DO NOT reload settings
        monkeypatch.setenv("DEFAULT_TIMEOUT_SECONDS", "50")

        # Get settings again, should be the same cached instance
        settings2 = get_settings()

        assert settings1 is settings2
        assert settings2.default_timeout_seconds == 30  # Should still be the old value

        # Now, reload the settings
        reload_settings()
        settings3 = get_settings()

        assert settings3 is not settings1
        assert settings3.default_timeout_seconds == 50  # Should now have the new value
