from unittest.mock import patch

from src.scraper.application.contracts.browser_automation import BrowserConfiguration


class TestScrapingConfigurationService:
    """Test suite for ScrapingConfigurationService that manages scraping configuration"""

    def test_get_browser_config_with_defaults(self):
        """Test browser configuration with default randomization"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch.object(service, "_get_user_agent") as mock_get_user_agent:
            with patch(
                "src.scraper.application.services.scraping_configuration_service.random.choice"
            ) as mock_choice:
                # Mock the user agent method to return the expected value
                mock_get_user_agent.return_value = "Mozilla/5.0 Test"

                # Mock the other random choices
                mock_choice.side_effect = [
                    {"width": 1920, "height": 1080},  # viewport
                    "en-US",  # accept_language
                ]

                config = service.get_browser_config(
                    custom_user_agent=None, timeout_seconds=30
                )

                assert isinstance(config, BrowserConfiguration)
                assert config.user_agent == "Mozilla/5.0 Test"
                assert config.viewport == {"width": 1920, "height": 1080}
                assert config.accept_language == "en-US"
                assert config.timeout_seconds == 30

    def test_get_browser_config_with_custom_user_agent(self):
        """Test browser configuration with custom user agent"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch(
            "src.scraper.application.services.scraping_configuration_service.random.choice"
        ) as mock_choice:
            mock_choice.side_effect = [
                {"width": 1366, "height": 768},  # viewport
                "en-GB",  # accept_language
            ]

            config = service.get_browser_config(
                custom_user_agent="Custom User Agent", timeout_seconds=60
            )

            assert config.user_agent == "Custom User Agent"
            assert config.timeout_seconds == 60

    def test_get_browser_config_randomization(self):
        """Test that browser configuration includes proper randomization"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        # Test multiple calls to ensure randomization is working
        configs = []
        for _ in range(3):
            config = service.get_browser_config(timeout_seconds=30)
            configs.append(config)

        # All configs should be valid BrowserConfiguration instances
        for config in configs:
            assert isinstance(config, BrowserConfiguration)
            assert config.user_agent is not None
            assert config.viewport is not None
            assert config.accept_language is not None
            assert config.timeout_seconds == 30

    def test_get_elements_to_remove_default_only(self):
        """Test getting elements to remove with default elements only"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch(
            "src.scraper.application.services.scraping_configuration_service.DEFAULT_ELEMENTS_TO_REMOVE",
            ["script", "style", "nav"],
        ):
            elements = service.get_elements_to_remove(custom_elements=None)

            assert elements == ["script", "style", "nav"]

    def test_get_elements_to_remove_with_custom_elements(self):
        """Test getting elements to remove with custom elements added"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch(
            "src.scraper.application.services.scraping_configuration_service.DEFAULT_ELEMENTS_TO_REMOVE",
            ["script", "style"],
        ):
            elements = service.get_elements_to_remove(custom_elements=["nav", "footer"])

            # Should contain both default and custom elements
            assert "script" in elements
            assert "style" in elements
            assert "nav" in elements
            assert "footer" in elements
            assert len(elements) == 4

    def test_get_elements_to_remove_empty_custom_elements(self):
        """Test getting elements to remove with empty custom elements list"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch(
            "src.scraper.application.services.scraping_configuration_service.DEFAULT_ELEMENTS_TO_REMOVE",
            ["script", "style"],
        ):
            elements = service.get_elements_to_remove(custom_elements=[])

            assert elements == ["script", "style"]

    def test_get_elements_to_remove_does_not_mutate_default(self):
        """Test that getting elements to remove doesn't mutate the default list"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch(
            "src.scraper.application.services.scraping_configuration_service.DEFAULT_ELEMENTS_TO_REMOVE",
            ["script", "style"],
        ) as mock_default:
            elements = service.get_elements_to_remove(custom_elements=["nav"])

            # Original default should be unchanged
            assert mock_default == ["script", "style"]
            # Returned list should have both
            assert "script" in elements
            assert "nav" in elements

    def test_get_timeout_with_custom_value(self):
        """Test timeout configuration with custom value"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        timeout = service.get_timeout(custom_timeout=45)

        assert timeout == 45

    def test_get_timeout_with_none_uses_default(self):
        """Test timeout configuration with None uses default"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch(
            "src.scraper.application.services.scraping_configuration_service.DEFAULT_TIMEOUT_SECONDS",
            30,
        ):
            timeout = service.get_timeout(custom_timeout=None)

            assert timeout == 30

    def test_get_scraping_config(self):
        """Test comprehensive scraping configuration generation"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        with patch.object(service, "get_browser_config") as mock_browser_config:
            with patch.object(service, "get_elements_to_remove") as mock_elements:
                with patch.object(service, "get_timeout") as mock_timeout:
                    # Setup mocks
                    mock_browser_config.return_value = BrowserConfiguration(
                        user_agent="Test Agent",
                        viewport={"width": 1920, "height": 1080},
                        accept_language="en-US",
                        timeout_seconds=30,
                    )
                    mock_elements.return_value = ["script", "style", "nav"]
                    mock_timeout.return_value = 30

                    config = service.get_scraping_config(
                        custom_user_agent="Test Agent",
                        custom_timeout=30,
                        custom_elements_to_remove=["nav"],
                    )

                    # Verify all methods were called with correct parameters
                    mock_browser_config.assert_called_once_with(
                        custom_user_agent="Test Agent", timeout_seconds=30
                    )
                    mock_elements.assert_called_once_with(custom_elements=["nav"])
                    mock_timeout.assert_called_once_with(custom_timeout=30)

                    # Verify config structure
                    assert "browser_config" in config
                    assert "elements_to_remove" in config
                    assert "timeout_seconds" in config

    def test_get_grace_period_default(self):
        """Test grace period configuration with default value"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        grace_period = service.get_grace_period()

        # Should return default grace period (typically 2.0 seconds)
        assert isinstance(grace_period, (int, float))
        assert grace_period > 0

    def test_get_grace_period_custom(self):
        """Test grace period configuration with custom value"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        grace_period = service.get_grace_period(custom_grace_period=5.0)

        assert grace_period == 5.0

    def test_validate_url_valid_http(self):
        """Test URL validation with valid HTTP URL"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        is_valid, error = service.validate_url("http://example.com")

        assert is_valid is True
        assert error is None

    def test_validate_url_valid_https(self):
        """Test URL validation with valid HTTPS URL"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        is_valid, error = service.validate_url("https://example.com/path?query=value")

        assert is_valid is True
        assert error is None

    def test_validate_url_invalid_format(self):
        """Test URL validation with invalid URL format"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        is_valid, error = service.validate_url("not-a-valid-url")

        assert is_valid is False
        assert error is not None
        assert "invalid" in error.lower()

    def test_validate_url_empty_string(self):
        """Test URL validation with empty string"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        is_valid, error = service.validate_url("")

        assert is_valid is False
        assert error is not None

    def test_validate_url_none(self):
        """Test URL validation with None"""
        from src.scraper.application.services.scraping_configuration_service import (
            ScrapingConfigurationService,
        )

        service = ScrapingConfigurationService()

        is_valid, error = service.validate_url(None)

        assert is_valid is False
        assert error is not None
