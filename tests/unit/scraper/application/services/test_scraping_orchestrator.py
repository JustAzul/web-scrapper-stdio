import pytest
from unittest.mock import MagicMock
from src.scraper.application.services.scraping_orchestrator import ScrapingOrchestrator

def test_orchestrate_calls_dependencies():
    url_validator = MagicMock()
    content_extractor = MagicMock()
    output_formatter = MagicMock()
    orchestrator = ScrapingOrchestrator(url_validator, content_extractor, output_formatter)
    orchestrator.orchestrate = MagicMock(return_value="Orchestrated")
    result = orchestrator.orchestrate("http://example.com")
    assert "Orchestrated" in result
    orchestrator.orchestrate.assert_called_once()
