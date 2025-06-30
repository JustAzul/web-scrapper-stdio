"""
ProcessingConfig - Single Responsibility: Content processing configuration

Extracted from ScrapingConfig to follow SRP principle.
This class is responsible only for content processing-related configuration.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ProcessingConfig:
    """
    Configuration for content processing.

    Single Responsibility: Handles all content processing-related configuration.
    """

    custom_elements_to_remove: List[str] = field(default_factory=list)
    click_selector: Optional[str] = None

    @property
    def has_custom_elements(self) -> bool:
        """Check if custom elements to remove are specified."""
        return len(self.custom_elements_to_remove) > 0

    @property
    def has_click_selector(self) -> bool:
        """Check if click selector is specified."""
        return self.click_selector is not None and self.click_selector.strip() != ""

    @property
    def elements_count(self) -> int:
        """Get count of custom elements to remove."""
        return len(self.custom_elements_to_remove)

    def get_all_elements_to_remove(self, default_elements: List[str]) -> List[str]:
        """Get combined list of default and custom elements to remove."""
        all_elements = default_elements.copy()
        if self.has_custom_elements:
            all_elements.extend(self.custom_elements_to_remove)
        return list(set(all_elements))  # Remove duplicates

    def with_elements(self, elements: List[str]) -> "ProcessingConfig":
        """Create new ProcessingConfig with different elements to remove."""
        return ProcessingConfig(
            custom_elements_to_remove=elements.copy(),
            click_selector=self.click_selector,
        )

    def with_click_selector(self, selector: Optional[str]) -> "ProcessingConfig":
        """Create new ProcessingConfig with different click selector."""
        return ProcessingConfig(
            custom_elements_to_remove=self.custom_elements_to_remove.copy(),
            click_selector=selector,
        )

    def add_element(self, element: str) -> "ProcessingConfig":
        """Create new ProcessingConfig with additional element to remove."""
        new_elements = self.custom_elements_to_remove.copy()
        if element not in new_elements:
            new_elements.append(element)
        return ProcessingConfig(
            custom_elements_to_remove=new_elements, click_selector=self.click_selector
        )

    def remove_element(self, element: str) -> "ProcessingConfig":
        """Create new ProcessingConfig with element removed."""
        new_elements = [e for e in self.custom_elements_to_remove if e != element]
        return ProcessingConfig(
            custom_elements_to_remove=new_elements, click_selector=self.click_selector
        )

    def __str__(self) -> str:
        """String representation."""
        elements_str = f"elements={len(self.custom_elements_to_remove)}"
        click_str = f", click='{self.click_selector}'" if self.click_selector else ""
        return f"ProcessingConfig({elements_str}{click_str})"
