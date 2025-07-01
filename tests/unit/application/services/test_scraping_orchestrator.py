from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_scraping_orchestrator_scrape_success():
    """
    Tests the happy path of the scrape method on the orchestrator.
    It should call its dependencies in the correct order and return a successful result.
    """
    from src.scraper.application.services.scraping_orchestrator import (
        ScrapingOrchestrator,
    )

    # Arrange: Create mocks for all dependencies
    mock_url_validator = MagicMock()
    mock_url_validator.validate.return_value = True
    mock_url_validator.normalize.return_value = "https://example.com"

    mock_content_extractor = AsyncMock()
    mock_content_extractor.extract.return_value = MagicMock(
        title="Example Title", content="Example Content", error=None
    )

    mock_output_formatter = MagicMock()
    mock_output_formatter.format_and_truncate.return_value = "Formatted Content"

    # Act: Initialize the orchestrator with mocked dependencies
    orchestrator = ScrapingOrchestrator(
        url_validator=mock_url_validator,
        content_extractor=mock_content_extractor,
        output_formatter=mock_output_formatter,
    )
    result = await orchestrator.scrape("https://example.com")

    # Assert: Verify the result and that all mocks were called correctly
    assert result["error"] is None
    assert result["title"] == "Example Title"
    assert result["content"] == "Formatted Content"
    mock_url_validator.validate.assert_called_once_with("https://example.com")
    mock_content_extractor.extract.assert_awaited_once()
    mock_output_formatter.format_and_truncate.assert_called_once()


def test_scraping_orchestrator_initialization():
    """
    Tests that the ScrapingOrchestrator can be initialized.
    This is the first, most basic test to confirm the class exists.
    """
    from src.scraper.application.services.scraping_orchestrator import (
        ScrapingOrchestrator,
    )

    # We will add mock dependencies later. For now, just check instantiation.
    orchestrator = ScrapingOrchestrator(
        url_validator=MagicMock(),
        content_extractor=AsyncMock(),
        output_formatter=MagicMock(),
    )
    assert orchestrator is not None
