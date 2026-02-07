"""
AI Agent Yanıt Doğrulama Sistemi - Fact-Checking Package

Bu paket, AI yanıtlarındaki bilgilerin doğruluğunu kontrol eden
fact-checking bileşenlerini içerir.

Components:
- FactChecker: Ana fact-checking engine
- RAGClient: ChromaDB RAG entegrasyonu
- WikipediaClient: Türkçe Wikipedia API client
- MEBResourceClient: MEB kaynak doğrulama

Fact-checking ağırlığı: %40 (toplam confidence score'da)

Source Priority:
- MEB: 60%
- RAG: 30%
- Wikipedia: 10%
"""

from backend.fact_checking.fact_checker import ClaimVerification, FactChecker
from backend.fact_checking.meb_resource_client import (
    MEBResourceClient,
    MEBVerificationResult,
)
from backend.fact_checking.rag_client import RAGClient, RAGVerificationResult
from backend.fact_checking.wikipedia_client import (
    WikipediaClient,
    WikipediaVerificationResult,
)

__all__ = [
    "FactChecker",
    "ClaimVerification",
    "RAGClient",
    "RAGVerificationResult",
    "WikipediaClient",
    "WikipediaVerificationResult",
    "MEBResourceClient",
    "MEBVerificationResult",
]
