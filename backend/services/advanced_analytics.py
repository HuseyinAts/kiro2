# Advanced Analytics Dashboard

from typing import List
from dataclasses import dataclass
import numpy as np


@dataclass
class StudentAnalytics:
    student_id: int
    overall_accuracy: float
    questions_attempted: int
    strong_topics: List[str]
    weak_topics: List[str]
    predicted_yks_score: float
    engagement_score: float


class AdvancedAnalyticsEngine:
    def calculate_student_analytics(self, student_id: int, performance_data: List[dict]) -> StudentAnalytics:
        total = len(performance_data)
        correct = sum(1 for d in performance_data if d.get("is_correct", False))
        accuracy = correct / total if total > 0 else 0.0
        
        predicted_yks = 300 + (accuracy - 0.5) * 400
        predicted_yks = np.clip(predicted_yks, 100, 500)
        
        return StudentAnalytics(
            student_id=student_id,
            overall_accuracy=accuracy,
            questions_attempted=total,
            strong_topics=[],
            weak_topics=[],
            predicted_yks_score=predicted_yks,
            engagement_score=0.75
        )
    
    def generate_dashboard_summary(self, student_id: int) -> dict:
        return {
            "student_id": student_id,
            "performance_overview": {
                "accuracy": "75.0%",
                "questions_attempted": 100
            },
            "predictions": {
                "yks_score": 380,
                "percentile": 85
            },
            "recommendations": [
                "Great progress! Continue with advanced topics"
            ]
        }
