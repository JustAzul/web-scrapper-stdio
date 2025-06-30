"""
TDD Tests for T011 - WebScrapingService.scrape_url Refactoring
Tests for breaking down method with 10 parameters into specialized classes following SRP
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.output_format_handler import OutputFormat


class TestScrapingRequest:
    """TDD Tests for ScrapingRequest parameter object"""

    def test_scraping_request_creation_with_minimal_params(self):
        """Test creating ScrapingRequest with only required parameters"""
        # This test will fail initially (RED phase)
        from src.scraper.application.services.scraping_request import ScrapingRequest

        request = ScrapingRequest(url="https://example.com")

        assert request.url == "https://example.com"
        assert request.timeout_seconds is None
        assert request.custom_elements_to_remove is None
        assert request.grace_period_seconds == 2.0  # Default value
        assert request.max_length is None
        assert request.user_agent is None
        assert request.wait_for_network_idle is True  # Default value
        assert request.output_format == OutputFormat.MARKDOWN  # Default value
        assert request.click_selector is None

    def test_scraping_request_creation_with_all_params(self):
        """Test creating ScrapingRequest with all parameters"""
        from src.scraper.application.services.scraping_request import ScrapingRequest

        request = ScrapingRequest(
            url="https://example.com",
            timeout_seconds=30,
            custom_elements_to_remove=["script", "style"],
            grace_period_seconds=5.0,
            max_length=1000,
            user_agent="Custom Agent",
            wait_for_network_idle=False,
            output_format=OutputFormat.TEXT,
            click_selector=".button",
        )

        assert request.url == "https://example.com"
        assert request.timeout_seconds == 30
        assert request.custom_elements_to_remove == ["script", "style"]
        assert request.grace_period_seconds == 5.0
        assert request.max_length == 1000
        assert request.user_agent == "Custom Agent"
        assert request.wait_for_network_idle is False
        assert request.output_format == OutputFormat.TEXT
        assert request.click_selector == ".button"

    def test_scraping_request_validation(self):
        """Test ScrapingRequest validates parameters"""
        from src.scraper.application.services.scraping_request import ScrapingRequest

        # Should validate URL is required
        with pytest.raises(ValueError, match="URL is required"):
            ScrapingRequest(url="")

        # Should validate timeout is positive
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ScrapingRequest(url="https://example.com", timeout_seconds=-1)

        # Should validate grace period is positive
        with pytest.raises(ValueError, match="grace_period_seconds must be positive"):
            ScrapingRequest(url="https://example.com", grace_period_seconds=-1.0)

        # Should validate max_length is positive
        with pytest.raises(ValueError, match="max_length must be positive"):
            ScrapingRequest(url="https://example.com", max_length=-100)

    def test_scraping_request_backward_compatibility(self):
        """Test ScrapingRequest maintains backward compatibility with old parameters"""
        from src.scraper.application.services.scraping_request import ScrapingRequest

        # Should handle custom_timeout parameter for backward compatibility
        request = ScrapingRequest(url="https://example.com", custom_timeout=45)
        assert request.timeout_seconds == 45

        # Should prioritize timeout_seconds over custom_timeout
        request = ScrapingRequest(
            url="https://example.com", timeout_seconds=30, custom_timeout=45
        )
        assert request.timeout_seconds == 30


class TestNavigationHandler:
    """TDD Tests for NavigationHandler - Single responsibility: URL navigation"""

    def test_navigation_handler_creation(self):
        """Test creating NavigationHandler with dependencies"""
        # This test will fail initially (RED phase)
        from src.scraper.application.services.navigation_handler import (
            NavigationHandler,
        )

        mock_browser_factory = Mock()
        mock_config_service = Mock()

        handler = NavigationHandler(
            browser_factory=mock_browser_factory,
            configuration_service=mock_config_service,
        )

        assert handler.browser_factory == mock_browser_factory
        assert handler.configuration_service == mock_config_service

    @pytest.mark.asyncio
    async def test_navigation_handler_navigate_success(self):
        """Test successful navigation handling"""
        from src.scraper.application.services.navigation_handler import (
            NavigationHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        # Setup mocks
        mock_browser_factory = Mock()
        mock_config_service = Mock()
        mock_browser = AsyncMock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.url = "https://example.com"
        mock_response.error = None

        mock_browser.navigate_to_url.return_value = mock_response
        mock_browser_factory.create_browser = AsyncMock(return_value=mock_browser)
        mock_config_service.get_browser_config.return_value = Mock(timeout_seconds=30)

        handler = NavigationHandler(
            browser_factory=mock_browser_factory,
            configuration_service=mock_config_service,
        )

        request = ScrapingRequest(url="https://example.com")

        # Execute navigation
        result = await handler.navigate(request)

        # Verify result
        assert result.success is True
        assert result.final_url == "https://example.com"
        assert result.browser_automation == mock_browser
        assert result.error is None

        # Verify calls
        mock_browser_factory.create_browser.assert_called_once()
        mock_browser.navigate_to_url.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_navigation_handler_navigate_failure(self):
        """Test failed navigation handling"""
        from src.scraper.application.services.navigation_handler import (
            NavigationHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        # Setup mocks for failure
        mock_browser_factory = Mock()
        mock_config_service = Mock()
        mock_browser = AsyncMock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "Connection failed"

        mock_browser.navigate_to_url.return_value = mock_response
        mock_browser_factory.create_browser = AsyncMock(return_value=mock_browser)
        mock_config_service.get_browser_config.return_value = Mock(timeout_seconds=30)

        handler = NavigationHandler(
            browser_factory=mock_browser_factory,
            configuration_service=mock_config_service,
        )

        request = ScrapingRequest(url="https://example.com")

        # Execute navigation
        result = await handler.navigate(request)

        # Verify result
        assert result.success is False
        assert result.error == "Connection failed"
        assert result.browser_automation == mock_browser


class TestContentStabilizationHandler:
    """TDD Tests for ContentStabilizationHandler - Single responsibility: Content stabilization"""

    def test_content_stabilization_handler_creation(self):
        """Test creating ContentStabilizationHandler"""
        # This test will fail initially (RED phase)
        from src.scraper.application.services.content_stabilization_handler import (
            ContentStabilizationHandler,
        )

        handler = ContentStabilizationHandler()
        assert handler is not None

    @pytest.mark.asyncio
    async def test_content_stabilization_success(self):
        """Test successful content stabilization"""
        from src.scraper.application.services.content_stabilization_handler import (
            ContentStabilizationHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_browser = AsyncMock()
        mock_browser.wait_for_content_stabilization.return_value = True

        handler = ContentStabilizationHandler()
        request = ScrapingRequest(url="https://example.com")

        result = await handler.stabilize_content(
            mock_browser, request, timeout_seconds=30
        )

        assert result.success is True
        assert result.error is None
        mock_browser.wait_for_content_stabilization.assert_called_once_with(30)

    @pytest.mark.asyncio
    async def test_content_stabilization_timeout(self):
        """Test content stabilization timeout"""
        from src.scraper.application.services.content_stabilization_handler import (
            ContentStabilizationHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_browser = AsyncMock()
        mock_browser.wait_for_content_stabilization.return_value = False

        handler = ContentStabilizationHandler()
        request = ScrapingRequest(url="https://example.com")

        result = await handler.stabilize_content(
            mock_browser, request, timeout_seconds=30
        )

        assert result.success is False
        assert "Content did not stabilize within timeout" in result.error


class TestInteractionHandler:
    """TDD Tests for InteractionHandler - Single responsibility: Element interactions"""

    def test_interaction_handler_creation(self):
        """Test creating InteractionHandler"""
        # This test will fail initially (RED phase)
        from src.scraper.application.services.interaction_handler import (
            InteractionHandler,
        )

        handler = InteractionHandler()
        assert handler is not None

    @pytest.mark.asyncio
    async def test_interaction_handler_click_success(self):
        """Test successful element clicking"""
        from src.scraper.application.services.interaction_handler import (
            InteractionHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_browser = AsyncMock()
        mock_browser.click_element.return_value = True

        handler = InteractionHandler()
        request = ScrapingRequest(url="https://example.com", click_selector=".button")

        result = await handler.handle_interactions(mock_browser, request)

        assert result.success is True
        assert result.error is None
        mock_browser.click_element.assert_called_once_with(".button")

    @pytest.mark.asyncio
    async def test_interaction_handler_no_selector(self):
        """Test interaction handler when no selector provided"""
        from src.scraper.application.services.interaction_handler import (
            InteractionHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_browser = AsyncMock()

        handler = InteractionHandler()
        request = ScrapingRequest(url="https://example.com")  # No click_selector

        result = await handler.handle_interactions(mock_browser, request)

        assert result.success is True
        assert result.error is None
        mock_browser.click_element.assert_not_called()

    @pytest.mark.asyncio
    async def test_interaction_handler_click_failure(self):
        """Test failed element clicking"""
        from src.scraper.application.services.interaction_handler import (
            InteractionHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_browser = AsyncMock()
        mock_browser.click_element.return_value = False

        handler = InteractionHandler()
        request = ScrapingRequest(url="https://example.com", click_selector=".button")

        result = await handler.handle_interactions(mock_browser, request)

        assert result.success is True  # Non-critical failure
        assert "Could not click selector" in result.error


class TestContentExtractionHandler:
    """TDD Tests for ContentExtractionHandler - Single responsibility: Content extraction"""

    def test_content_extraction_handler_creation(self):
        """Test creating ContentExtractionHandler"""
        # This test will fail initially (RED phase)
        from src.scraper.application.services.content_extraction_handler import (
            ContentExtractionHandler,
        )

        mock_content_processor = Mock()

        handler = ContentExtractionHandler(content_processor=mock_content_processor)
        assert handler.content_processor == mock_content_processor

    @pytest.mark.asyncio
    async def test_content_extraction_success(self):
        """Test successful content extraction"""
        from src.scraper.application.services.content_extraction_handler import (
            ContentExtractionHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_content_processor = Mock()
        mock_content_processor.process_html_content.return_value = (
            "Test Title",
            "<p>Clean HTML</p>",
            "Clean text",
            None,
        )
        mock_content_processor.get_min_content_length.return_value = 10
        mock_content_processor.validate_content_length.return_value = True
        mock_content_processor.format_content.return_value = "Formatted content"

        mock_browser = AsyncMock()
        mock_browser.get_page_content.return_value = "<html>Raw HTML</html>"

        handler = ContentExtractionHandler(content_processor=mock_content_processor)
        request = ScrapingRequest(url="https://example.com")

        result = await handler.extract_content(
            mock_browser, request, "https://example.com", []
        )

        assert result.success is True
        assert result.title == "Test Title"
        assert result.content == "Formatted content"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_content_extraction_cloudflare_block(self):
        """Test content extraction with Cloudflare block detection"""
        from src.scraper.application.services.content_extraction_handler import (
            ContentExtractionHandler,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_content_processor = Mock()
        mock_browser = AsyncMock()
        # Cloudflare challenge HTML
        mock_browser.get_page_content.return_value = (
            "<html><title>Attention Required! | Cloudflare</title></html>"
        )

        handler = ContentExtractionHandler(content_processor=mock_content_processor)
        request = ScrapingRequest(url="https://example.com")

        result = await handler.extract_content(
            mock_browser, request, "https://example.com", []
        )

        assert result.success is False
        assert "Cloudflare" in result.error


class TestRefactoredWebScrapingService:
    """TDD Tests for the refactored WebScrapingService using specialized handlers"""

    def test_refactored_service_creation(self):
        """Test creating refactored WebScrapingService with specialized handlers"""
        # This test will fail initially (RED phase)
        from src.scraper.application.services.refactored_web_scraping_service import (
            RefactoredWebScrapingService,
        )

        mock_navigation_handler = Mock()
        mock_stabilization_handler = Mock()
        mock_interaction_handler = Mock()
        mock_extraction_handler = Mock()

        service = RefactoredWebScrapingService(
            navigation_handler=mock_navigation_handler,
            stabilization_handler=mock_stabilization_handler,
            interaction_handler=mock_interaction_handler,
            extraction_handler=mock_extraction_handler,
        )

        assert service.navigation_handler == mock_navigation_handler
        assert service.stabilization_handler == mock_stabilization_handler
        assert service.interaction_handler == mock_interaction_handler
        assert service.extraction_handler == mock_extraction_handler

    @pytest.mark.asyncio
    async def test_refactored_service_scrape_success(self):
        """Test successful scraping with refactored service"""
        from src.scraper.application.services.refactored_web_scraping_service import (
            RefactoredWebScrapingService,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        # Setup mocks for successful flow
        mock_navigation_handler = AsyncMock()
        mock_stabilization_handler = AsyncMock()
        mock_interaction_handler = AsyncMock()
        mock_extraction_handler = AsyncMock()

        # Mock successful navigation
        nav_result = Mock()
        nav_result.success = True
        nav_result.final_url = "https://example.com"
        nav_result.browser_automation = Mock()
        nav_result.error = None
        mock_navigation_handler.navigate.return_value = nav_result

        # Mock successful stabilization
        stab_result = Mock()
        stab_result.success = True
        stab_result.error = None
        mock_stabilization_handler.stabilize_content.return_value = stab_result

        # Mock successful interaction
        int_result = Mock()
        int_result.success = True
        int_result.error = None
        mock_interaction_handler.handle_interactions.return_value = int_result

        # Mock successful extraction
        ext_result = Mock()
        ext_result.success = True
        ext_result.title = "Test Title"
        ext_result.content = "Test Content"
        ext_result.error = None
        mock_extraction_handler.extract_content.return_value = ext_result

        service = RefactoredWebScrapingService(
            navigation_handler=mock_navigation_handler,
            stabilization_handler=mock_stabilization_handler,
            interaction_handler=mock_interaction_handler,
            extraction_handler=mock_extraction_handler,
        )

        request = ScrapingRequest(url="https://example.com")

        result = await service.scrape_url(request)

        # Verify result
        assert result["title"] == "Test Title"
        assert result["final_url"] == "https://example.com"
        assert result["content"] == "Test Content"
        assert result["error"] is None

        # Verify handler calls
        mock_navigation_handler.navigate.assert_called_once_with(request)
        mock_stabilization_handler.stabilize_content.assert_called_once()
        mock_interaction_handler.handle_interactions.assert_called_once()
        mock_extraction_handler.extract_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_refactored_service_navigation_failure(self):
        """Test scraping with navigation failure"""
        from src.scraper.application.services.refactored_web_scraping_service import (
            RefactoredWebScrapingService,
        )
        from src.scraper.application.services.scraping_request import ScrapingRequest

        mock_navigation_handler = AsyncMock()
        mock_stabilization_handler = AsyncMock()
        mock_interaction_handler = AsyncMock()
        mock_extraction_handler = AsyncMock()

        # Mock failed navigation
        nav_result = Mock()
        nav_result.success = False
        nav_result.error = "Connection failed"
        nav_result.browser_automation = Mock()
        mock_navigation_handler.navigate.return_value = nav_result

        service = RefactoredWebScrapingService(
            navigation_handler=mock_navigation_handler,
            stabilization_handler=mock_stabilization_handler,
            interaction_handler=mock_interaction_handler,
            extraction_handler=mock_extraction_handler,
        )

        request = ScrapingRequest(url="https://example.com")

        result = await service.scrape_url(request)

        # Verify result
        assert result["title"] is None
        assert result["final_url"] == "https://example.com"
        assert result["content"] is None
        assert result["error"] == "Connection failed"

        # Verify only navigation was called
        mock_navigation_handler.navigate.assert_called_once_with(request)
        mock_stabilization_handler.stabilize_content.assert_not_called()
        mock_interaction_handler.handle_interactions.assert_not_called()
        mock_extraction_handler.extract_content.assert_not_called()


class TestBackwardCompatibility:
    """TDD Tests to ensure backward compatibility with existing WebScrapingService interface"""

    @pytest.mark.asyncio
    async def test_original_service_interface_maintained(self):
        """Test that original WebScrapingService interface is maintained"""
        from src.scraper.application.services.web_scraping_service import (
            WebScrapingService,
        )

        # Should still accept the old parameter format
        mock_browser_factory = Mock()
        mock_content_processor = Mock()
        mock_config_service = Mock()

        service = WebScrapingService(
            browser_factory=mock_browser_factory,
            content_processor=mock_content_processor,
            configuration_service=mock_config_service,
        )

        # Should still have the scrape_url method with same signature
        assert hasattr(service, "scrape_url")
        # Verify it accepts the old parameters (we'll test the actual call separately)

    @pytest.mark.asyncio
    async def test_parameter_object_integration(self):
        """Test that WebScrapingService can use ScrapingRequest internally"""
        from src.scraper.application.services.scraping_request import ScrapingRequest

        # Should be able to create ScrapingRequest from old parameters
        request = ScrapingRequest.from_legacy_parameters(
            url="https://example.com",
            timeout_seconds=30,
            custom_elements_to_remove=["script"],
            custom_timeout=None,
            grace_period_seconds=2.0,
            max_length=1000,
            user_agent="Custom Agent",
            wait_for_network_idle=True,
            output_format=OutputFormat.MARKDOWN,
            click_selector=".button",
        )

        assert request.url == "https://example.com"
        assert request.timeout_seconds == 30
        assert request.custom_elements_to_remove == ["script"]
