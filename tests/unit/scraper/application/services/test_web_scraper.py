import pytest
from unittest.mock import AsyncMock, MagicMock
from src.scraper.application.services.web_scraper import RefactoredWebScrapingService

@pytest.mark.asyncio
async def test_scrape_success():
    navigation_handler = AsyncMock()
    stabilization_handler = AsyncMock()
    interaction_handler = AsyncMock()
    extraction_handler = AsyncMock()

    # Setup navigation handler to succeed
    navigation_handler.navigate.return_value = MagicMock(
        success=True, browser_automation=MagicMock(), final_url="http://example.com", error=None
    )
    # Setup stabilization handler to succeed
    stabilization_handler.stabilize_content.return_value = MagicMock(success=True, error=None)
    # Setup interaction handler to succeed
    interaction_handler.handle_interactions.return_value = MagicMock(error=None)
    # Setup extraction handler to succeed
    extraction_handler.extract_and_process_content.return_value = MagicMock(
        success=True, title="Title", content="Content", error=None
    )

    service = RefactoredWebScrapingService(
        navigation_handler, stabilization_handler, interaction_handler, extraction_handler
    )

    request = MagicMock()
    request.url = "http://example.com"
    request.get_effective_timeout.return_value = 5
    request.get_elements_to_remove.return_value = []

    result = await service.scrape(request)
    assert result["error"] is None
    assert result["content"] == "Content"
    assert result["title"] == "Title"
