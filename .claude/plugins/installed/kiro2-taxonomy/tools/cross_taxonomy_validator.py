"""Cross-taxonomy validation tool wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

_backend_path = str(Path(__file__).resolve().parents[5] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


def run(question_text: str, subject: str = "") -> dict:
    """Validate cross-taxonomy consistency (Bloom/SOLO/Marzano/Webb DOK)."""
    from services.taxonomy.multi_taxonomy_analyzer import analyze_all

    result = analyze_all(question_text, subject)
    return {
        "bloom_level": result.bloom_level,
        "solo_level": result.solo_level,
        "marzano_system": result.marzano_system,
        "marzano_cognitive": result.marzano_cognitive,
        "webb_dok": result.webb_dok,
        "consistency_score": round(result.consistency_score, 3),
        "inconsistencies": result.inconsistencies,
    }
