"""kiro2-taxonomy Plugin - Multi-taxonomy siniflandirma araclari.

Bu plugin SOLO, Marzano, Webb DOK ve CLT (Cognitive Load Theory)
toollarini saglar. Soru siniflandirma ve kalite analizi icin kullanilir.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

# Backend services path'ini ekle
_backend_path = str(Path(__file__).resolve().parents[4] / "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


class KiroTaxonomyPlugin:
    """KIRO2 Taxonomy Plugin ana sinifi."""

    def __init__(self) -> None:
        self._solo = None
        self._marzano = None
        self._webb_dok = None
        self._clt = None

    def classify_solo(
        self, question_text: str, subject: str = ""
    ) -> dict[str, Any]:
        """SOLO taksonomi siniflandirmasi."""
        from services.taxonomy.solo_classifier import classify_solo

        result = classify_solo(question_text, subject)
        return {
            "level": result.level.value if hasattr(result.level, "value") else str(result.level),
            "confidence": round(result.confidence, 3),
            "matched_patterns": result.matched_patterns,
        }

    def classify_marzano(
        self, question_text: str, subject: str = ""
    ) -> dict[str, Any]:
        """Marzano taksonomi siniflandirmasi."""
        from services.taxonomy.marzano_classifier import classify_marzano

        result = classify_marzano(question_text, subject)
        return {
            "system": result.system.value if hasattr(result.system, "value") else str(result.system),
            "cognitive_level": result.cognitive_level.value if hasattr(result.cognitive_level, "value") else str(result.cognitive_level),
            "confidence": round(result.confidence, 3),
            "matched_patterns": result.matched_patterns,
        }

    def classify_webb_dok(
        self,
        question_text: str,
        options: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Webb DOK siniflandirmasi."""
        from services.taxonomy.webb_dok_classifier import classify_webb_dok

        result = classify_webb_dok(question_text, options)
        return result.to_dict()

    def calculate_cognitive_load(
        self,
        question_text: str,
        options: Optional[list[str]] = None,
        subject: str = "",
    ) -> dict[str, Any]:
        """Bilissel yuk hesapla (CLT)."""
        from services.taxonomy.cognitive_load_calculator import calculate_cognitive_load

        result = calculate_cognitive_load(question_text, options, subject)
        return result.to_dict()

    def validate_cross_taxonomy(
        self, question_text: str, subject: str = ""
    ) -> dict[str, Any]:
        """Capraz taksonomi dogrulamasi."""
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

    def full_analysis(
        self,
        question_text: str,
        options: Optional[list[str]] = None,
        subject: str = "",
    ) -> dict[str, Any]:
        """Tam taksonomi analizi (tum sistemler)."""
        return {
            "solo": self.classify_solo(question_text, subject),
            "marzano": self.classify_marzano(question_text, subject),
            "webb_dok": self.classify_webb_dok(question_text, options),
            "cognitive_load": self.calculate_cognitive_load(
                question_text, options, subject
            ),
            "cross_validation": self.validate_cross_taxonomy(
                question_text, subject
            ),
        }
