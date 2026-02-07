"""
Final Quality Gate Agent (Stage 6)
Tüm kalite kontrollerinin final onayı

Requirements (REQ-6.x):
- REQ-6.1: Tüm pipeline aşamaları tamamlandığında final review yapar
- REQ-6.2: Tüm önceki agent skorlarını toplar
- REQ-6.3: Ağırlıklı ortalama kullanır (Content 25%, Difficulty 20%, Distractor 20%, Compliance 20%, Language 15%)
- REQ-6.4: Skor >= 85% olduğunda soruyu onaylar
- REQ-6.5: Skor 70-85% arasında olduğunda manuel review önerir
- REQ-6.6: Skor < 70% olduğunda soruyu reddeder ve iyileştirme önerileri sunar
"""

import time
from typing import Any, Dict, List, Optional

from ..stage_base import BasePipelineStage, StageInput, StageOutput


class QualityGateAgent(BasePipelineStage):
    """
    Final Kalite Geçidi Agent'ı (Aşama 6)

    Tüm aşama skorlarını toplar ve final karar verir.
    """

    STAGE_NAME = "quality_gate"

    # Stage ağırlıkları (design.md'den)
    STAGE_WEIGHTS = {
        "content_generator": 0.25,
        "difficulty_calibration": 0.20,
        "distractor_generator": 0.20,
        "osym_compliance": 0.20,
        "language_qa": 0.15
    }

    # Karar eşikleri
    APPROVAL_THRESHOLD = 0.85  # >= 85% -> approved
    REVIEW_THRESHOLD = 0.70   # >= 70% -> review
    # < 70% -> rejected

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Quality Gate Agent başlat

        Args:
            llm_client: LLM istemcisi (opsiyonel)
            config: Ek konfigürasyon
        """
        super().__init__(self.STAGE_NAME, llm_client, config)

    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Final kalite değerlendirmesi yap

        Args:
            input_data: Pipeline girişi (önceki skorları içerir)

        Returns:
            StageOutput: Final karar ve öneri
        """
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []

        try:
            question_data = input_data.question_data
            previous_scores = input_data.previous_scores

            # 1. Tüm skorları topla (REQ-6.1, REQ-6.2)
            stage_scores = self._collect_stage_scores(previous_scores, question_data)

            if not stage_scores:
                return self._create_error_output(
                    "Önceki aşama skorları bulunamadı",
                    input_data,
                    time.time() - start_time
                )

            # 2. Ağırlıklı ortalama hesapla (REQ-6.3)
            final_score = self._calculate_weighted_score(stage_scores)

            # 3. Karar ver (REQ-6.4, REQ-6.5, REQ-6.6)
            decision, decision_reason = self._make_decision(final_score)

            # 4. İyileştirme önerileri
            if decision != "approved":
                suggestions = self._generate_improvement_suggestions(
                    stage_scores, decision
                )

            # 5. Başarısız aşamaları belirle
            failed_stages = [
                stage for stage, score in stage_scores.items()
                if score < 0.7
            ]
            if failed_stages:
                warnings.append(f"Düşük skorlu aşamalar: {', '.join(failed_stages)}")

            # Status belirleme
            status = decision  # approved, review, rejected

            # Output verisi
            output_data = {
                **question_data,
                "final_score": final_score,
                "decision": decision,
                "decision_reason": decision_reason,
                "status": status,
                "stage_scores": stage_scores
            }

            return StageOutput(
                question_data=output_data,
                score=final_score,
                passed=decision == "approved",
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "stage": self.STAGE_NAME,
                    "final_score": final_score,
                    "decision": decision,
                    "stage_scores": stage_scores,
                    "weights_used": self.STAGE_WEIGHTS
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_output(
                f"Kalite değerlendirme hatası: {str(e)}",
                input_data,
                time.time() - start_time
            )

    def get_stage_weight(self) -> float:
        """Quality Gate kendi skoru için ağırlık döndürmez"""
        return 0.0

    def _collect_stage_scores(
        self,
        previous_scores: Dict[str, float],
        question_data: Dict
    ) -> Dict[str, float]:
        """
        Tüm aşama skorlarını topla

        Args:
            previous_scores: Önceki aşama skorları
            question_data: Soru verisi (alternatif skorlar için)

        Returns:
            Dict[str, float]: Stage -> skor mapping
        """
        scores = {}

        # previous_scores'dan al
        for stage_name, weight in self.STAGE_WEIGHTS.items():
            if stage_name in previous_scores:
                scores[stage_name] = previous_scores[stage_name]
            elif f"{stage_name}_score" in question_data:
                scores[stage_name] = question_data[f"{stage_name}_score"]

        # Alternatif alan adları
        alt_names = {
            "content_generator": ["content_score"],
            "difficulty_calibration": ["difficulty_score", "zpd_score"],
            "distractor_generator": ["distractor_score"],
            "osym_compliance": ["compliance_score", "osym_score"],
            "language_qa": ["language_score", "readability_score"]
        }

        for stage_name, alt_list in alt_names.items():
            if stage_name not in scores:
                for alt in alt_list:
                    if alt in question_data:
                        scores[stage_name] = question_data[alt]
                        break

        return scores

    def _calculate_weighted_score(self, stage_scores: Dict[str, float]) -> float:
        """
        Ağırlıklı ortalama hesapla

        Formula: sum(score * weight) / sum(weights)

        Args:
            stage_scores: Aşama skorları

        Returns:
            float: Final skor (0-1)
        """
        total_score = 0.0
        total_weight = 0.0

        for stage_name, score in stage_scores.items():
            weight = self.STAGE_WEIGHTS.get(stage_name, 0.0)
            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(total_score / total_weight, 4)

    def _make_decision(self, final_score: float) -> tuple:
        """
        Final karar ver

        Args:
            final_score: Final skor

        Returns:
            tuple: (decision, reason)
        """
        if final_score >= self.APPROVAL_THRESHOLD:
            return "approved", f"Skor {final_score:.1%} >= {self.APPROVAL_THRESHOLD:.0%}"
        elif final_score >= self.REVIEW_THRESHOLD:
            return "review", f"Skor {final_score:.1%} ({self.REVIEW_THRESHOLD:.0%}-{self.APPROVAL_THRESHOLD:.0%} arası)"
        else:
            return "rejected", f"Skor {final_score:.1%} < {self.REVIEW_THRESHOLD:.0%}"

    def _generate_improvement_suggestions(
        self,
        stage_scores: Dict[str, float],
        decision: str
    ) -> List[str]:
        """
        İyileştirme önerileri üret

        Args:
            stage_scores: Aşama skorları
            decision: Karar

        Returns:
            List[str]: Öneriler
        """
        suggestions = []

        # En düşük skorlu aşamaları bul
        sorted_stages = sorted(stage_scores.items(), key=lambda x: x[1])

        stage_suggestions = {
            "content_generator": [
                "Kazanımı daha net ifade edin",
                "Günlük hayat bağlamı ekleyin",
                "Türkçe anlaşılırlığı artırın"
            ],
            "difficulty_calibration": [
                "Soru zorluğunu hedef seviyeye ayarlayın",
                "ZPD aralığına uygun hale getirin",
                "IRT parametrelerini kontrol edin"
            ],
            "distractor_generator": [
                "Çeldiricileri daha mantıklı yapın",
                "Yaygın öğrenci hatalarını kullanın",
                "Seçenek uzunluklarını dengeleyin"
            ],
            "osym_compliance": [
                "ÖSYM formatına uygun hale getirin",
                "Soru uzunluğunu kontrol edin",
                "Seçenek yapısını düzeltin"
            ],
            "language_qa": [
                "Yazım hatalarını düzeltin",
                "Cümle yapısını basitleştirin",
                "Okunabilirliği artırın"
            ]
        }

        # En düşük 2 aşama için öneri
        for stage_name, score in sorted_stages[:2]:
            if score < 0.8 and stage_name in stage_suggestions:
                suggestions.extend(stage_suggestions[stage_name][:2])

        # Genel öneriler
        if decision == "rejected":
            suggestions.append("Soruyu baştan gözden geçirin")
        elif decision == "review":
            suggestions.append("Uzman incelemesi için işaretlendi")

        return suggestions[:5]  # Max 5 öneri

    def _create_error_output(
        self,
        error_message: str,
        input_data: StageInput,
        execution_time: float
    ) -> StageOutput:
        """Hata output'u oluştur"""
        return StageOutput(
            question_data={
                **input_data.question_data,
                "status": "rejected",
                "decision": "rejected"
            },
            score=0.0,
            passed=False,
            errors=[error_message],
            warnings=[],
            suggestions=["Pipeline'ı tekrar çalıştırın"],
            metadata={"stage": self.STAGE_NAME, "error": True},
            execution_time=execution_time
        )
