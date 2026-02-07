"""Cognitive Load Theory calculator tool wrapper."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_backend_path = str(Path(__file__).resolve().parents[5] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


def run(
    question_text: str,
    options: Optional[list[str]] = None,
    subject: str = "",
) -> dict:
    """Calculate cognitive load metrics for a question."""
    from services.taxonomy.cognitive_load_calculator import calculate_cognitive_load

    result = calculate_cognitive_load(question_text, options, subject)
    return result.to_dict()
