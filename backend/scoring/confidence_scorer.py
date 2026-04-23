"""
Confidence Score Calculator

Bu modül, tüm validator sonuçlarından ağırlıklı confidence score hesaplar.

Weights:
- Agent-specific validation: 30%
- Fact-checking: 40%
- Consistency: 30%

Action Thresholds:
- >= 0.8: approve
- 0.5 - 0.8: review
- < 0.5: reject

Requirements: REQ-7.1 - REQ-7.6
"""

import logging

from backend.validators.base_response_validator import (
    ValidationAction,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Ağırlıklı confidence score hesaplayıcı.

    Tüm validator sonuçlarını birleştirerek nihai
    güven skorunu ve önerilen aksiyonu belirler.
    """

    # Varsayılan ağırlıklar
    DEFAULT_WEIGHTS = {
        "agent_specific": 0.30,
        "fact_checking": 0.40,
        "consistency": 0.30,
    }

    # Aksiyon eşik değerleri
    APPROVE_THRESHOLD = 0.80
    REVIEW_THRESHOLD = 0.50

    def __init__(
        self,
        weights: dict[str, float] = None,
        approve_threshold: float = 0.80,
        review_threshold: float = 0.50,
    ):
        """
        Args:
            weights: Özel ağırlıklar (opsiyonel)
            approve_threshold: Onay eşiği
            review_threshold: İnceleme eşiği
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.approve_threshold = approve_threshold
        self.review_threshold = review_threshold

        # Ağırlıkların toplamını doğrula
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(
                f"Weights sum to {total_weight}, normalizing to 1.0"
            )
            # Normalize et
            for key in self.weights:
                self.weights[key] /= total_weight

    def calculate_confidence(
        self,
        agent_validation: ValidationResult,
        fact_checking: ValidationResult,
        consistency: ValidationResult,
    ) -> float:
        """
        Ağırlıklı confidence score hesapla.

        Args:
            agent_validation: Agent-specific doğrulama sonucu
            fact_checking: Fact-checking sonucu
            consistency: Tutarlılık sonucu

        Returns:
            float: Confidence score (0-1)
        """
        # Ağırlıklı ortalama hesapla
        total_score = (
            agent_validation.score * self.weights["agent_specific"] +
            fact_checking.score * self.weights["fact_checking"] +
            consistency.score * self.weights["consistency"]
        )

        # Sınırla ve yuvarla
        confidence = max(0.0, min(1.0, total_score))
        return round(confidence, 3)

    def determine_action(self, confidence: float) -> ValidationAction:
        """
        Confidence score'a göre aksiyon belirle.

        Args:
            confidence: Confidence score

        Returns:
            ValidationAction: Önerilen aksiyon
        """
        if confidence >= self.approve_threshold:
            return ValidationAction.APPROVE
        if confidence >= self.review_threshold:
            return ValidationAction.REVIEW
        return ValidationAction.REJECT

    def calculate_and_determine(
        self,
        agent_validation: ValidationResult,
        fact_checking: ValidationResult,
        consistency: ValidationResult,
    ) -> tuple[float, ValidationAction]:
        """
        Confidence hesapla ve aksiyon belirle (kombine metot).

        Args:
            agent_validation: Agent-specific doğrulama sonucu
            fact_checking: Fact-checking sonucu
            consistency: Tutarlılık sonucu

        Returns:
            Tuple[float, ValidationAction]: (confidence, action)
        """
        confidence = self.calculate_confidence(
            agent_validation, fact_checking, consistency
        )
        action = self.determine_action(confidence)

        return confidence, action

    def get_score_breakdown(
        self,
        agent_validation: ValidationResult,
        fact_checking: ValidationResult,
        consistency: ValidationResult,
    ) -> dict[str, float]:
        """
        Skor dağılımını al (debugging için).

        Args:
            agent_validation: Agent-specific doğrulama sonucu
            fact_checking: Fact-checking sonucu
            consistency: Tutarlılık sonucu

        Returns:
            Dict: Skor breakdown
        """
        return {
            "agent_specific": {
                "raw_score": agent_validation.score,
                "weight": self.weights["agent_specific"],
                "weighted_score": agent_validation.score * self.weights["agent_specific"],
            },
            "fact_checking": {
                "raw_score": fact_checking.score,
                "weight": self.weights["fact_checking"],
                "weighted_score": fact_checking.score * self.weights["fact_checking"],
            },
            "consistency": {
                "raw_score": consistency.score,
                "weight": self.weights["consistency"],
                "weighted_score": consistency.score * self.weights["consistency"],
            },
            "total_confidence": self.calculate_confidence(
                agent_validation, fact_checking, consistency
            ),
        }

    @staticmethod
    def get_action_description(action: ValidationAction) -> str:
        """
        Aksiyon açıklaması al.

        Args:
            action: Aksiyon

        Returns:
            str: Açıklama
        """
        descriptions = {
            ValidationAction.APPROVE: "Yanıt onaylandı - kullanıcıya gösterilebilir",
            ValidationAction.REVIEW: "Manuel inceleme gerekli - düşük güven",
            ValidationAction.REJECT: "Yanıt reddedildi - kullanıcıya gösterilmemeli",
        }
        return descriptions.get(action, "Bilinmeyen aksiyon")
