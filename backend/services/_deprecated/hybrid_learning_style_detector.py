"""
Hybrid Learning Style Detector
REQ-10.1, REQ-10.2
Teknofest 2025 - Eğitim Eylemci Projesi

64 Benzersiz profil sistemi:
- VARK (4 boyut): Visual, Auditory, Reading, Kinesthetic
- Felder-Silverman (4 boyut): Active/Reflective, Sensing/Intuitive, Visual/Verbal, Sequential/Global
- Türk ZPD Uyarlamaları: Grup öğrenme, Ramazan/sınav dönemleri, MEB Maarif faktörleri
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VARKDimension(Enum):
    """VARK öğrenme stilleri"""

    VISUAL = "Visual"
    AUDITORY = "Auditory"
    READING = "Reading"
    KINESTHETIC = "Kinesthetic"


class FelderDimension(Enum):
    """Felder-Silverman boyutları"""

    ACTIVE = "Active"
    REFLECTIVE = "Reflective"
    SENSING = "Sensing"
    INTUITIVE = "Intuitive"
    VISUAL_FELDER = "Visual"
    VERBAL = "Verbal"
    SEQUENTIAL = "Sequential"
    GLOBAL = "Global"


@dataclass
class LearningStyleProfile:
    """Öğrenme stili profili"""

    vark: str  # V, A, R, or K
    processing: str  # Active or Reflective
    perception: str  # Sensing or Intuitive
    input: str  # Visual or Verbal
    understanding: str  # Sequential or Global

    # Scores
    confidence_score: float  # 0.0-1.0
    vark_scores: dict[str, float]
    felder_scores: dict[str, float]

    # Turkish adaptations
    group_learning_preference: float  # 0.0-1.0
    cultural_factors: dict[str, float]

    def get_profile_code(self) -> str:
        """64 profil kodunu al"""
        return f"{self.vark}-{self.processing}-{self.perception}-{self.understanding}"


class HybridLearningStyleDetector:
    """
    Hibrit Öğrenme Stili Tespit Servisi

    VARK + Felder-Silverman kombinasyonu ile 64 benzersiz profil
    Türk eğitim sistemi ve kültürel faktörler dahil
    """

    def __init__(
        self,
        min_confidence: float = 0.70,
        enable_turkish_zpd: bool = True,
        enable_cultural_factors: bool = True,
    ):
        """
        Initialize detector

        Args:
            min_confidence: Minimum güven skoru (REQ-10: %70)
            enable_turkish_zpd: Türk ZPD uyarlamalarını etkinleştir
            enable_cultural_factors: MEB Maarif kültürel faktörleri
        """
        self.min_confidence = min_confidence
        self.enable_turkish_zpd = enable_turkish_zpd
        self.enable_cultural_factors = enable_cultural_factors

        # VARK question weights
        self.vark_questions = self._init_vark_questions()

        # Felder-Silverman question weights
        self.felder_questions = self._init_felder_questions()

        # Cultural factors (MEB Maarif)
        self.cultural_factors = {
            "ramazan_period": 0.0,  # Ramazan dönemi etkisi
            "exam_period": 0.0,  # Sınav dönemi stresi
            "group_preference": 0.0,  # Grup öğrenme tercihi
            "family_involvement": 0.0,  # Aile katılımı
        }

        logger.info(
            f"Hybrid Learning Style Detector initialized "
            f"(profiles: 64, min_confidence: {min_confidence})"
        )

    def _init_vark_questions(self) -> dict:
        """VARK soru setini başlat"""
        return {
            "prefers_diagrams": {"V": 1.0, "A": 0.0, "R": 0.3, "K": 0.2},
            "prefers_listening": {"V": 0.0, "A": 1.0, "R": 0.2, "K": 0.1},
            "prefers_reading": {"V": 0.2, "A": 0.1, "R": 1.0, "K": 0.0},
            "prefers_practice": {"V": 0.1, "A": 0.0, "R": 0.0, "K": 1.0},
            # Türkçe uyarlamalar
            "watches_educational_videos": {"V": 0.8, "A": 0.7, "R": 0.3, "K": 0.2},
            "listens_to_lectures": {"V": 0.2, "A": 0.9, "R": 0.4, "K": 0.1},
            "reads_textbooks": {"V": 0.3, "A": 0.2, "R": 0.9, "K": 0.1},
            "solves_practice_problems": {"V": 0.2, "A": 0.1, "R": 0.4, "K": 0.9},
        }

    def _init_felder_questions(self) -> dict:
        """Felder-Silverman soru setini başlat"""
        return {
            # Active/Reflective
            "prefers_group_work": {"Active": 0.9, "Reflective": 0.1},
            "thinks_before_acting": {"Active": 0.1, "Reflective": 0.9},
            # Sensing/Intuitive
            "prefers_facts": {"Sensing": 0.9, "Intuitive": 0.2},
            "prefers_theories": {"Sensing": 0.2, "Intuitive": 0.9},
            # Visual/Verbal
            "prefers_charts": {"Visual": 0.9, "Verbal": 0.2},
            "prefers_explanations": {"Visual": 0.2, "Verbal": 0.9},
            # Sequential/Global
            "learns_step_by_step": {"Sequential": 0.9, "Global": 0.2},
            "sees_big_picture": {"Sequential": 0.2, "Global": 0.9},
        }

    def detect(
        self, student_responses: dict[str, float], behavior_data: dict | None = None
    ) -> LearningStyleProfile:
        """
        Öğrenme stilini tespit et

        Args:
            student_responses: Öğrenci anket cevapları (0.0-1.0)
            behavior_data: Davranışsal veriler (opsiyonel)

        Returns:
            LearningStyleProfile: 64 profilden biri
        """
        # Calculate VARK scores
        vark_scores = self._calculate_vark_scores(student_responses)
        dominant_vark = max(vark_scores, key=vark_scores.get)

        # Calculate Felder-Silverman scores
        felder_scores = self._calculate_felder_scores(student_responses)

        # Extract dimensions
        processing = (
            "Active"
            if felder_scores.get("Active", 0) > felder_scores.get("Reflective", 0)
            else "Reflective"
        )
        perception = (
            "Sensing"
            if felder_scores.get("Sensing", 0) > felder_scores.get("Intuitive", 0)
            else "Intuitive"
        )
        input_pref = (
            "Visual"
            if felder_scores.get("Visual", 0) > felder_scores.get("Verbal", 0)
            else "Verbal"
        )
        understanding = (
            "Sequential"
            if felder_scores.get("Sequential", 0) > felder_scores.get("Global", 0)
            else "Global"
        )

        # Calculate confidence
        confidence = self._calculate_confidence(vark_scores, felder_scores)

        # Turkish adaptations
        group_pref = student_responses.get("prefers_group_work", 0.5)
        cultural_factors = self._calculate_cultural_factors(
            student_responses, behavior_data
        )

        profile = LearningStyleProfile(
            vark=dominant_vark,
            processing=processing,
            perception=perception,
            input=input_pref,
            understanding=understanding,
            confidence_score=confidence,
            vark_scores=vark_scores,
            felder_scores=felder_scores,
            group_learning_preference=group_pref,
            cultural_factors=cultural_factors,
        )

        logger.info(
            f"Detected learning style: {profile.get_profile_code()} "
            f"(confidence: {confidence:.2f})"
        )

        return profile

    def _calculate_vark_scores(self, responses: dict[str, float]) -> dict[str, float]:
        """VARK skorlarını hesapla"""
        scores = {"V": 0.0, "A": 0.0, "R": 0.0, "K": 0.0}
        total_weight = 0.0

        for question, response_value in responses.items():
            if question in self.vark_questions:
                weights = self.vark_questions[question]
                for dimension, weight in weights.items():
                    scores[dimension] += response_value * weight
                    total_weight += response_value

        # Normalize
        if total_weight > 0:
            for dim in scores:
                scores[dim] /= total_weight

        return scores

    def _calculate_felder_scores(self, responses: dict[str, float]) -> dict[str, float]:
        """Felder-Silverman skorlarını hesapla"""
        scores = {
            "Active": 0.0,
            "Reflective": 0.0,
            "Sensing": 0.0,
            "Intuitive": 0.0,
            "Visual": 0.0,
            "Verbal": 0.0,
            "Sequential": 0.0,
            "Global": 0.0,
        }
        total_weight = 0.0

        for question, response_value in responses.items():
            if question in self.felder_questions:
                weights = self.felder_questions[question]
                for dimension, weight in weights.items():
                    scores[dimension] += response_value * weight
                    total_weight += response_value

        # Normalize
        if total_weight > 0:
            for dim in scores:
                scores[dim] /= total_weight

        return scores

    def _calculate_confidence(
        self, vark_scores: dict[str, float], felder_scores: dict[str, float]
    ) -> float:
        """Güven skorunu hesapla"""
        # Check if there's a clear dominant style
        vark_max = max(vark_scores.values())
        vark_second_max = sorted(vark_scores.values(), reverse=True)[1]
        vark_confidence = (
            (vark_max - vark_second_max) / vark_max if vark_max > 0 else 0.0
        )

        # Average Felder confidence
        felder_confidence = (
            sum(
                max(felder_scores[d1], felder_scores[d2])
                / (felder_scores[d1] + felder_scores[d2] + 0.001)
                for d1, d2 in [
                    ("Active", "Reflective"),
                    ("Sensing", "Intuitive"),
                    ("Visual", "Verbal"),
                    ("Sequential", "Global"),
                ]
            )
            / 4.0
        )

        # Combined confidence
        confidence = (vark_confidence + felder_confidence) / 2.0

        return min(confidence, 1.0)

    def _calculate_cultural_factors(
        self, responses: dict[str, float], behavior_data: dict | None
    ) -> dict[str, float]:
        """Kültürel faktörleri hesapla (MEB Maarif)"""
        if not self.enable_cultural_factors:
            return {}

        factors = {
            "group_preference": responses.get("prefers_group_work", 0.5),
            "family_involvement": responses.get("family_support", 0.5),
            "ramazan_adaptation": 0.0,
            "exam_stress_level": 0.0,
        }

        if behavior_data:
            # Check for Ramazan period
            if behavior_data.get("is_ramazan_period", False):
                factors["ramazan_adaptation"] = 0.8

            # Check for exam period
            if behavior_data.get("is_exam_period", False):
                factors["exam_stress_level"] = 0.7

        return factors


if __name__ == "__main__":
    # Test
    detector = HybridLearningStyleDetector(
        min_confidence=0.70, enable_turkish_zpd=True, enable_cultural_factors=True
    )

    # Sample student responses
    responses = {
        "prefers_diagrams": 0.8,
        "prefers_listening": 0.6,
        "prefers_reading": 0.3,
        "prefers_practice": 0.7,
        "prefers_group_work": 0.9,
        "thinks_before_acting": 0.4,
        "prefers_facts": 0.7,
        "prefers_charts": 0.8,
        "learns_step_by_step": 0.6,
    }

    profile = detector.detect(responses)
    print(f"Profile: {profile.get_profile_code()}")
    print(f"Confidence: {profile.confidence_score:.2f}")
    print(f"VARK scores: {profile.vark_scores}")
    print(f"Group learning: {profile.group_learning_preference:.2f}")
