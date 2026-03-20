"""
Turkish NLP Utilities — canonical text normalization.

CRITICAL RULES (CLAUDE.md §Turkish NLP):
1. NFC normalization FIRST (prevents İ decomposition)
2. Turkish mapping: İ→i, I→ı  (NOT İ→I!)
3. Standard lowercase LAST
"""

import unicodedata


def normalize_tr(text: str) -> str:
    """NFC + Turkish-correct lowercase normalization.

    Use for search, comparison, deduplication.
    """
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def tr_casefold(text: str) -> str:
    """Case-insensitive comparison key for Turkish (alias for normalize_tr)."""
    return normalize_tr(text)
