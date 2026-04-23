"""
ExamAgent Yanıt Doğrulayıcı

Bu modül, ExamAgent'ın yaptığı değerlendirmeleri doğrular.

Doğrulamalar:
1. Puanlama tutarlılığı
2. Doğru/yanlış sayı kontrolü
3. İstatistik hesaplama doğruluğu
4. Zayıf alan tespiti doğruluğu
5. Öneri uygunluğu

Requirements: REQ-3.1 - REQ-3.6
"""

import logging
import statistics
from typing import Any

from backend.validators.base_response_validator import (
    AgentResponse,
    BaseResponseValidator,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# Zayıf alan eşik değeri
WEAK_AREA_THRESHOLD = 0.60  # %60'ın altı zayıf


class ExamAgentValidator(BaseResponseValidator):
    """
    ExamAgent yanıtlarını doğrulayan validator.

    Sınav değerlendirmelerinin:
    - Puanlama kriterlerinin tutarlı uygulandığını
    - Matematiksel hesaplamaların doğru olduğunu
    - İstatistiklerin doğru hesaplandığını
    - Zayıf alan tespitlerinin veriye dayalı olduğunu
    - Önerilerin öğrenci profiline uygun olduğunu

    kontrol eder.
    """

    # Scoring tutarlılığı için maksimum standart sapma
    MAX_SCORING_STD_DEV = 10.0

    def __init__(self, weight: float = 0.30):
        """
        Args:
            weight: Validator ağırlığı (default: 0.30)
        """
        super().__init__(weight)

    def get_validator_name(self) -> str:
        return "ExamAgentValidator"

    async def validate(self, response: AgentResponse) -> ValidationResult:
        """
        ExamAgent yanıtını doğrula.

        Args:
            response: Doğrulanacak agent yanıtı

        Returns:
            ValidationResult: Doğrulama sonucu
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []
        score = 1.0

        evaluation = response.response_data.get("evaluation", {})

        if not evaluation:
            # response_text'ten çıkarmaya çalış
            evaluation = self._extract_evaluation_from_text(
                response.response_text
            )

        # Context bilgilerini al
        context = response.context or {}
        student_profile = context.get("student_profile", {})

        # 1. Puanlama tutarlılığı kontrolü (REQ-3.1)
        scoring_result = self._check_scoring_consistency(evaluation)
        if not scoring_result["is_consistent"]:
            errors.append(
                f"Puanlama kriterleri tutarsız: {scoring_result['detail']}"
            )
            score -= 0.3
            suggestions.append(
                "Aynı zorluk seviyesindeki soruları tutarlı puanlayın"
            )

        # 2. Matematiksel hesaplama kontrolü (REQ-3.2)
        math_result = self._verify_math_calculations(evaluation)
        if not math_result["is_correct"]:
            for error in math_result["errors"]:
                errors.append(error)
            score -= 0.4
            suggestions.append("Doğru/yanlış sayılarını tekrar hesaplayın")

        # 3. İstatistiksel hesaplama kontrolü (REQ-3.3)
        stats_result = self._verify_statistics(evaluation)
        if not stats_result["is_correct"]:
            for error in stats_result["errors"]:
                errors.append(error)
            score -= 0.2
            suggestions.append("İstatistiksel hesaplamaları gözden geçirin")

        # 4. Zayıf alan tespiti doğruluğu (REQ-3.4)
        weak_area_result = self._validate_weak_area_detection(evaluation)
        if not weak_area_result["is_valid"]:
            for warning in weak_area_result["warnings"]:
                warnings.append(warning)
            score -= 0.1 * len(weak_area_result["warnings"])
            suggestions.append(
                "Zayıf alan tespitlerini performans verileriyle destekleyin"
            )

        # 5. Öneri uygunluğu kontrolü (REQ-3.5)
        rec_result = self._check_recommendation_appropriateness(
            evaluation, student_profile
        )
        if not rec_result["is_appropriate"]:
            for warning in rec_result["warnings"]:
                warnings.append(warning)
            score -= 0.05 * len(rec_result["warnings"])
            suggestions.append(
                "Önerileri öğrenci profili ve zayıf alanlara göre özelleştirin"
            )

        # Skoru sınırla
        score = max(0.0, min(1.0, score))

        # Metadata oluştur
        metadata = {
            "validator": self.get_validator_name(),
            "total_questions": evaluation.get("total_questions", 0),
            "correct_count": evaluation.get("correct_count", 0),
            "wrong_count": evaluation.get("wrong_count", 0),
            "weak_areas_count": len(evaluation.get("weak_areas", [])),
            "recommendations_count": len(evaluation.get("recommendations", [])),
        }

        return ValidationResult(
            is_valid=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata=metadata,
        )

    def _extract_evaluation_from_text(
        self, text: str
    ) -> dict[str, Any]:
        """
        Metin yanıtından değerlendirme bilgilerini çıkar.

        Args:
            text: Agent yanıt metni

        Returns:
            Dict: Çıkarılan değerlendirme verileri
        """
        import re

        evaluation = {
            "total_questions": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "statistics": {},
            "weak_areas": [],
            "recommendations": [],
            "question_results": [],
        }

        text_lower = text.lower()

        # Sayıları çıkar
        def extract_number(pattern: str) -> int | None:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))
            return None

        # Toplam soru sayısı
        total = extract_number(r'toplam[:\s]+(\d+)')
        if total:
            evaluation["total_questions"] = total

        # Doğru sayısı
        correct = extract_number(r'doğru[:\s]+(\d+)')
        if correct:
            evaluation["correct_count"] = correct

        # Yanlış sayısı
        wrong = extract_number(r'yanlış[:\s]+(\d+)')
        if wrong:
            evaluation["wrong_count"] = wrong

        # Başarı yüzdesi
        percentage = extract_number(r'başarı[:\s]+%?(\d+)')
        if percentage:
            evaluation["statistics"]["success_percentage"] = percentage

        # Zayıf alanları çıkar
        weak_patterns = [
            r'zayıf[:\s]+([^\n,]+)',
            r'geliştirilmesi gereken[:\s]+([^\n,]+)',
        ]
        for pattern in weak_patterns:
            matches = re.findall(pattern, text_lower)
            evaluation["weak_areas"].extend([m.strip() for m in matches])

        return evaluation

    def _check_scoring_consistency(
        self, evaluation: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Puanlama tutarlılığını kontrol et.

        Args:
            evaluation: Değerlendirme verileri

        Returns:
            Dict: Tutarlılık sonucu
        """
        question_results = evaluation.get("question_results", [])

        if len(question_results) < 2:
            return {
                "is_consistent": True,
                "detail": "Yeterli veri yok",
            }

        # Zorluk seviyesine göre grupla
        by_difficulty: dict[str, list[dict]] = {}

        for result in question_results:
            difficulty = result.get("difficulty", "orta")
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = []
            by_difficulty[difficulty].append(result)

        # Her zorluk grubu için tutarlılık kontrol et
        inconsistencies = []

        for difficulty, results in by_difficulty.items():
            if len(results) < 2:
                continue

            # Doğru cevapların puanlarını al
            correct_scores = [
                r.get("score", r.get("points", 0))
                for r in results
                if r.get("is_correct", False)
            ]

            if len(correct_scores) >= 2:
                try:
                    std_dev = statistics.stdev(correct_scores)
                    if std_dev > self.MAX_SCORING_STD_DEV:
                        inconsistencies.append(
                            f"{difficulty} zorluk: std_dev={std_dev:.1f}"
                        )
                except statistics.StatisticsError:
                    pass

        if inconsistencies:
            return {
                "is_consistent": False,
                "detail": ", ".join(inconsistencies),
            }

        return {
            "is_consistent": True,
            "detail": "Puanlama tutarlı",
        }

    def _verify_math_calculations(
        self, evaluation: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Matematiksel hesaplamaları doğrula.

        Args:
            evaluation: Değerlendirme verileri

        Returns:
            Dict: Doğrulama sonucu
        """
        errors = []

        correct_count = evaluation.get("correct_count", 0)
        wrong_count = evaluation.get("wrong_count", 0)
        total_questions = evaluation.get("total_questions", 0)
        empty_count = evaluation.get("empty_count", 0)

        # Toplam kontrol
        calculated_total = correct_count + wrong_count + empty_count

        if total_questions > 0:
            if calculated_total != total_questions:
                # Empty olmadan kontrol
                if correct_count + wrong_count != total_questions:
                    errors.append(
                        f"Doğru ({correct_count}) + Yanlış ({wrong_count}) = "
                        f"{correct_count + wrong_count}, "
                        f"beklenen toplam: {total_questions}"
                    )

        # question_results ile doğrula
        question_results = evaluation.get("question_results", [])
        if question_results:
            actual_correct = sum(
                1 for r in question_results
                if r.get("is_correct", False)
            )
            actual_wrong = sum(
                1 for r in question_results
                if not r.get("is_correct", True) and not r.get("is_empty", False)
            )

            if actual_correct != correct_count and correct_count > 0:
                errors.append(
                    f"Bildirilen doğru sayısı ({correct_count}) "
                    f"hesaplanan değerle uyuşmuyor ({actual_correct})"
                )

            if actual_wrong != wrong_count and wrong_count > 0:
                errors.append(
                    f"Bildirilen yanlış sayısı ({wrong_count}) "
                    f"hesaplanan değerle uyuşmuyor ({actual_wrong})"
                )

        return {
            "is_correct": len(errors) == 0,
            "errors": errors,
        }

    def _verify_statistics(
        self, evaluation: dict[str, Any]
    ) -> dict[str, Any]:
        """
        İstatistiksel hesaplamaları doğrula.

        Args:
            evaluation: Değerlendirme verileri

        Returns:
            Dict: Doğrulama sonucu
        """
        errors = []
        statistics_data = evaluation.get("statistics", {})
        question_results = evaluation.get("question_results", [])

        # Ortalama kontrolü
        if question_results:
            scores = [
                r.get("score", r.get("points", 0))
                for r in question_results
                if isinstance(r.get("score", r.get("points")), (int, float))
            ]

            if scores:
                calculated_avg = sum(scores) / len(scores)
                reported_avg = statistics_data.get("average_score", 0)

                if reported_avg > 0:
                    if abs(calculated_avg - reported_avg) > 0.5:
                        errors.append(
                            f"Ortalama hatalı: bildirilen={reported_avg:.2f}, "
                            f"hesaplanan={calculated_avg:.2f}"
                        )

                # Medyan kontrolü
                reported_median = statistics_data.get("median_score")
                if reported_median is not None and len(scores) >= 3:
                    calculated_median = statistics.median(scores)
                    if abs(calculated_median - reported_median) > 1:
                        errors.append(
                            f"Medyan hatalı: bildirilen={reported_median:.2f}, "
                            f"hesaplanan={calculated_median:.2f}"
                        )

        # Başarı yüzdesi kontrolü
        correct_count = evaluation.get("correct_count", 0)
        total_questions = evaluation.get("total_questions", 0)

        if total_questions > 0:
            calculated_percentage = (correct_count / total_questions) * 100
            reported_percentage = statistics_data.get(
                "success_percentage",
                statistics_data.get("score_percentage", 0)
            )

            if reported_percentage > 0:
                if abs(calculated_percentage - reported_percentage) > 1:
                    errors.append(
                        f"Başarı yüzdesi hatalı: "
                        f"bildirilen=%{reported_percentage:.1f}, "
                        f"hesaplanan=%{calculated_percentage:.1f}"
                    )

        return {
            "is_correct": len(errors) == 0,
            "errors": errors,
        }

    def _validate_weak_area_detection(
        self, evaluation: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Zayıf alan tespitlerini doğrula.

        Args:
            evaluation: Değerlendirme verileri

        Returns:
            Dict: Doğrulama sonucu
        """
        warnings = []
        weak_areas = evaluation.get("weak_areas", [])
        question_results = evaluation.get("question_results", [])

        if not weak_areas or not question_results:
            return {"is_valid": True, "warnings": []}

        # Her zayıf alan için performans verisi kontrol et
        for area in weak_areas:
            # Bu alandaki soruları bul
            area_lower = area.lower() if isinstance(area, str) else str(area).lower()

            area_questions = [
                q for q in question_results
                if area_lower in str(q.get("topic", "")).lower()
                or area_lower in str(q.get("subject", "")).lower()
                or area_lower in str(q.get("category", "")).lower()
            ]

            if not area_questions:
                warnings.append(
                    f"Zayıf alan '{area}' için soru verisi bulunamadı"
                )
                continue

            # Başarı oranını hesapla
            correct_in_area = sum(
                1 for q in area_questions
                if q.get("is_correct", False)
            )
            success_rate = correct_in_area / len(area_questions)

            # Gerçekten zayıf mı kontrol et
            if success_rate >= WEAK_AREA_THRESHOLD:
                warnings.append(
                    f"'{area}' alanı zayıf olarak işaretlenmiş "
                    f"ama başarı oranı %{success_rate*100:.0f}"
                )

        return {
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
        }

    def _check_recommendation_appropriateness(
        self,
        evaluation: dict[str, Any],
        student_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Önerilerin öğrenci profiline uygunluğunu kontrol et.

        Args:
            evaluation: Değerlendirme verileri
            student_profile: Öğrenci profili

        Returns:
            Dict: Uygunluk sonucu
        """
        warnings = []
        recommendations = evaluation.get("recommendations", [])

        if not recommendations:
            return {"is_appropriate": True, "warnings": []}

        # Öğrenci seviyesi
        student_level = student_profile.get("level", "orta")
        grade_level = student_profile.get("grade", 9)

        for rec in recommendations:
            rec_text = str(rec).lower() if isinstance(rec, str) else ""

            # Seviye uygunluğu kontrolü
            if "ileri" in rec_text and student_level == "başlangıç":
                warnings.append(
                    f"Öneri başlangıç seviyesi için çok ileri: {rec}"
                )

            # Zayıf alanlarla ilişki kontrolü (soft check)
            # Bu kural çok sıkı olabilir, bu yüzden sadece bilgi amaçlı

            # Sınıf seviyesi uygunluğu
            level_keywords = {
                "lise": range(9, 13),
                "ortaokul": range(5, 9),
                "ilkokul": range(1, 5),
                "üniversite": range(13, 20),
            }

            for keyword, grades in level_keywords.items():
                if keyword in rec_text and grade_level not in grades:
                    warnings.append(
                        f"Öneri sınıf seviyesine uygun değil: {rec}"
                    )
                    break

        return {
            "is_appropriate": len(warnings) == 0,
            "warnings": warnings,
        }
