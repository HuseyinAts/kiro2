"""
Learning Style Strategy Module
Teknofest 2025 - Eğitim Eylemci Projesi

This module implements learning style-based resource filtering and ranking.

Responsibilities:
- Filter resources by learning style
- Rank resources based on style match
- Calculate style compatibility scores
"""

import logging
from typing import Any

from ..models import LearningResource, LearningStyle

logger = logging.getLogger(__name__)


class LearningStyleStrategy:
    """Learning Style Strategy - Matches resources to learning styles"""

    def __init__(self):
        """Initialize strategy"""
        self.style_weights = {
            LearningStyle.VISUAL: {"video": 1.0, "infographic": 0.9, "diagram": 0.8},
            LearningStyle.AUDITORY: {"audio": 1.0, "podcast": 1.0, "video": 0.7},
            LearningStyle.READING: {"article": 1.0, "book": 1.0, "text": 0.9},
            LearningStyle.KINESTHETIC: {
                "practice": 1.0,
                "quiz": 0.9,
                "interactive": 0.9,
            },
        }
        logger.info("LearningStyleStrategy initialized")

    def filter_by_style(
        self, resources: list[LearningResource], learning_style: LearningStyle
    ) -> list[LearningResource]:
        """Filter resources matching learning style"""
        if learning_style == LearningStyle.MIXED:
            return resources

        return [r for r in resources if r.matches_style(learning_style)]

    def rank_by_style(
        self, resources: list[LearningResource], learning_style: LearningStyle
    ) -> list[LearningResource]:
        """Rank resources by learning style compatibility"""
        scored = [(r, self.calculate_style_match(r, learning_style)) for r in resources]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in scored]

    def calculate_style_match(
        self, resource: LearningResource, learning_style: LearningStyle
    ) -> float:
        """Calculate style match score (0.0-1.0)"""
        if learning_style == LearningStyle.MIXED:
            return 0.7

        weights = self.style_weights.get(learning_style, {})
        return weights.get(resource.resource_type.lower(), 0.5)

    def get_recommendations(
        self, resources: list[LearningResource], learning_style: LearningStyle
    ) -> list[dict[str, Any]]:
        """Get style-based recommendations"""
        return [
            {
                "resource": r,
                "match_score": self.calculate_style_match(r, learning_style),
                "recommendation": "Öğrenme stilinize çok uygun"
                if self.calculate_style_match(r, learning_style) > 0.8
                else "Uygun",
            }
            for r in resources
        ]
