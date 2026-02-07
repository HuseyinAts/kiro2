# LECTOR Algorithm - LLM-Enhanced Concept-based Test-Oriented Repetition
# Target: 90.2% success rate

import numpy as np
from typing import Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

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
    semantic_understanding_score: float = 0.0

@dataclass
class StudentConceptProfile:
    student_id: str
    concept_id: str
    mastery_level: ConceptMasteryLevel = ConceptMasteryLevel.UNKNOWN
    total_reviews: int = 0
    successful_reviews: int = 0
    avg_performance: float = 0.0
    current_interval: float = 1.0
    learning_velocity: float = 1.0

class LECTORScheduler:
    def __init__(self, min_interval: float = 1.0, max_interval: float = 365.0):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.target_retention = 0.90
    
    def calculate_next_review(
        self,
        profile: StudentConceptProfile,
        recent_review: ConceptReview,
        concept: Concept
    ) -> Tuple[datetime, float]:
        base_interval = self._calculate_base_interval(profile, recent_review)
        difficulty_factor = 1.0 + (concept.difficulty_level - 0.5) * 0.4
        semantic_factor = self._calculate_semantic_factor(recent_review)
        
        final_interval = base_interval * difficulty_factor * semantic_factor
        final_interval = np.clip(final_interval, self.min_interval, self.max_interval)
        
        next_review = datetime.now() + timedelta(days=final_interval)
        confidence = 0.85
        
        return next_review, confidence
    
    def _calculate_base_interval(self, profile: StudentConceptProfile, review: ConceptReview) -> float:
        performance = review.performance_score
        current_interval = profile.current_interval
        
        if performance >= 0.8:
            return current_interval * (1.0 + performance * 0.5)
        elif performance >= 0.6:
            return current_interval * 1.1
        else:
            return 1.0
    
    def _calculate_semantic_factor(self, review: ConceptReview) -> float:
        semantic_score = review.semantic_understanding_score
        
        if semantic_score >= 0.85:
            return 1.3
        elif semantic_score >= 0.70:
            return 1.1
        else:
            return 0.8
