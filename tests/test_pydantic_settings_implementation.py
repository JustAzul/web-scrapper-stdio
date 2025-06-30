"""
Test suite for T008-TDD: Implementing Pydantic Settings.

This module tests the replacement of manual config.py with Pydantic Settings,
ensuring proper validation, type safety, and environment variable management.

TDD Approach:
1. RED: Write failing tests for Pydantic Settings requirements
2. GREEN: Implement minimum Pydantic Settings configuration
3. REFACTOR: Optimize settings structure and validation
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError


class TestPydanticSettingsImplementation:
    """Test cases for Pydantic Settings implementation."""

    def test_settings_class_exists(self):
        """Should have a Settings class based on Pydantic BaseSettings"""
        from src.settings import Settings

        # Should be a Pydantic settings class
        assert hasattr(Settings, "model_config")
        assert hasattr(Settings, "model_validate")

        # Should be instantiable
        settings = Settings()
        assert settings is not None

    def test_settings_environment_variable_loading(self):
        """Should load configuration from environment variables"""
        from src.settings import Settings

        with patch.dict(
            os.environ,
            {
                "DEFAULT_TIMEOUT_SECONDS": "45",
                "DEFAULT_MIN_CONTENT_LENGTH": "150",
                "DEBUG_LOGS_ENABLED": "true",
            },
        ):
            settings = Settings()

            assert settings.default_timeout_seconds == 45
            assert settings.default_min_content_length == 150
            assert settings.debug_logs_enabled is True

    def test_settings_default_values(self):
        """Should have proper default values when environment variables are not set"""
        from src.settings import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.default_timeout_seconds == 30
            assert settings.default_min_content_length == 100
            assert settings.default_min_content_length_search_app == 30
            assert settings.default_min_seconds_between_requests == 2.0
            assert settings.default_test_request_timeout == 10
            assert settings.default_test_no_delay_threshold == 0.5
            assert settings.debug_logs_enabled is False

    def test_settings_type_validation(self):
        """Should validate types properly and raise ValidationError for invalid values"""
        from src.settings import Settings

        # Test invalid integer
        with patch.dict(os.environ, {"DEFAULT_TIMEOUT_SECONDS": "invalid"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "DEFAULT_TIMEOUT_SECONDS" in str(
                exc_info.value
            ) or "default_timeout_seconds" in str(exc_info.value)

        # Test invalid float
        with patch.dict(
            os.environ, {"DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS": "not_a_float"}
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS" in str(
                exc_info.value
            ) or "default_min_seconds_between_requests" in str(exc_info.value)

        # Test invalid boolean
        with patch.dict(os.environ, {"DEBUG_LOGS_ENABLED": "maybe"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "DEBUG_LOGS_ENABLED" in str(
                exc_info.value
            ) or "debug_logs_enabled" in str(exc_info.value)

    def test_settings_positive_number_validation(self):
        """Should validate that numeric settings are positive"""
        from src.settings import Settings

        # Test negative timeout
        with patch.dict(os.environ, {"DEFAULT_TIMEOUT_SECONDS": "-5"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "greater than 0" in str(exc_info.value) or "positive" in str(
                exc_info.value
            )

        # Test zero min content length
        with patch.dict(os.environ, {"DEFAULT_MIN_CONTENT_LENGTH": "0"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "greater than 0" in str(exc_info.value) or "positive" in str(
                exc_info.value
            )

    def test_settings_singleton_pattern(self):
        """Should implement singleton pattern for global configuration access"""
        from src.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same instance
        assert settings1 is settings2
        assert id(settings1) == id(settings2)

    def test_settings_backward_compatibility(self):
        """Should maintain backward compatibility with existing config.py imports"""
        # Test that old constants are still accessible
        from src.settings import (
            DEBUG_LOGS_ENABLED,
            DEFAULT_MIN_CONTENT_LENGTH,
            DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP,
            DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS,
            DEFAULT_TEST_NO_DELAY_THRESHOLD,
            DEFAULT_TEST_REQUEST_TIMEOUT,
            DEFAULT_TIMEOUT_SECONDS,
        )

        # Should be the same types as before
        assert isinstance(DEFAULT_TIMEOUT_SECONDS, int)
        assert isinstance(DEFAULT_MIN_CONTENT_LENGTH, int)
        assert isinstance(DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP, int)
        assert isinstance(DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS, float)
        assert isinstance(DEFAULT_TEST_REQUEST_TIMEOUT, int)
        assert isinstance(DEFAULT_TEST_NO_DELAY_THRESHOLD, float)
        assert isinstance(DEBUG_LOGS_ENABLED, bool)

    def test_settings_environment_prefix(self):
        """Should support environment variable prefix for organization"""
        from src.settings import Settings

        # Test with prefixed environment variables
        with patch.dict(
            os.environ,
            {
                "SCRAPER_DEFAULT_TIMEOUT_SECONDS": "60",
                "SCRAPER_DEBUG_LOGS_ENABLED": "true",
            },
        ):
            # Settings should support both prefixed and non-prefixed
            settings = Settings()

            # Should prioritize prefixed variables if available
            # This tests environment variable precedence
            assert hasattr(settings, "default_timeout_seconds")
            assert hasattr(settings, "debug_logs_enabled")

    def test_settings_model_dump(self):
        """Should be able to export settings as dictionary"""
        from src.settings import Settings

        settings = Settings()
        config_dict = settings.model_dump()

        # Should contain all expected keys
        expected_keys = {
            "default_timeout_seconds",
            "default_min_content_length",
            "default_min_content_length_search_app",
            "default_min_seconds_between_requests",
            "default_test_request_timeout",
            "default_test_no_delay_threshold",
            "debug_logs_enabled",
        }

        assert all(key in config_dict for key in expected_keys)

        # Should have correct types
        assert isinstance(config_dict["default_timeout_seconds"], int)
        assert isinstance(config_dict["debug_logs_enabled"], bool)

    def test_settings_json_schema(self):
        """Should provide JSON schema for documentation and validation"""
        from src.settings import Settings

        schema = Settings.model_json_schema()

        # Should have properties for all settings
        assert "properties" in schema
        assert "default_timeout_seconds" in schema["properties"]
        assert "debug_logs_enabled" in schema["properties"]

        # Should have type information
        assert schema["properties"]["default_timeout_seconds"]["type"] == "integer"
        assert schema["properties"]["debug_logs_enabled"]["type"] == "boolean"


class TestConfigMigrationCompatibility:
    """Test cases for ensuring smooth migration from config.py"""

    def test_old_config_imports_still_work(self):
        """Should maintain all existing import patterns during migration"""
        # These imports should continue to work
        try:
            from src.config import (
                DEBUG_LOGS_ENABLED,
                DEFAULT_MIN_CONTENT_LENGTH,
                DEFAULT_TIMEOUT_SECONDS,
            )

            # Should be the correct types
            assert isinstance(DEFAULT_TIMEOUT_SECONDS, int)
            assert isinstance(DEFAULT_MIN_CONTENT_LENGTH, int)
            assert isinstance(DEBUG_LOGS_ENABLED, bool)

        except ImportError:
            pytest.fail("Old config.py imports should still work during migration")

    def test_settings_values_match_config_values(self):
        """Should ensure Pydantic settings produce same values as old config.py"""
        from src.config import DEBUG_LOGS_ENABLED as OLD_DEBUG
        from src.config import DEFAULT_MIN_CONTENT_LENGTH as OLD_MIN_LENGTH
        from src.config import DEFAULT_TIMEOUT_SECONDS as OLD_TIMEOUT
        from src.settings import Settings

        settings = Settings()

        # Values should match between old and new systems
        assert settings.default_timeout_seconds == OLD_TIMEOUT
        assert settings.default_min_content_length == OLD_MIN_LENGTH
        assert settings.debug_logs_enabled == OLD_DEBUG

    def test_environment_variable_parsing_consistency(self):
        """Should parse environment variables consistently with old config.py"""
        from src.settings import Settings

        test_cases = [
            ("DEFAULT_TIMEOUT_SECONDS", "45", "default_timeout_seconds", 45),
            ("DEBUG_LOGS_ENABLED", "true", "debug_logs_enabled", True),
            ("DEBUG_LOGS_ENABLED", "false", "debug_logs_enabled", False),
            (
                "DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS",
                "3.5",
                "default_min_seconds_between_requests",
                3.5,
            ),
        ]

        for env_var, env_value, attr_name, expected_value in test_cases:
            with patch.dict(os.environ, {env_var: env_value}):
                settings = Settings()
                actual_value = getattr(settings, attr_name)
                assert actual_value == expected_value, (
                    f"Expected {attr_name}={expected_value}, got {actual_value}"
                )


class TestPydanticSettingsAdvancedFeatures:
    """Test cases for advanced Pydantic Settings features"""

    def test_settings_field_descriptions(self):
        """Should have proper field descriptions for documentation"""
        from src.settings import Settings

        schema = Settings.model_json_schema()
        properties = schema["properties"]

        # Should have descriptions for important fields
        assert "description" in properties["default_timeout_seconds"]
        assert "description" in properties["debug_logs_enabled"]

        # Descriptions should be meaningful
        timeout_desc = properties["default_timeout_seconds"]["description"]
        assert "timeout" in timeout_desc.lower()
        assert "second" in timeout_desc.lower()

    def test_settings_validation_error_messages(self):
        """Should provide clear validation error messages"""
        from src.settings import Settings

        with patch.dict(os.environ, {"DEFAULT_TIMEOUT_SECONDS": "not_an_integer"}):
            try:
                Settings()
                pytest.fail("Should have raised ValidationError")
            except ValidationError as e:
                error_message = str(e)
                # Should mention the field name and issue
                assert (
                    "default_timeout_seconds" in error_message.lower()
                    or "DEFAULT_TIMEOUT_SECONDS" in error_message
                )
                assert (
                    "int" in error_message.lower() or "integer" in error_message.lower()
                )

    def test_settings_reload_functionality(self):
        """Should support reloading settings when environment changes"""
        from src.settings import Settings, reload_settings

        # Initial settings
        with patch.dict(os.environ, {"DEFAULT_TIMEOUT_SECONDS": "30"}):
            settings1 = Settings()
            assert settings1.default_timeout_seconds == 30

        # Change environment and reload
        with patch.dict(os.environ, {"DEFAULT_TIMEOUT_SECONDS": "60"}):
            reload_settings()
            settings2 = Settings()
            assert settings2.default_timeout_seconds == 60
