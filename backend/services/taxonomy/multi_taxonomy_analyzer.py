"""Multi-Taxonomy Analyzer.

Cross-taxonomy consistency analysis for YKS questions.
Combines Bloom, SOLO, Marzano, and Webb DOK taxonomies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.question_generation import (
    CognitiveLevel,
    MarzanoProcessLevel,
    MarzanoSystem,
    SOLOLevel,
    WebbDOKLevel,
)
from services.bloom_taxonomy_classifier import BloomTaxonomyClassifier
from services.taxonomy.marzano_classifier import classify_marzano
from services.taxonomy.solo_classifier import classify_solo

# Cross-validation matrix: Expected mappings between taxonomies
# Format: {bloom_level: {solo_level: weight, marzano_cognitive: weight}}
CROSS_VALIDATION_MATRIX: dict[CognitiveLevel, dict[str, list[str]]] = {
    CognitiveLevel.BILGI: {
        "solo": [SOLOLevel.UNISTRUCTURAL.value, SOLOLevel.PRESTRUCTURAL.value],
        "marzano": [MarzanoProcessLevel.RETRIEVAL.value],
        "webb_dok": [WebbDOKLevel.RECALL.value],
    },
    CognitiveLevel.KAVRAMA: {
        "solo": [SOLOLevel.MULTISTRUCTURAL.value, SOLOLevel.UNISTRUCTURAL.value],
        "marzano": [MarzanoProcessLevel.COMPREHENSION.value],
        "webb_dok": [WebbDOKLevel.SKILL.value, WebbDOKLevel.RECALL.value],
    },
    CognitiveLevel.UYGULAMA: {
        "solo": [SOLOLevel.MULTISTRUCTURAL.value, SOLOLevel.RELATIONAL.value],
        "marzano": [
            MarzanoProcessLevel.KNOWLEDGE_UTILIZATION.value,
            MarzanoProcessLevel.COMPREHENSION.value,
        ],
        "webb_dok": [WebbDOKLevel.SKILL.value, WebbDOKLevel.STRATEGIC.value],
    },
    CognitiveLevel.ANALIZ: {
        "solo": [SOLOLevel.RELATIONAL.value, SOLOLevel.MULTISTRUCTURAL.value],
        "marzano": [MarzanoProcessLevel.ANALYSIS.value],
        "webb_dok": [WebbDOKLevel.STRATEGIC.value],
    },
    CognitiveLevel.SENTEZ: {
        "solo": [
            SOLOLevel.EXTENDED_ABSTRACT.value,
            SOLOLevel.RELATIONAL.value,
        ],
        "marzano": [
            MarzanoProcessLevel.KNOWLEDGE_UTILIZATION.value,
            MarzanoProcessLevel.ANALYSIS.value,
        ],
        "webb_dok": [WebbDOKLevel.EXTENDED.value, WebbDOKLevel.STRATEGIC.value],
    },
    CognitiveLevel.DEGERLENDIRME: {
        "solo": [SOLOLevel.EXTENDED_ABSTRACT.value],
        "marzano": [MarzanoProcessLevel.KNOWLEDGE_UTILIZATION.value],
        "webb_dok": [WebbDOKLevel.EXTENDED.value],
    },
}

# YKS distribution targets (based on TYT/AYT analysis)
YKS_TARGET_DISTRIBUTION: dict[str, dict[str, float]] = {
    "bloom": {
        CognitiveLevel.BILGI.value: 0.15,
        CognitiveLevel.KAVRAMA.value: 0.25,
        CognitiveLevel.UYGULAMA.value: 0.30,
        CognitiveLevel.ANALIZ.value: 0.20,
        CognitiveLevel.SENTEZ.value: 0.07,
        CognitiveLevel.DEGERLENDIRME.value: 0.03,
    },
    "solo": {
        SOLOLevel.PRESTRUCTURAL.value: 0.05,
        SOLOLevel.UNISTRUCTURAL.value: 0.20,
        SOLOLevel.MULTISTRUCTURAL.value: 0.35,
        SOLOLevel.RELATIONAL.value: 0.30,
        SOLOLevel.EXTENDED_ABSTRACT.value: 0.10,
    },
    "webb_dok": {
        WebbDOKLevel.RECALL.value: 0.20,
        WebbDOKLevel.SKILL.value: 0.35,
        WebbDOKLevel.STRATEGIC.value: 0.35,
        WebbDOKLevel.EXTENDED.value: 0.10,
    },
}


@dataclass
class MultiTaxonomyResult:
    """Multi-taxonomy analysis result.

    Attributes:
        bloom_level: Bloom taxonomy level.
        solo_level: SOLO taxonomy level.
        marzano_system: Marzano system.
        marzano_cognitive: Marzano cognitive level (if COGNITIVE system).
        webb_dok: Webb DOK level.
        consistency_score: Cross-taxonomy consistency (0.0-1.0).
        inconsistencies: List of detected inconsistencies.
    """

    bloom_level: CognitiveLevel
    solo_level: SOLOLevel
    marzano_system: MarzanoSystem
    marzano_cognitive: MarzanoProcessLevel
    webb_dok: WebbDOKLevel
    consistency_score: float = 0.0
    inconsistencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Dict representation."""
        return {
            "bloom_level": self.bloom_level.value,
            "solo_level": self.solo_level.value,
            "marzano_system": self.marzano_system.value,
            "marzano_cognitive": self.marzano_cognitive.value,
            "webb_dok": self.webb_dok.value,
            "consistency_score": round(self.consistency_score, 3),
            "inconsistencies": self.inconsistencies,
        }


def analyze_all(question_text: str, subject: str = "") -> MultiTaxonomyResult:
    """Analyze question using all taxonomies.

    Args:
        question_text: Question text.
        subject: Subject name (optional).

    Returns:
        MultiTaxonomyResult with all taxonomy levels and consistency score.
    """
    # Classify using each taxonomy
    bloom_classifier = BloomTaxonomyClassifier()
    bloom_level_int, _, bloom_confidence = bloom_classifier.classify_question(
        question_text
    )
    bloom_level = _int_to_bloom_enum(bloom_level_int)

    solo_result = classify_solo(question_text, subject)
    solo_level = solo_result.level

    marzano_result = classify_marzano(question_text, subject)
    marzano_system = marzano_result.system
    marzano_cognitive = marzano_result.cognitive_level

    # Webb DOK (placeholder - will be implemented in separate task)
    webb_dok = _infer_webb_dok_from_bloom(bloom_level)

    # Calculate consistency score
    consistency_score, inconsistencies = _calculate_consistency(
        bloom_level, solo_level, marzano_cognitive, webb_dok
    )

    return MultiTaxonomyResult(
        bloom_level=bloom_level,
        solo_level=solo_level,
        marzano_system=marzano_system,
        marzano_cognitive=marzano_cognitive,
        webb_dok=webb_dok,
        consistency_score=consistency_score,
        inconsistencies=inconsistencies,
    )


def _int_to_bloom_enum(bloom_int: int) -> CognitiveLevel:
    """Convert Bloom int to enum."""
    mapping = {
        1: CognitiveLevel.BILGI,
        2: CognitiveLevel.KAVRAMA,
        3: CognitiveLevel.UYGULAMA,
        4: CognitiveLevel.ANALIZ,
        5: CognitiveLevel.SENTEZ,
        6: CognitiveLevel.DEGERLENDIRME,
    }
    return mapping.get(bloom_int, CognitiveLevel.KAVRAMA)


def _infer_webb_dok_from_bloom(bloom_level: CognitiveLevel) -> WebbDOKLevel:
    """Infer Webb DOK from Bloom (temporary until Webb classifier is ready).

    Args:
        bloom_level: Bloom taxonomy level.

    Returns:
        Webb DOK level.
    """
    mapping = {
        CognitiveLevel.BILGI: WebbDOKLevel.RECALL,
        CognitiveLevel.KAVRAMA: WebbDOKLevel.SKILL,
        CognitiveLevel.UYGULAMA: WebbDOKLevel.SKILL,
        CognitiveLevel.ANALIZ: WebbDOKLevel.STRATEGIC,
        CognitiveLevel.SENTEZ: WebbDOKLevel.EXTENDED,
        CognitiveLevel.DEGERLENDIRME: WebbDOKLevel.EXTENDED,
    }
    return mapping.get(bloom_level, WebbDOKLevel.SKILL)


def _calculate_consistency(
    bloom: CognitiveLevel,
    solo: SOLOLevel,
    marzano_cog: MarzanoProcessLevel,
    webb: WebbDOKLevel,
) -> tuple[float, list[str]]:
    """Calculate cross-taxonomy consistency score.

    Args:
        bloom: Bloom level.
        solo: SOLO level.
        marzano_cog: Marzano cognitive level.
        webb: Webb DOK level.

    Returns:
        (consistency_score, inconsistencies)
    """
    inconsistencies: list[str] = []
    matches = 0
    total_checks = 0

    # Check Bloom vs SOLO
    expected = CROSS_VALIDATION_MATRIX.get(bloom, {})
    if "solo" in expected:
        total_checks += 1
        if solo.value in expected["solo"]:
            matches += 1
        else:
            inconsistencies.append(
                f"Bloom {bloom.value} expects SOLO {expected['solo']}, got {solo.value}"
            )

    # Check Bloom vs Marzano
    if "marzano" in expected:
        total_checks += 1
        if marzano_cog.value in expected["marzano"]:
            matches += 1
        else:
            inconsistencies.append(
                f"Bloom {bloom.value} expects Marzano {expected['marzano']}, "
                f"got {marzano_cog.value}"
            )

    # Check Bloom vs Webb DOK
    if "webb_dok" in expected:
        total_checks += 1
        if webb.value in expected["webb_dok"]:
            matches += 1
        else:
            inconsistencies.append(
                f"Bloom {bloom.value} expects Webb DOK {expected['webb_dok']}, "
                f"got {webb.value}"
            )

    # Calculate score
    consistency_score = matches / total_checks if total_checks > 0 else 0.0

    return round(consistency_score, 3), inconsistencies


def get_yks_distribution_targets() -> dict[str, dict[str, float]]:
    """Get YKS target distribution for all taxonomies.

    Returns:
        Distribution targets for Bloom, SOLO, Webb DOK.
    """
    return YKS_TARGET_DISTRIBUTION.copy()
