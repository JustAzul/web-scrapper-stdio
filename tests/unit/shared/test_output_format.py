import pytest
from bs4 import BeautifulSoup

from src.output_format_handler import (
    OutputFormat,
    format_content,
    to_html,
    to_markdown,
    to_text,
    truncate_content,
    truncate_html,
)

HTML_SNIPPET = """
<html><body><h1>Title</h1><p>Hello <b>world</b>!</p></body></html>
"""


@pytest.mark.parametrize(
    "fmt,expected_fn",
    [
        (OutputFormat.MARKDOWN, to_markdown),
        (OutputFormat.TEXT, to_text),
        (OutputFormat.HTML, to_html),
    ],
)
def test_format_content_dispatch(fmt, expected_fn):
    """format_content should delegate to the correct helper based on enum."""
    result = format_content(HTML_SNIPPET, fmt)
    # Compute expected directly for comparison
    expected = expected_fn(HTML_SNIPPET)
    assert result == expected


@pytest.mark.parametrize("length", [None, 5, 1000])
def test_truncate_content_boundaries(length):
    content = "Hello world!"
    truncated = truncate_content(content, length)
    if length is None or length >= len(content):
        assert truncated == content
    else:
        assert truncated.endswith("[Content truncated due to length]")
        assert len(truncated) == length + len("\n\n[Content truncated due to length]")


def test_truncate_html_exact_and_overflow():
    soup = BeautifulSoup(HTML_SNIPPET, "html.parser")
    # Exact length: should return original html/text
    exact_len = len(HTML_SNIPPET)
    assert truncate_html(HTML_SNIPPET, exact_len) == HTML_SNIPPET

    # Overflow length: should include truncation notice
    short_len = 10
    truncated = truncate_html(HTML_SNIPPET, short_len, soup)
    assert truncated.endswith("[Content truncated due to length]")

    # Check the length of the truncated text, ignoring whitespace
    truncated_text = truncated.split("[Content truncated due to length]")[0].strip()
    assert len(truncated_text) == short_len
