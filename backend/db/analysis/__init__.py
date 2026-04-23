"""
Migration Analysis Module

Performans analizi ve etki degerlendirmesi saglar.
EXPLAIN ANALYZE, lock süresi tahmini, downtime uyarisi.
"""

from .performance import (
    DowntimeAssessment,
    ExplainResult,
    PerformanceAnalyzer,
    Recommendation,
)

__all__ = [
    "DowntimeAssessment",
    "ExplainResult",
    "PerformanceAnalyzer",
    "Recommendation",
]
