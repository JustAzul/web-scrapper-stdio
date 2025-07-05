# Standard lib imports
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from src.logger import get_logger

from .text_utils import normalize_text

logger = get_logger(__name__)


def _extract_and_clean_html(html_content, elements_to_remove):
    soup = BeautifulSoup(html_content, "html.parser")

    remove_elements(soup, elements_to_remove)
    target_element = soup.body

    return soup, target_element


def _extract_markdown_and_text(target_element):
    text = normalize_text(target_element.get_text(separator="\n", strip=True))
    markdown_content = md(str(target_element))

    return markdown_content, text


def _is_content_too_short(text, min_length):
    return not text or len(text) < min_length


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def remove_elements(soup: BeautifulSoup, selectors):
    """Decompose all elements matching *selectors* from *soup*.

    *selectors* can be:
      • tag names (e.g., ``'script'``)
      • CSS classes/IDs (e.g., ``'.ads', '#sidebar'``)
    """
    for sel in selectors:
        try:
            if sel.startswith(".") or sel.startswith("#"):
                for element in soup.select(sel):
                    element.decompose()
            else:
                for element in soup.find_all(sel):
                    element.decompose()
        except Exception as e:
            logger.warning(f"Failed to remove selector '{sel}': {e}")
