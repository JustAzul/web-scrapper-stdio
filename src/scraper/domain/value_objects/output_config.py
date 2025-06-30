"""
OutputConfig - Single Responsibility: Output formatting configuration

Extracted from ScrapingConfig to follow SRP principle.
This class is responsible only for output-related configuration.
"""

from dataclasses import dataclass
from typing import Optional

from src.output_format_handler import OutputFormat


@dataclass(frozen=True)
class OutputConfig:
    """
    Configuration for output formatting.

    Single Responsibility: Handles all output-related configuration and validation.
    """

    format: OutputFormat = OutputFormat.MARKDOWN
    max_length: Optional[int] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate max_length
        if self.max_length is not None and self.max_length <= 0:
            raise ValueError("max_length must be positive")

    @property
    def is_text_format(self) -> bool:
        """Check if output format is text."""
        return self.format == OutputFormat.TEXT

    @property
    def is_markdown_format(self) -> bool:
        """Check if output format is markdown."""
        return self.format == OutputFormat.MARKDOWN

    @property
    def is_html_format(self) -> bool:
        """Check if output format is HTML."""
        return self.format == OutputFormat.HTML

    @property
    def has_length_limit(self) -> bool:
        """Check if there is a length limit."""
        return self.max_length is not None

    def should_truncate(self, content_length: int) -> bool:
        """Check if content should be truncated."""
        return self.has_length_limit and content_length > self.max_length

    def truncate_content(self, content: str) -> str:
        """Truncate content if needed."""
        if not self.should_truncate(len(content)):
            return content

        truncated = content[: self.max_length]
        return truncated + "..." if len(content) > self.max_length else truncated

    def with_format(self, format_type: OutputFormat) -> "OutputConfig":
        """Create new OutputConfig with different format."""
        return OutputConfig(format=format_type, max_length=self.max_length)

    def with_max_length(self, max_length: Optional[int]) -> "OutputConfig":
        """Create new OutputConfig with different max length."""
        return OutputConfig(format=self.format, max_length=max_length)

    def __str__(self) -> str:
        """String representation."""
        length_str = f", max_length={self.max_length}" if self.max_length else ""
        return f"OutputConfig(format={self.format.value}{length_str})"
