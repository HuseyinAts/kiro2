"""
Response Synthesizer - Multi-Agent Response Merger
REQ-7.6
Teknofest 2025 - KIRO2 YKS Platformu

Birden fazla agent'in yanitlarini birlestirerek
tutarli ve kapsamli bir yanit olusturur.
"""

import logging
from typing import Any, Dict, List

from ..domain_experts.base_domain_agent import DomainResponse

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    """
    Response Synthesizer (REQ-7.6)

    Multi-domain sorularda birden fazla agent'in yanitlarini
    birlestirir ve tutarli bir yanit olusturur.

    Strategies:
    - Sequential merge: Yanitlari sirasiyla birlestir
    - Weighted merge: Confidence skorlarina gore agirlikli birlestir
    """

    def __init__(self, merge_strategy: str = "sequential"):
        """
        ResponseSynthesizer olustur

        Args:
            merge_strategy: "sequential" veya "weighted"
        """
        self.merge_strategy = merge_strategy
        logger.info(f"ResponseSynthesizer initialized with strategy: {merge_strategy}")

    def synthesize(
        self,
        responses: List[DomainResponse],
        question: str,
    ) -> str:
        """
        Yanitlari birlestir

        Args:
            responses: Agent yanitlari
            question: Orijinal soru

        Returns:
            Birlestirilmis yanit string'i
        """
        if not responses:
            return ""

        if len(responses) == 1:
            return responses[0].content

        if self.merge_strategy == "sequential":
            return self._merge_sequential(responses, question)
        elif self.merge_strategy == "weighted":
            return self._merge_weighted(responses, question)
        else:
            return self._merge_sequential(responses, question)

    def _merge_sequential(
        self, responses: List[DomainResponse], question: str
    ) -> str:
        """
        Yanitlari sirasiyla birlestir

        Her agent'in yanitini domain basligi ile ayirarak birlestir.
        """
        parts = []

        for response in responses:
            domain_name = response.domain.value.upper()
            parts.append(f"## {domain_name} Perspektifi\n\n{response.content}")

            # Add step-by-step if available
            if response.step_by_step_solution:
                steps = "\n".join(
                    f"{i+1}. {step}"
                    for i, step in enumerate(response.step_by_step_solution)
                )
                parts.append(f"\n### Adim Adim Cozum\n{steps}")

        # Add summary
        summary = self._generate_summary(responses)
        if summary:
            parts.append(f"\n## Ozet\n{summary}")

        return "\n\n".join(parts)

    def _merge_weighted(
        self, responses: List[DomainResponse], question: str
    ) -> str:
        """
        Yanitlari confidence skorlarina gore agirlikli birlestir

        Yuksek confidence'li yanitlar onde gelir.
        """
        # Sort by confidence
        sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)

        parts = []
        for response in sorted_responses:
            confidence_str = f"({response.confidence:.0%} guven)"
            domain_name = response.domain.value.upper()
            parts.append(f"## {domain_name} {confidence_str}\n\n{response.content}")

        return "\n\n".join(parts)

    def _generate_summary(self, responses: List[DomainResponse]) -> str:
        """
        Yanitlarin ozetini olustur
        """
        if len(responses) < 2:
            return ""

        domains = [r.domain.value for r in responses]
        avg_confidence = sum(r.confidence for r in responses) / len(responses)

        return (
            f"Bu soru {' ve '.join(domains)} alanlarini kapsamaktadir. "
            f"Ortalama guven skoru: {avg_confidence:.0%}"
        )

    def extract_combined_visualizations(
        self, responses: List[DomainResponse]
    ) -> List[Dict[str, Any]]:
        """
        Tum yanitlardan gorselleri topla

        Returns:
            Birlestirilmis gorsel listesi
        """
        visualizations = []
        for response in responses:
            for viz in response.visualizations:
                viz_with_source = dict(viz)
                viz_with_source["source_domain"] = response.domain.value
                visualizations.append(viz_with_source)
        return visualizations

    def extract_combined_references(
        self, responses: List[DomainResponse]
    ) -> List[str]:
        """
        Tum yanitlardan kaynaklari topla

        Returns:
            Birlestirilmis kaynak listesi (unique)
        """
        references = []
        seen = set()
        for response in responses:
            for ref in response.references:
                if ref not in seen:
                    references.append(ref)
                    seen.add(ref)
        return references

    def calculate_combined_confidence(
        self, responses: List[DomainResponse]
    ) -> float:
        """
        Birlesik guven skoru hesapla

        Agirlikli ortalama kullanir.
        """
        if not responses:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for response in responses:
            # Weight by response quality indicators
            weight = 1.0
            if response.step_by_step_solution:
                weight += 0.2
            if response.visualizations:
                weight += 0.1

            weighted_sum += response.confidence * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0
