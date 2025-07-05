from src.scraper.domain.value_objects.extraction_config import ExtractionConfig

def test_extraction_config_creation_and_properties():
    config = ExtractionConfig(
        elements_to_remove=[".ads", "script"],
        custom_elements_to_remove=[".banner"],
        use_chunked_processing=False,
        memory_limit_mb=42,
        parser="lxml",
        enable_fallback=False,
        chunk_size_threshold=2048,
        extra_noise_cleanup=True
    )
    # custom_elements_to_remove é mesclado em elements_to_remove
    assert ".ads" in config.elements_to_remove
    assert ".banner" in config.elements_to_remove
    assert config.use_chunked_processing is False
    assert config.memory_limit_mb == 42
    assert config.parser == "lxml"
    assert config.enable_fallback is False
    assert config.chunk_size_threshold == 2048
    assert config.extra_noise_cleanup is True

def test_extraction_config_with_defaults():
    config = ExtractionConfig()
    assert isinstance(config.elements_to_remove, list)
    assert config.use_chunked_processing is True
    assert config.enable_fallback is True
    assert config.memory_limit_mb == 150
    assert config.parser == "html.parser"
    assert config.chunk_size_threshold == 102400
    assert config.extra_noise_cleanup is False
