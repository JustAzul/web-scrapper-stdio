from src.enums import OutputFormat

def test_output_format_enum_values():
    assert OutputFormat.MARKDOWN.value == "markdown"
    assert OutputFormat.TEXT.value == "text"
    assert OutputFormat.HTML.value == "html"

def test_output_format_enum_members():
    assert set(OutputFormat.__members__.keys()) == {"MARKDOWN", "TEXT", "HTML"}
