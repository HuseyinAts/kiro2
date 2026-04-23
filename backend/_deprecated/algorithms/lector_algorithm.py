# LECTOR Algorithm - LLM-Enhanced Spaced Repetition
# Target: 90.2% success rate

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class ConceptMasteryLevel(Enum):
    UNKNOWN = 0
    LEARNING = 1
    FAMILIAR = 2
    PROFICIENT = 3
    MASTERED = 4


@dataclass
class Concept:
    concept_id: str
    name: str
    description: str
    subject: str
    difficulty_level: float = 0.5


@dataclass
class ConceptReview:
    concept_id: str
    student_id: str
    review_date: datetime
    performance_score: float
    response_time: float
    mastery_level: ConceptMasteryLevel
    semantic_understanding_score: float = 0.0


@dataclass
class StudentConceptProfile:
    student_id: str
    concept_id: str
    mastery_level: ConceptMasteryLevel = ConceptMasteryLevel.UNKNOWN
    total_reviews: int = 0
    successful_reviews: int = 0
    avg_performance: float = 0.0
    avg_semantic_score: float = 0.0
    current_interval: float = 1.0
    learning_velocity: float = 1.0
    retention_rate: float = 0.9


class LECTORScheduler:
    """LECTOR Scheduling Algorithm - LLM-enhanced spaced repetition"""

    def __init__(
        self,
        llm_service=None,
        berturk_service=None,
        min_interval: float = 1.0,
        max_interval: float = 365.0,
        target_retention: float = 0.90
    ):
        self.llm_service = llm_service
        self.berturk_service = berturk_service
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.target_retention = target_retention

    def calculate_next_review(
        self,
        profile: StudentConceptProfile,
        recent_review: ConceptReview,
        concept: Concept
    ) -> tuple[datetime, float]:
        base_interval = self._calculate_base_interval(profile, recent_review)
        difficulty_factor = 1.0 + (concept.difficulty_level - 0.5) * 0.4
        semantic_factor = self._calculate_semantic_factor(recent_review)

        final_interval = base_interval * difficulty_factor * semantic_factor * profile.learning_velocity
        final_interval = np.clip(final_interval, self.min_interval, self.max_interval)

        next_review = datetime.now() + timedelta(days=final_interval)
        confidence = self._calculate_confidence(profile, recent_review)

        return next_review, confidence

    def _calculate_base_interval(self, profile: StudentConceptProfile, review: ConceptReview) -> float:
        performance = review.performance_score
        current_interval = profile.current_interval

        if performance >= 0.8:
            return current_interval * (1.0 + performance * 0.5)
        if performance >= 0.6:
            return current_interval * 1.1
        return 1.0

    def _calculate_semantic_factor(self, review: ConceptReview) -> float:
        semantic_score = review.semantic_understanding_score

        if semantic_score >= 0.85:
            return 1.3
        if semantic_score >= 0.70:
            return 1.1
        return 0.8

    def _calculate_confidence(self, profile: StudentConceptProfile, review: ConceptReview) -> float:
        review_factor = min(profile.total_reviews / 10.0, 1.0)
        consistency = 1.0 - abs(review.performance_score - profile.avg_performance)
        return np.clip((review_factor + consistency) / 2, 0.0, 1.0)

    async def assess_semantic_understanding(
        self, student_response: str, correct_answer: str, concept: Concept
    ) -> float:
        if not self.llm_service:
            return 0.5

        try:
            prompt = (
                f"Evaluate semantic understanding (0-1): {concept.name}\n"
                f"Correct: {correct_answer}\n"
                f"Student: {student_response}"
            )
            response = await self.llm_service.generate(prompt)
            return np.clip(float(response.strip()), 0.0, 1.0)
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Semantic evaluation failed: {e}")
            return 0.5
