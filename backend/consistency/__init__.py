"""
AI Agent Yanıt Doğrulama Sistemi - Consistency Package

Bu paket, AI yanıtlarının önceki yanıtlarla tutarlılığını
kontrol eden bileşenleri içerir.

Components:
- ConsistencyChecker: Tutarlılık kontrolü
- ResponseHistoryManager: Redis yanıt geçmişi yönetimi

Consistency ağırlığı: %30 (toplam confidence score'da)

Features:
- Son 10 yanıt analizi
- Direct contradiction detection
- Semantic contradiction detection (embeddings)
"""

from backend.consistency.consistency_checker import ConsistencyChecker, Contradiction
from backend.consistency.response_history_manager import ResponseHistoryManager

__all__ = [
    "ConsistencyChecker",
    "Contradiction",
    "ResponseHistoryManager",
]
