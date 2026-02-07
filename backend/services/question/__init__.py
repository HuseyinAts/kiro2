"""
Soru Uretim Modulu (Question Generation Module)
REQ-48.33-48.48: OSYM formatinda otomatik soru uretimi

Bu modul asagidaki bilesenleri icerir:
- TopicBasedQuestionGenerator: Konu bazli soru uretimi
- DistractorGenerationSystem: Celdirici uretim sistemi
- MathematicalValidationEngine: SymPy ile matematiksel dogrulama
- VisualGenerationEngine: Matplotlib/Plotly gorsel uretimi
- QuestionGenerationEngine: Ana orkestrator

Kullanim:
    from services.question import QuestionGenerationEngine

    engine = QuestionGenerationEngine(llm_service=my_llm)
    question = await engine.generate_complete_question(
        subject=SubjectType.MATEMATIK,
        topic_name="Denklemler",
        topic_context="Birinci derece denklemler",
        difficulty_level=DifficultyLevel.ORTA,
        cognitive_level=CognitiveLevel.ANLAMA,
    )
"""

from .distractor import DistractorGenerationSystem
from .engine import QuestionGenerationEngine
from .generator import TopicBasedQuestionGenerator
from .models import (
    MISCONCEPTION_DATABASE,
    QUESTION_TEMPLATES,
    get_misconceptions,
    get_question_templates,
)
from .validator import MathematicalValidationEngine
from .visual import VisualGenerationEngine

__all__ = [
    # Main orchestrator
    "QuestionGenerationEngine",
    # Sub-components
    "TopicBasedQuestionGenerator",
    "DistractorGenerationSystem",
    "MathematicalValidationEngine",
    "VisualGenerationEngine",
    # Data/templates
    "QUESTION_TEMPLATES",
    "MISCONCEPTION_DATABASE",
    "get_question_templates",
    "get_misconceptions",
]
