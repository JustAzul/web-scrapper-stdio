from src.scraper.domain.value_objects.output_config import OutputConfig
from src.output_format_handler import OutputFormat

def test_output_config_creation_and_properties():
    config = OutputConfig(
        format=OutputFormat.MARKDOWN,
        max_length=1000
    )
    assert config.format == OutputFormat.MARKDOWN
    assert config.max_length == 1000
    assert config.is_markdown_format is True
    assert config.is_text_format is False
    assert config.is_html_format is False
    assert config.has_length_limit is True
    assert config.should_truncate(1500) is True
    assert config.truncate_content("a" * 1200).endswith("...")

def test_output_config_defaults():
    config = OutputConfig()
    assert config.format == OutputFormat.MARKDOWN
    assert config.max_length is None
    assert config.has_length_limit is False
    assert config.truncate_content("abc") == "abc"
