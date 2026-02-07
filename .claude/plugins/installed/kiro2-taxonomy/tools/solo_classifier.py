"""SOLO Taxonomy classifier tool wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

_backend_path = str(Path(__file__).resolve().parents[5] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


def run(question_text: str, subject: str = "") -> dict:
    """Classify question using SOLO taxonomy."""
    from services.taxonomy.solo_classifier import classify_solo

    result = classify_solo(question_text, subject)
    return {
        "level": result.level.value if hasattr(result.level, "value") else str(result.level),
        "confidence": round(result.confidence, 3),
        "matched_patterns": result.matched_patterns,
        "subject_weight": round(result.subject_weight, 2),
    }
