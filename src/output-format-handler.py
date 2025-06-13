from enum import Enum
import re
from bs4 import BeautifulSoup, NavigableString, Tag
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


def truncate_html(html: str, max_length: int) -> str:
    """Safely truncate HTML while preserving valid markup."""
    soup = BeautifulSoup(html, "html.parser")
    length = 0

    def _truncate(node: Tag):
        nonlocal length
        for child in list(node.children):
            if isinstance(child, NavigableString):
                if length >= max_length:
                    child.extract()
                    continue
                remaining = max_length - length
                if len(child) > remaining:
                    child.replace_with(child[:remaining])
                    length = max_length
                    for sibling in list(child.next_siblings):
                        sibling.extract()
                    break
                else:
                    length += len(child)
            elif isinstance(child, Tag):
                _truncate(child)
                if length >= max_length:
                    for sibling in list(child.next_siblings):
                        sibling.extract()
                    break

    _truncate(soup)
    return str(soup)


def truncate_content(content: str, max_length: int | None, output_format: OutputFormat) -> str:
    """Truncate formatted content respecting the output format."""
    if max_length is None:
        return content
    if output_format == OutputFormat.HTML:
        return truncate_html(content, max_length)
    return content[:max_length]
