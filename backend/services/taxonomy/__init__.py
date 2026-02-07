"""Taxonomy classification services - SOLO, Marzano, Webb DOK, CLT."""

from .cognitive_load_calculator import CLTResult, calculate_cognitive_load
from .marzano_classifier import MarzanoResult, classify_marzano
from .multi_taxonomy_analyzer import (
    MultiTaxonomyResult,
    analyze_all,
    get_yks_distribution_targets,
)
from .solo_classifier import SOLOResult, classify_solo
from .webb_dok_classifier import (
    WebbDOKResult,
    classify_webb_dok,
    estimate_dok_from_bloom,
)

__all__ = [
    "classify_solo",
    "SOLOResult",
    "classify_marzano",
    "MarzanoResult",
    "classify_webb_dok",
    "WebbDOKResult",
    "estimate_dok_from_bloom",
    "analyze_all",
    "MultiTaxonomyResult",
    "get_yks_distribution_targets",
    "calculate_cognitive_load",
    "CLTResult",
]
