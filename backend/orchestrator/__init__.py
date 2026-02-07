"""
AI Agent Yanıt Doğrulama Sistemi - Orchestrator Package

Bu paket, tüm doğrulama bileşenlerini koordine eden
ana orchestrator'ı içerir.

Components:
- ResponseValidationOrchestrator: Ana koordinatör

Features:
- Paralel validator çalıştırma (asyncio.gather)
- Result aggregation
- Performance tracking (< 2 saniye hedef)
- Error collection ve reporting
"""

from backend.orchestrator.response_validation_orchestrator import (
    ResponseValidationOrchestrator,
)

__all__ = [
    "ResponseValidationOrchestrator",
]
