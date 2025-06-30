"""Text utility helpers shared by scraper modules."""

import re
from typing import Optional

__all__ = ["normalize_text"]


def normalize_text(text: Optional[str]) -> str:
    """Collapse consecutive blank lines and strip surrounding whitespace.

    This mirrors the logic previously duplicated in multiple modules.
    """
    if not text:
        return ""
    # Replace multi-line whitespace blocks with a single empty line, then trim.
    return re.sub(r"\n\s*\n", "\n\n", text).strip()
