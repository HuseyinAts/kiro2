"""
Difficulty Adaptation Strategy Module
Teknofest 2025 - Eğitim Eylemci Projesi

This module implements dynamic difficulty adjustment based on performance.

Responsibilities:
- Adjust difficulty based on student performance
- Detect struggle and mastery patterns
- Calculate next difficulty level
"""

import logging
from typing import Dict, Any, Optional

from ..models import KnowledgeLevel

logger = logging.getLogger(__name__)


class DifficultyAdapter:
    """Difficulty Adapter - Dynamically adjusts difficulty"""

    def __init__(self):
        """Initialize adapter"""
        self.difficulty_order = [
            KnowledgeLevel.BEGINNER,
            KnowledgeLevel.ELEMENTARY,
            KnowledgeLevel.INTERMEDIATE,
            KnowledgeLevel.ADVANCED,
            KnowledgeLevel.EXPERT,
        ]
        logger.info("DifficultyAdapter initialized")

    def calculate_next_difficulty(
        self, current_difficulty: KnowledgeLevel, performance_data: Dict[str, Any]
    ) -> KnowledgeLevel:
        """Calculate next appropriate difficulty level"""
        avg_score = performance_data.get("avg_score", 0)
        consistency = performance_data.get("consistency", 0.5)

        current_index = self.difficulty_order.index(current_difficulty)

        # Struggling: decrease difficulty
        if avg_score < 60:
            new_index = max(0, current_index - 1)
        # Mastering: increase difficulty
        elif avg_score > 85 and consistency > 0.7:
            new_index = min(len(self.difficulty_order) - 1, current_index + 1)
        # Stable: maintain
        else:
            new_index = current_index

        return self.difficulty_order[new_index]

    def detect_struggle(self, performance_data: Dict[str, Any]) -> bool:
        """Detect if student is struggling"""
        avg_score = performance_data.get("avg_score", 0)
        return avg_score < 60

    def detect_mastery(self, performance_data: Dict[str, Any]) -> bool:
        """Detect if student has mastered current level"""
        avg_score = performance_data.get("avg_score", 0)
        consistency = performance_data.get("consistency", 0)
        return avg_score > 85 and consistency > 0.7

    def adapt_difficulty(
        self, current_difficulty: KnowledgeLevel, performance_data: Dict[str, Any]
    ) -> tuple[KnowledgeLevel, str]:
        """Adapt difficulty and return reason"""
        next_difficulty = self.calculate_next_difficulty(
            current_difficulty, performance_data
        )

        if next_difficulty != current_difficulty:
            if self.difficulty_order.index(
                next_difficulty
            ) > self.difficulty_order.index(current_difficulty):
                reason = "Performans yüksek, zorluk artırıldı"
            else:
                reason = "Destek gerekli, zorluk azaltıldı"
        else:
            reason = "Zorluk seviyesi uygun"

        return next_difficulty, reason
