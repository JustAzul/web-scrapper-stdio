import pytest
from src.output_format_handler import format_content, to_markdown, to_text, to_html
from src.enums import OutputFormat

def test_format_content_markdown():
    html = "<h1>Title</h1><p>Content</p>"
    result = format_content(html, OutputFormat.MARKDOWN)
    assert "# Title" in result or "Title" in result

def test_format_content_text():
    html = "<h1>Title</h1><p>Content</p>"
    result = format_content(html, OutputFormat.TEXT)
    assert "Title" in result and "Content" in result

def test_format_content_html():
    html = "<h1>Title</h1><p>Content</p>"
    result = format_content(html, OutputFormat.HTML)
    assert "<h1>Title</h1>" in result and "<p>Content</p>" in result

def test_to_markdown():
    html = "<h1>Title</h1><p>Content</p>"
    md = to_markdown(html)
    assert "# Title" in md or "Title" in md

def test_to_text():
    html = "<h1>Title</h1><p>Content</p>"
    txt = to_text(html)
    assert "Title" in txt and "Content" in txt

def test_to_html():
    html = "<h1>Title</h1><p>Content</p>"
    html_out = to_html(html)
    assert "<h1>Title</h1>" in html_out and "<p>Content</p>" in html_out
