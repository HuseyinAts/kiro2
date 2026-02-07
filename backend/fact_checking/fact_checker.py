"""
Fact-Checking Engine

Bu modül, AI yanıtlarındaki bilgilerin doğruluğunu kontrol eden
ana fact-checking engine'ıdır.

Features:
- Claim extraction (NLP)
- Parallel fact-checking (asyncio.gather)
- Source priority: MEB (60%) > RAG (30%) > Wikipedia (10%)
- Confidence score calculation

Requirements: REQ-4.1 - REQ-4.6

Weight in total confidence: 40%
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from backend.fact_checking.meb_resource_client import (
    MEBResourceClient,
    MEBVerificationResult,
)
from backend.fact_checking.rag_client import RAGClient, RAGVerificationResult
from backend.fact_checking.wikipedia_client import (
    WikipediaClient,
    WikipediaVerificationResult,
)
from backend.validators.base_response_validator import (
    AgentResponse,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class ClaimVerification(BaseModel):
    """Tek bir iddia için doğrulama sonucu"""
    claim: str = Field(description="Doğrulanan iddia")
    status: str = Field(description="true/false/partially_true/unverified")
    confidence: float = Field(ge=0.0, le=1.0, description="Güven skoru")
    source: str = Field(description="Kaynak (MEB/RAG/Wikipedia/none)")
    evidence: Optional[str] = Field(default=None, description="Kanıt")


class FactChecker:
    """
    Ana fact-checking engine.

    RAG, Wikipedia ve MEB kaynaklarını kullanarak
    AI yanıtlarındaki iddiaları doğrular.

    Source Priority (Spec REQ-4.4):
    - MEB: 60%
    - RAG: 30%
    - Wikipedia: 10%
    """

    # Source ağırlıkları
    SOURCE_WEIGHTS = {
        "MEB": 0.60,
        "RAG": 0.30,
        "Wikipedia": 0.10,
    }

    # Türkçe görüş belirteçleri (bunları iddia olarak sayma)
    OPINION_MARKERS = [
        "sanırım", "bence", "galiba", "belki", "muhtemelen",
        "düşünüyorum", "tahminimce", "kanımca", "görüşümce",
    ]

    def __init__(
        self,
        rag_client: Optional[RAGClient] = None,
        wikipedia_client: Optional[WikipediaClient] = None,
        meb_client: Optional[MEBResourceClient] = None,
        parallel_checking: bool = True,
        max_claims: int = 10,
    ):
        """
        Args:
            rag_client: RAG client instance
            wikipedia_client: Wikipedia client instance
            meb_client: MEB client instance
            parallel_checking: Paralel doğrulama aktif mi
            max_claims: Maksimum kontrol edilecek iddia sayısı
        """
        self.rag = rag_client or RAGClient()
        self.wikipedia = wikipedia_client or WikipediaClient()
        self.meb = meb_client or MEBResourceClient()
        self.parallel_checking = parallel_checking
        self.max_claims = max_claims

    async def check_facts(
        self, response: AgentResponse
    ) -> ValidationResult:
        """
        AI yanıtındaki tüm iddiaları doğrula.

        Args:
            response: Doğrulanacak agent yanıtı

        Returns:
            ValidationResult: Fact-checking sonucu
        """
        errors: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        score = 1.0

        # İddiaları çıkar
        claims = self._extract_claims(response.response_text)

        if not claims:
            return ValidationResult(
                is_valid=True,
                score=1.0,
                errors=[],
                warnings=["Doğrulanacak iddia bulunamadı"],
                suggestions=[],
                metadata={
                    "fact_checker": "FactChecker",
                    "claims_checked": 0,
                },
            )

        # Her iddiayı doğrula
        verified_claims: List[ClaimVerification] = []

        if self.parallel_checking:
            # Paralel doğrulama
            tasks = [
                self._verify_single_claim(claim)
                for claim in claims[:self.max_claims]
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, ClaimVerification):
                    verified_claims.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Claim verification error: {result}")
        else:
            # Sıralı doğrulama
            for claim in claims[:self.max_claims]:
                try:
                    result = await self._verify_single_claim(claim)
                    verified_claims.append(result)
                except Exception as e:
                    logger.error(f"Claim verification error: {e}")

        # Sonuçları işle
        for verification in verified_claims:
            if verification.status == "false":
                errors.append(f"Yanlış bilgi: {verification.claim}")
                score -= 0.3
            elif verification.status == "unverified":
                warnings.append(f"Doğrulanamayan bilgi: {verification.claim}")
                score -= 0.1
            elif verification.status == "partially_true":
                warnings.append(f"Kısmen doğru bilgi: {verification.claim}")
                score -= 0.05

        # Öneriler oluştur
        if errors:
            suggestions.append(
                "Yanlış bilgileri düzeltin veya güvenilir kaynaklarla destekleyin"
            )
        if warnings:
            suggestions.append(
                "Doğrulanamayan bilgiler için kaynak belirtin"
            )

        # Skoru sınırla
        score = max(0.0, min(1.0, score))

        return ValidationResult(
            is_valid=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={
                "fact_checker": "FactChecker",
                "claims_checked": len(claims),
                "verified_claims": [v.model_dump() for v in verified_claims],
                "source_usage": self._calculate_source_usage(verified_claims),
            },
        )

    def _extract_claims(self, text: str) -> List[str]:
        """
        Metinden iddiaları çıkar.

        Args:
            text: Metin

        Returns:
            List[str]: İddia listesi
        """
        # Cümlelere ayır
        sentences = re.split(r'[.!?]\s+', text)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            # Minimum uzunluk
            if len(sentence) < 10:
                continue

            # Soru cümlelerini atla
            if '?' in sentence:
                continue

            # Görüş belirteçlerini atla
            sentence_lower = sentence.lower()
            if any(marker in sentence_lower for marker in self.OPINION_MARKERS):
                continue

            # Emir cümlelerini atla
            command_patterns = [
                r'^(yap|et|gel|git|al|ver|bak|oku|yaz)',
                r'^(lütfen|rica)',
            ]
            if any(re.match(p, sentence_lower) for p in command_patterns):
                continue

            # Sayısal veya bilimsel içerik içeriyorsa öncelikli
            has_dates = bool(re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', sentence))
            has_scientific = any(
                kw in sentence_lower
                for kw in ['formül', 'denklem', 'kanun', 'teori', 'prensip']
            )

            # Öncelikli iddiaları başa al
            if has_dates or has_scientific:
                claims.insert(0, sentence)
            else:
                claims.append(sentence)

        return claims

    async def _verify_single_claim(self, claim: str) -> ClaimVerification:
        """
        Tek bir iddiayı tüm kaynaklarda doğrula.

        Args:
            claim: Doğrulanacak iddia

        Returns:
            ClaimVerification: Doğrulama sonucu
        """
        # Paralel olarak tüm kaynakları kontrol et
        meb_task = self.meb.verify_claim(claim)
        rag_task = self.rag.verify_claim(claim)
        wiki_task = self.wikipedia.verify_claim(claim)

        results = await asyncio.gather(
            meb_task, rag_task, wiki_task,
            return_exceptions=True,
        )

        meb_result = (
            results[0] if isinstance(results[0], MEBVerificationResult)
            else MEBVerificationResult(found=False, confidence=0.0, status="unverified")
        )
        rag_result = (
            results[1] if isinstance(results[1], RAGVerificationResult)
            else RAGVerificationResult(found=False, confidence=0.0, status="unverified")
        )
        wiki_result = (
            results[2] if isinstance(results[2], WikipediaVerificationResult)
            else WikipediaVerificationResult(found=False, confidence=0.0, status="unverified")
        )

        # Sonuçları birleştir (priority: MEB > RAG > Wikipedia)
        return self._combine_verifications(
            claim, meb_result, rag_result, wiki_result
        )

    def _combine_verifications(
        self,
        claim: str,
        meb_result: MEBVerificationResult,
        rag_result: RAGVerificationResult,
        wiki_result: WikipediaVerificationResult,
    ) -> ClaimVerification:
        """
        Doğrulama sonuçlarını birleştir.

        Priority: MEB (60%) > RAG (30%) > Wikipedia (10%)

        Args:
            claim: İddia
            meb_result: MEB sonucu
            rag_result: RAG sonucu
            wiki_result: Wikipedia sonucu

        Returns:
            ClaimVerification: Birleştirilmiş sonuç
        """
        # MEB bulunduysa öncelikli kullan
        if meb_result.found and meb_result.confidence > 0.5:
            return ClaimVerification(
                claim=claim,
                status=meb_result.status,
                confidence=meb_result.confidence * self.SOURCE_WEIGHTS["MEB"],
                source="MEB",
                evidence=meb_result.evidence,
            )

        # RAG bulunduysa
        if rag_result.found and rag_result.confidence > 0.5:
            return ClaimVerification(
                claim=claim,
                status=rag_result.status,
                confidence=rag_result.confidence * self.SOURCE_WEIGHTS["RAG"],
                source="RAG",
                evidence=rag_result.evidence,
            )

        # Wikipedia bulunduysa
        if wiki_result.found and wiki_result.confidence > 0.5:
            return ClaimVerification(
                claim=claim,
                status=wiki_result.status,
                confidence=wiki_result.confidence * self.SOURCE_WEIGHTS["Wikipedia"],
                source="Wikipedia",
                evidence=wiki_result.evidence,
            )

        # Hiçbiri bulamadıysa
        # En yüksek confidence'a sahip sonucu al
        best_result = max(
            [
                (meb_result.confidence, meb_result.status, "MEB", meb_result.evidence),
                (rag_result.confidence, rag_result.status, "RAG", rag_result.evidence),
                (wiki_result.confidence, wiki_result.status, "Wikipedia", wiki_result.evidence),
            ],
            key=lambda x: x[0],
        )

        if best_result[0] > 0:
            return ClaimVerification(
                claim=claim,
                status=best_result[1],
                confidence=best_result[0] * 0.5,  # Düşük güven
                source=best_result[2],
                evidence=best_result[3],
            )

        return ClaimVerification(
            claim=claim,
            status="unverified",
            confidence=0.0,
            source="none",
            evidence=None,
        )

    def _calculate_source_usage(
        self, verifications: List[ClaimVerification]
    ) -> Dict[str, int]:
        """
        Kaynak kullanım istatistiklerini hesapla.

        Args:
            verifications: Doğrulama listesi

        Returns:
            Dict: Kaynak kullanım sayıları
        """
        usage = {"MEB": 0, "RAG": 0, "Wikipedia": 0, "none": 0}

        for v in verifications:
            if v.source in usage:
                usage[v.source] += 1

        return usage

    async def verify_specific_fact(
        self,
        fact: str,
        expected_value: str,
        subject: Optional[str] = None,
    ) -> Tuple[bool, float, str]:
        """
        Belirli bir gerçeği doğrula.

        Args:
            fact: Gerçek adı (örn: "ışık hızı")
            expected_value: Beklenen değer
            subject: Ders adı (opsiyonel)

        Returns:
            Tuple[bool, float, str]: (doğru_mu, confidence, evidence)
        """
        # Önce MEB'den kontrol et
        if subject:
            meb_value = self.meb.get_fact(subject, fact)
            if meb_value:
                is_correct = expected_value.lower() in meb_value.lower()
                return (
                    is_correct,
                    0.95 if is_correct else 0.3,
                    f"MEB: {fact} = {meb_value}",
                )

        # Genel doğrulama
        claim = f"{fact} {expected_value}"
        verification = await self._verify_single_claim(claim)

        is_correct = verification.status in ["true", "partially_true"]
        return (
            is_correct,
            verification.confidence,
            verification.evidence or "",
        )
