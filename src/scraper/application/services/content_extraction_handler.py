"""
ContentExtractionHandler - Single Responsibility: Content Extraction

Handles the content extraction responsibility extracted from WebScrapingService.scrape_url
following the Single Responsibility Principle.
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional

from src.scraper.infrastructure.external.errors import _handle_cloudflare_block
from src.scraper.application.services.content_processing_service import ContentProcessingService

logger = Logger(__name__)
class ExtractionResult:


    - Process HTML content

    def __init__(self, content_processor: ContentProcessingService):
        Initialize content extraction handler with dependencies.

        """
        self.content_processor = content_processor
        self,
        browser_automation: object,
        final_url: str,
        elements_to_remove: List[str],
        """
        Extract and process content from the web page.

            browser_automation: Browser automation instance
            request: Scraping request containing configuration
            final_url: Final URL after navigation and redirects
            elements_to_remove: List of HTML elements to remove during processing

        Returns:
        """
        try:
            # Wait grace period and get content
            logger.debug(f"Extracting content from: {final_url}")
            await asyncio.sleep(request.grace_period_seconds)
            html_content = await browser_automation.get_page_content()

            # Check for Cloudflare blocks
            is_blocked, cf_error = _handle_cloudflare_block(html_content, final_url)
            if is_blocked:
                return ExtractionResult(
                    success=False, title=None, content=None, error=cf_error
                )

            # Process HTML content
            page_title, clean_html, text_content, content_error = (
                self.content_processor.process_html_content(
                    html_content, elements_to_remove, final_url
                )
            )
            if content_error:
                return ExtractionResult(
                    success=False, title=None, content=None, error=content_error
                )

            # Validate content length
            min_content_length = self.content_processor.get_min_content_length(
                final_url
            )
            if not self.content_processor.validate_content_length(
                text_content, min_content_length, final_url
            ):
                return ExtractionResult(
                    success=False,
                    title=page_title,
                    content=None,
                    error=f"[ERROR] No significant text content extracted (too short, less than {min_content_length} characters).",
                )

            # Format content
            formatted_content = self.content_processor.format_content(
                title=page_title,
                html_content=clean_html,
                text_content=text_content,
                output_format=request.output_format,
                max_length=request.max_length,
            )

            logger.debug(f"Successfully extracted text from {final_url}")

            return ExtractionResult(
                success=True, title=page_title, content=formatted_content, error=None
            )

        except Exception as e:
            error_msg = f"[ERROR] Unexpected error during content extraction: {str(e)}"
            logger.warning(
                f"Unexpected error during content extraction from {final_url}: {e}"
            )
            return ExtractionResult(
                success=False, title=None, content=None, error=error_msg
            )
