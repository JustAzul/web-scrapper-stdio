from src.scraper.domain.value_objects.processing_config import ProcessingConfig

def test_processing_config_creation_and_properties():
    config = ProcessingConfig(
        custom_elements_to_remove=[".ads", ".banner"],
        click_selector="#btn"
    )
    assert config.custom_elements_to_remove == [".ads", ".banner"]
    assert config.click_selector == "#btn"
    assert config.has_custom_elements is True
    assert config.has_click_selector is True
    assert config.elements_count == 2
    combined = config.get_all_elements_to_remove(["header", "footer"])
    assert ".ads" in combined and "header" in combined

def test_processing_config_defaults_and_methods():
    config = ProcessingConfig()
    assert config.custom_elements_to_remove == []
    assert config.click_selector is None
    assert config.has_custom_elements is False
    assert config.has_click_selector is False
    assert config.elements_count == 0
    # Test with_elements
    new_config = config.with_elements([".x"])
    assert new_config.custom_elements_to_remove == [".x"]
    # Test with_click_selector
    new_config2 = config.with_click_selector(".y")
    assert new_config2.click_selector == ".y"
    # Test add_element
    config2 = config.add_element(".z")
    assert ".z" in config2.custom_elements_to_remove
    # Test remove_element
    config3 = config2.remove_element(".z")
    assert ".z" not in config3.custom_elements_to_remove
