from bs4 import BeautifulSoup
import re
from markdownify import markdownify as md
from src.logger import Logger

logger = Logger(__name__)


def _extract_and_clean_html(html_content, elements_to_remove):
    soup = BeautifulSoup(html_content, 'html.parser')

    for element in soup(elements_to_remove):
        element.decompose()
    target_element = soup.body

    return soup, target_element


def _extract_markdown_and_text(target_element):
    text = target_element.get_text(separator='\n', strip=True)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    markdown_content = md(str(target_element))

    return markdown_content, text


def _is_content_too_short(text, min_length):
    return not text or len(text) < min_length
