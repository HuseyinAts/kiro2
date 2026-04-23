"""
Specialization Scorer - Agent Uzmanlik Skoru Hesaplama
REQ-8.1, REQ-8.2
Teknofest 2025 - KIRO2 YKS Platformu

Agirlikli Uzmanlik Skoru:
- Domain Relevance: 40%
- Accuracy: 30%
- Completeness: 20%
- User Satisfaction: 10%
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..domain_experts.base_domain_agent import DomainResponse, DomainType

logger = logging.getLogger(__name__)

# Exact weights (REQ-8.2)
WEIGHT_RELEVANCE = 0.40
WEIGHT_ACCURACY = 0.30
WEIGHT_COMPLETENESS = 0.20
WEIGHT_SATISFACTION = 0.10


@dataclass
class SpecializationScore:
    """
    Agent uzmanlik skoru (REQ-8.1, REQ-8.2)

    Formula: 0.4*relevance + 0.3*accuracy + 0.2*completeness + 0.1*satisfaction
    """

    domain: DomainType
    domain_relevance: float  # [0, 1]
    accuracy: float  # [0, 1]
    completeness: float  # [0, 1]
    user_satisfaction: float  # [0, 1]
    total_score: float  # [0, 1]
    calculated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain.value,
            "domain_relevance": self.domain_relevance,
            "accuracy": self.accuracy,
            "completeness": self.completeness,
            "user_satisfaction": self.user_satisfaction,
            "total_score": self.total_score,
            "calculated_at": self.calculated_at.isoformat(),
        }


class SpecializationScorer:
    """
    Uzmanlik Skoru Hesaplayici (REQ-8.1, REQ-8.2)

    Her agent icin uzmanlik skorunu hesaplar ve izler.
    Skor <= 0.7 ise yeniden egitim onerilir (REQ-8.6).
    """

    RETRAINING_THRESHOLD = 0.70

    def __init__(self):
        """SpecializationScorer olustur"""
        self._scores: dict[DomainType, list[SpecializationScore]] = {}
        logger.info("SpecializationScorer initialized")

    def calculate_score(
        self,
        domain: DomainType,
        relevance: float,
        accuracy: float,
        completeness: float,
        satisfaction: float,
    ) -> SpecializationScore:
        """
        Uzmanlik skorunu hesapla (REQ-8.2)

        Args:
            domain: Agent domain'i
            relevance: Domain uygunluk skoru [0, 1]
            accuracy: Dogruluk skoru [0, 1]
            completeness: Tamlik skoru [0, 1]
            satisfaction: Kullanici memnuniyet skoru [0, 1]

        Returns:
            SpecializationScore: Hesaplanan skor
        """
        # Validate inputs
        for name, value in [
            ("relevance", relevance),
            ("accuracy", accuracy),
            ("completeness", completeness),
            ("satisfaction", satisfaction),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")

        # Calculate total score (EXACT formula REQ-8.2)
        total = (
            relevance * WEIGHT_RELEVANCE
            + accuracy * WEIGHT_ACCURACY
            + completeness * WEIGHT_COMPLETENESS
            + satisfaction * WEIGHT_SATISFACTION
        )

        score = SpecializationScore(
            domain=domain,
            domain_relevance=relevance,
            accuracy=accuracy,
            completeness=completeness,
            user_satisfaction=satisfaction,
            total_score=total,
            calculated_at=datetime.now(),
        )

        # Store score
        if domain not in self._scores:
            self._scores[domain] = []
        self._scores[domain].append(score)

        logger.info(
            f"Calculated score for {domain.value}: {total:.3f} "
            f"(R:{relevance:.2f}, A:{accuracy:.2f}, C:{completeness:.2f}, S:{satisfaction:.2f})"
        )

        return score

    def calculate_from_response(
        self,
        response: DomainResponse,
        user_satisfaction: float = 0.8,
    ) -> SpecializationScore:
        """
        Agent yanitindan skor hesapla

        Args:
            response: Agent yaniti
            user_satisfaction: Kullanici memnuniyet skoru [0, 1]

        Returns:
            SpecializationScore: Hesaplanan skor
        """
        # Extract relevance from confidence
        relevance = response.confidence

        # Calculate accuracy (based on tools used and steps)
        accuracy = 0.7  # Base
        if response.tools_used:
            accuracy += 0.15
        if response.step_by_step_solution:
            accuracy += 0.15
        accuracy = min(1.0, accuracy)

        # Calculate completeness
        completeness = 0.6  # Base
        if response.step_by_step_solution:
            completeness += 0.2
        if response.visualizations:
            completeness += 0.1
        if response.references:
            completeness += 0.1
        completeness = min(1.0, completeness)

        return self.calculate_score(
            domain=response.domain,
            relevance=relevance,
            accuracy=accuracy,
            completeness=completeness,
            satisfaction=user_satisfaction,
        )

    def get_average_score(self, domain: DomainType) -> float | None:
        """Domain icin ortalama skoru al"""
        scores = self._scores.get(domain, [])
        if not scores:
            return None
        return sum(s.total_score for s in scores) / len(scores)

    def get_latest_score(self, domain: DomainType) -> SpecializationScore | None:
        """Domain icin son skoru al"""
        scores = self._scores.get(domain, [])
        if not scores:
            return None
        return scores[-1]

    def needs_retraining(self, domain: DomainType) -> bool:
        """
        Yeniden egitim gerekli mi? (REQ-8.6)

        Returns:
            True eger ortalama skor < 0.70
        """
        avg_score = self.get_average_score(domain)
        if avg_score is None:
            return False
        return avg_score < self.RETRAINING_THRESHOLD

    def get_all_scores(self) -> dict[DomainType, SpecializationScore]:
        """Tum domain'ler icin son skorlari al"""
        return {
            domain: scores[-1]
            for domain, scores in self._scores.items()
            if scores
        }

    def get_domains_needing_retraining(self) -> list[DomainType]:
        """Yeniden egitim gereken domain'leri al"""
        return [
            domain
            for domain in self._scores.keys()
            if self.needs_retraining(domain)
        ]

    def get_best_performing_domain(self) -> DomainType | None:
        """En iyi performans gosteren domain'i al"""
        best_domain = None
        best_score = 0.0

        for domain in self._scores.keys():
            avg = self.get_average_score(domain)
            if avg and avg > best_score:
                best_score = avg
                best_domain = domain

        return best_domain

    def get_metrics(self) -> dict[str, Any]:
        """Scorer metriklerini al"""
        return {
            "total_scores_calculated": sum(len(s) for s in self._scores.values()),
            "domains_tracked": len(self._scores),
            "domains": {
                domain.value: {
                    "count": len(scores),
                    "average": self.get_average_score(domain),
                    "latest": scores[-1].total_score if scores else None,
                    "needs_retraining": self.needs_retraining(domain),
                }
                for domain, scores in self._scores.items()
            },
        }
