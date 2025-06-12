from enum import Enum
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md


class OutputFormat(Enum):
    """Supported output formats for scraped content."""

    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"


def to_markdown(html: str) -> str:
    """Convert sanitized HTML to Markdown."""
    return md(html)


def to_text(html: str) -> str:
    """Convert sanitized HTML to plain text."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return re.sub(r"\n\s*\n", "\n\n", text).strip()


def to_html(html: str) -> str:
    """Return sanitized HTML as-is."""
    return html


def format_content(html: str, output_format: OutputFormat) -> str:
    """Return content in the desired format."""
    if output_format == OutputFormat.TEXT:
        return to_text(html)
    if output_format == OutputFormat.HTML:
        return to_html(html)
    return to_markdown(html)
