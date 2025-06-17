from enum import Enum
from bs4 import BeautifulSoup
from markdownify import markdownify as md

TRUNCATION_NOTICE = "\n\n[Content truncated due to length]"


class OutputFormat(Enum):
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"


def to_markdown(html: str) -> str:
    return md(html)


def to_text(html: str = None, soup: BeautifulSoup = None) -> str:
    if soup is None:
        soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def to_html(html: str = None, soup: BeautifulSoup = None) -> str:
    if soup is None:
        soup = BeautifulSoup(html, "html.parser")
    return str(soup)


def format_content(html: str, output_format: OutputFormat, soup: BeautifulSoup = None) -> str:
    if output_format is OutputFormat.TEXT:
        return to_text(html, soup)
    if output_format is OutputFormat.HTML:
        return to_html(html, soup)
    return to_markdown(html)


def truncate_html(html: str = None, max_length: int = None, soup: BeautifulSoup = None) -> str:
    if html is not None and len(html) <= max_length:
        return html
    if soup is None:
        soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    truncated = text[:max_length]
    return truncated + TRUNCATION_NOTICE


def truncate_content(content: str, max_length: int) -> str:
    if content is None or max_length is None:
        return content
    if len(content) > max_length:
        return content[:max_length] + TRUNCATION_NOTICE
    return content
