"""
Soru Uretim Motoru (Question Generation Engine) - BACKWARD COMPATIBILITY WRAPPER
LLM tabanli OSYM formatinda otomatik soru uretimi

REQ-48.33-48.48: Soru Uretim Motoru

REFACTORED (2025-01-25):
Bu dosya artik backward compatibility wrapper olarak calisir.
Gercek implementasyon backend/services/question/ altindadir:

- question/generator.py  -> TopicBasedQuestionGenerator
- question/distractor.py -> DistractorGenerationSystem
- question/validator.py  -> MathematicalValidationEngine
- question/visual.py     -> VisualGenerationEngine
- question/engine.py     -> QuestionGenerationEngine (orchestrator)
- question/models.py     -> Templates ve misconception database

Yeni kodda su sekilde import edin:
    from services.question import QuestionGenerationEngine

Eski kodlar icin bu wrapper hala calisir:
    from services.question_generation_engine import QuestionGenerationEngine
"""

import warnings

# Re-export all classes from new module structure for backward compatibility
from services.question import (
    DistractorGenerationSystem,
    MathematicalValidationEngine,
    QuestionGenerationEngine,
    TopicBasedQuestionGenerator,
    VisualGenerationEngine,
)

# Emit deprecation warning on import
warnings.warn(
    "Importing from 'services.question_generation_engine' is deprecated. "
    "Please use 'from services.question import QuestionGenerationEngine' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "QuestionGenerationEngine",
    "TopicBasedQuestionGenerator",
    "DistractorGenerationSystem",
    "MathematicalValidationEngine",
    "VisualGenerationEngine",
]
