"""
Hızlı Öğrenme Stili Servisi
Performans optimizasyonu için minimal implementasyon
"""
import logging
from typing import Any, Dict

from algorithms.simple_learning_detector import SimpleLearningStyleDetector
from models.learning_style import (
    BehavioralData,
    ContentRecommendation,
    HybridLearningProfile,
)

logger = logging.getLogger(__name__)


class FastLearningStyleService:
    """Hızlı öğrenme stili servisi"""

    def __init__(self):
        self.detector = SimpleLearningStyleDetector()
        self.profiles_cache: Dict[str, HybridLearningProfile] = {}
        logger.info("[CHECK] Hızlı Öğrenme Stili Servisi başlatıldı")

    async def detect_learning_style(self, student_id: str) -> HybridLearningProfile:
        """Hızlı öğrenme stili tespiti"""

        # Cache kontrolü
        if student_id in self.profiles_cache:
            return self.profiles_cache[student_id]

        # Örnek davranışsal veri (hızlı)
        sample_data = [
            BehavioralData(
                student_id=student_id,
                video_watch_time=30.0,
                text_reading_time=20.0,
                interactive_engagement=15.0,
                quiz_completion_rate=0.8,
                note_taking_frequency=5,
                question_asking_frequency=2,
                peer_interaction_count=3,
                help_seeking_behavior=1,
                visual_content_performance=0.7,
                auditory_content_performance=0.6,
                text_content_performance=0.8,
                hands_on_performance=0.9,
            )
        ]

        # Profil tespit et
        profile = await self.detector.detect_hybrid_profile(
            student_id=student_id,
            behavioral_data=sample_data,
            questionnaire_responses=[],
        )

        # Cache'e kaydet
        self.profiles_cache[student_id] = profile

        return profile

    async def generate_content_recommendations(
        self, student_id: str, subject_area: str = "matematik"
    ) -> ContentRecommendation:
        """Hızlı içerik önerileri"""

        profile = await self.detect_learning_style(student_id)

        # Basit öneriler
        recommended_types = ["video_lecture", "interactive_simulation", "quiz_practice"]
        learning_strategies = ["active_learning", "visual_aids", "practice_tests"]
        study_techniques = ["note_taking", "mind_mapping", "group_study"]

        recommendation = ContentRecommendation(
            student_id=student_id,
            hybrid_code=profile.hybrid_code,
            recommended_content_types=recommended_types,
            content_weights={"video_lecture": 0.8, "quiz_practice": 0.7},
            learning_strategies=learning_strategies,
            study_techniques=study_techniques,
            difficulty_adjustment=0.0,
            pace_adjustment=0.0,
            confidence_score=profile.confidence_score,
        )

        return recommendation

    async def get_learning_style_explanation(self, student_id: str) -> Dict[str, Any]:
        """Hızlı açıklama"""
        profile = await self.detect_learning_style(student_id)

        return {
            "hybrid_code": profile.hybrid_code,
            "confidence_level": profile.confidence_level.value,
            "vark_dominant": profile.vark_profile.dominant_vark.value,
            "vark_explanation": f"{profile.vark_profile.dominant_vark.value} öğrenme stili baskın",
            "message": "Hızlı mod - Basitleştirilmiş analiz",
        }
