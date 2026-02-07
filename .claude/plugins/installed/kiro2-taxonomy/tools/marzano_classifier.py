"""Marzano Taxonomy classifier tool wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

_backend_path = str(Path(__file__).resolve().parents[5] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


def run(question_text: str, subject: str = "") -> dict:
    """Classify question using Marzano taxonomy."""
    from services.taxonomy.marzano_classifier import classify_marzano

    result = classify_marzano(question_text, subject)
    return {
        "system": result.system.value if hasattr(result.system, "value") else str(result.system),
        "cognitive_level": result.cognitive_level.value if hasattr(result.cognitive_level, "value") else str(result.cognitive_level),
        "confidence": round(result.confidence, 3),
        "matched_patterns": result.matched_patterns,
    }
