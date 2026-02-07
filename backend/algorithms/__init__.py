"""
Algoritma modülleri
VARK + Felder-Silverman hibrit öğrenme stili algoritmaları
Türk öğrenci davranışlarına optimize edilmiş FSRS algoritması

Lazy imports kullanılır - database bağlantısı import-time'da gerekli değildir.
"""

__all__ = [
    "HybridLearningStyleDetector",
    "PersonalizedContentRecommender",
    "TurkishOptimizedFSRS",
    "FSRSCard",
    "FSRSSchedule",
    "FSRSGrade",
    "StudentContext",
    "MultiAgentBlackboard",
    "EventType",
    "Priority",
]


def __getattr__(name: str):
    """Lazy import for algorithms - avoids database connection at import time."""
    if name == "HybridLearningStyleDetector":
        from .hybrid_learning_style_detector import HybridLearningStyleDetector
        return HybridLearningStyleDetector

    if name == "PersonalizedContentRecommender":
        from .personalized_content_recommender import PersonalizedContentRecommender
        return PersonalizedContentRecommender

    if name in ("TurkishOptimizedFSRS", "FSRSCard", "FSRSGrade", "FSRSSchedule", "StudentContext"):
        from .turkish_optimized_fsrs import (
            FSRSCard,
            FSRSGrade,
            FSRSSchedule,
            StudentContext,
            TurkishOptimizedFSRS,
        )
        mapping = {
            "TurkishOptimizedFSRS": TurkishOptimizedFSRS,
            "FSRSCard": FSRSCard,
            "FSRSGrade": FSRSGrade,
            "FSRSSchedule": FSRSSchedule,
            "StudentContext": StudentContext,
        }
        return mapping[name]

    if name in ("MultiAgentBlackboard", "EventType", "Priority"):
        from .multi_agent_blackboard import (
            MultiAgentBlackboard,
            EventType,
            Priority,
        )
        mapping = {
            "MultiAgentBlackboard": MultiAgentBlackboard,
            "EventType": EventType,
            "Priority": Priority,
        }
        return mapping[name]

    raise AttributeError(f"module 'algorithms' has no attribute '{name}'")
