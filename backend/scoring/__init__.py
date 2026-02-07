"""
AI Agent Yanıt Doğrulama Sistemi - Scoring Package

Bu paket, doğrulama sonuçlarından confidence score
hesaplayan bileşenleri içerir.

Components:
- ConfidenceScorer: Ağırlıklı confidence hesaplama

Weights:
- Agent-specific validation: 30%
- Fact-checking: 40%
- Consistency: 30%

Action Thresholds:
- >= 0.8: approve
- 0.5 - 0.8: review
- < 0.5: reject
"""

from backend.scoring.confidence_scorer import ConfidenceScorer

__all__ = [
    "ConfidenceScorer",
]
