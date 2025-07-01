"""
ContentExtractionHandler - Single Responsibility: Content Extraction

Handles the content extraction responsibility extracted from WebScrapingService.scrape_url
following the Single Responsibility Principle.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional

from src.logger import Logger
from src.scraper.application.services.content_processing_service import (
    ContentProcessingService,
)
from src.scraper.application.services.scraping_request import ScrapingRequest
from src.scraper.infrastructure.external.errors import _handle_cloudflare_block


@dataclass
class ExtractionResult:
    """Dataclass for extraction results."""

    success: bool
    title: Optional[str]
    content: Optional[str]
    error: Optional[str] = None


class ContentExtractionHandler:
    """Single Responsibility: Content Extraction"""

    def __init__(
        self,
        content_processor: ContentProcessingService,
        logger: Optional[Logger] = None,
    ):
        """Initialize content extraction handler with dependencies."""
        self.content_processor = content_processor
        self.logger = logger or Logger(__name__)

    async def extract_and_process_content(
        self,
        browser_automation: Any,  # Replace Any with BrowserAutomationInterface
        request: ScrapingRequest,
        final_url: str,
        elements_to_remove: List[str],
    ) -> ExtractionResult:
        """Extract and process content from the web page."""
        try:
            self.logger.debug(f"Extracting content from: {final_url}")
            await asyncio.sleep(request.grace_period_seconds)
            html_content = await browser_automation.get_page_content()

            is_blocked, cf_error = _handle_cloudflare_block(html_content, final_url)
            if is_blocked:
                return ExtractionResult(
                    success=False, title=None, content=None, error=cf_error
                )

            page_title, clean_html, text_content, content_error = (
                self.content_processor.process_html_content(
                    html_content, elements_to_remove, final_url
                )
            )
            if content_error:
                return ExtractionResult(
                    success=False, title=None, content=None, error=content_error
                )

            min_len = self.content_processor.get_min_content_length(final_url)
            if not self.content_processor.validate_content_length(
                text_content, min_len, final_url
            ):
                error_msg = f"[ERROR] No significant text content extracted (too short, less than {min_len} characters)."
                return ExtractionResult(
                    success=False, title=page_title, content=None, error=error_msg
                )

            formatted_content = self.content_processor.format_content(
                title=page_title,
                html_content=clean_html,
                text_content=text_content,
                output_format=request.output_format,
                max_length=request.max_length,
            )

            self.logger.debug(f"Successfully extracted text from {final_url}")
            return ExtractionResult(
                success=True, title=page_title, content=formatted_content, error=None
            )

        except Exception as e:
            error_msg = f"[ERROR] Unexpected error during content extraction: {str(e)}"
            self.logger.warning(
                f"Unexpected error during content extraction from {final_url}: {e}"
            )
            return ExtractionResult(
                success=False, title=None, content=None, error=error_msg
            )
