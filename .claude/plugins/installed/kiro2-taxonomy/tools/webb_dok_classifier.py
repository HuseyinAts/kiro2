"""Webb DOK classifier tool wrapper."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_backend_path = str(Path(__file__).resolve().parents[5] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


def run(question_text: str, options: Optional[list[str]] = None) -> dict:
    """Classify question using Webb Depth of Knowledge."""
    from services.taxonomy.webb_dok_classifier import classify_webb_dok

    result = classify_webb_dok(question_text, options)
    return result.to_dict()
