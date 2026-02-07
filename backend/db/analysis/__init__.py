"""
Migration Analysis Module

Performans analizi ve etki degerlendirmesi saglar.
EXPLAIN ANALYZE, lock süresi tahmini, downtime uyarisi.
"""

from .performance import (
    PerformanceAnalyzer,
    ExplainResult,
    DowntimeAssessment,
    Recommendation,
)

__all__ = [
    "PerformanceAnalyzer",
    "ExplainResult",
    "DowntimeAssessment",
    "Recommendation",
]
