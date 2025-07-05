"""
Data models for the web scraper application.

This module contains Pydantic models used throughout the application.
"""

from typing import Any, Dict, Optional

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from src.core.constants import MAX_GRACE_PERIOD_VALIDATION, MAX_TIMEOUT_VALIDATION
from src.output_format_handler import OutputFormat
from src.settings import DEFAULT_TIMEOUT_SECONDS, get_settings


class ScrapeArgs(BaseModel):
    """Parameters for web scraping."""

    url: HttpUrl = Field(description="URL to scrape")

    @field_validator("url", mode="before")
    def check_for_malicious_patterns(cls, v: Any):
        """
        Validate that the URL does not contain common malicious characters
        or patterns that could be used for injection or traversal attacks.
        This runs BEFORE Pydantic's own URL parsing.
        """
        if not isinstance(v, str):
            return v  # Let Pydantic handle non-string types

        malicious_chars = ["<", ">", '"', "'", "{", "}"]
        if any(char in v for char in malicious_chars):
            raise ValueError(f"URL contains prohibited characters: {malicious_chars}")

        # Basic path traversal check
        if "../" in v or "..\\" in v:
            raise ValueError("URL contains path traversal characters ('../')")

        return v

    @model_validator(mode="after")
    def check_url_not_local(cls, values: "ScrapeArgs") -> "ScrapeArgs":
        """
        Ensures the URL is not pointing to a local development environment.
        This is a secondary check against potential SSRF vulnerabilities.
        This check is skipped if ALLOW_LOCALHOST is True in the settings.
        """
        settings = get_settings()
        if settings.allow_localhost:
            return values

        url_str = str(values.url)
        if "localhost" in url_str or "127.0.0.1" in url_str:
            raise ValueError("URL cannot be localhost or a local IP address.")
        return values

    max_length: Optional[int | float] = Field(
        default=None,
        description="Maximum number of characters to return. If None, unlimited.",
        gt=0,
    )
    grace_period_seconds: float = Field(
        default=2.0,
        description="Short grace period to allow JS to finish rendering (in seconds)",
        gt=0,
        lt=MAX_GRACE_PERIOD_VALIDATION,
    )
    timeout_seconds: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        description="Maximum time to wait for page load (in seconds)",
        gt=0,
        lt=MAX_TIMEOUT_VALIDATION,
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="Custom User-Agent string to use. If not provided, a random one will be selected.",
    )
    include_links: bool = Field(
        default=True,
        description="Whether to include links in the extracted content",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Format for the output content",
    )
    custom_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom HTTP headers to include in the request",
    )
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector to extract specific content from the page",
    )
    custom_elements_to_remove: Optional[list[str]] = Field(
        default=None,
        description=(
            "Additional HTML elements (CSS selectors) to remove before extraction."
        ),
    )
