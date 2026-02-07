"""
Ana Soru Uretim Motoru (Orchestrator)
REQ-48.33-48.48: Tum alt sistemleri birlestiren ana sinif

Bu modul soru uretim sisteminin orkestratoru olarak calisir:
- TopicBasedQuestionGenerator ile soru uretir
- DistractorGenerationSystem ile celdiriciler ekler
- MathematicalValidationEngine ile matematik sorularini dogrular
- VisualGenerationEngine ile gorseller uretir
"""

import logging
from typing import Optional

from models.curriculum import SubjectType
from models.question_generation import (
    CognitiveLevel,
    DifficultyLevel,
    GeneratedQuestion,
)

from .distractor import DistractorGenerationSystem
from .generator import TopicBasedQuestionGenerator
from .validator import MathematicalValidationEngine
from .visual import VisualGenerationEngine

logger = logging.getLogger(__name__)


class QuestionGenerationEngine:
    """
    Ana Soru Uretim Motoru
    Tum alt sistemleri birlestiren ana sinif
    """

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLM servisi
        """
        self.topic_generator = TopicBasedQuestionGenerator(llm_service)
        self.distractor_generator = DistractorGenerationSystem(llm_service)
        self.math_validator = MathematicalValidationEngine()
        self.visual_generator = VisualGenerationEngine()

        logger.info("Soru Uretim Motoru baslatildi")

    async def generate_complete_question(
        self,
        subject: SubjectType,
        topic_name: str,
        topic_context: str,
        difficulty_level: DifficultyLevel,
        cognitive_level: CognitiveLevel,
        include_visual: bool = False,
    ) -> Optional[GeneratedQuestion]:
        """
        Tam bir soru uret (soru + celdiriciler + dogrulama + gorsel)

        Returns:
            Tam GeneratedQuestion objesi
        """
        try:
            # 1. Temel soruyu uret
            question = await self.topic_generator.generate_question(
                subject, topic_name, topic_context, difficulty_level, cognitive_level
            )

            if not question:
                return None

            # 2. Celdiricileri uret ve ekle
            distractors = await self.distractor_generator.generate_distractors(
                question.correct_answer,
                question.question_text,
                subject,
                topic_name,
                count=3,
            )

            # Secenekleri guncelle (A: dogru cevap, B-D: celdiriciler)
            question.options = [f"A) {question.correct_answer}"] + [
                d["text"] for d in distractors[:3]
            ]

            # 3. Matematik sorusu ise dogrula
            if subject == SubjectType.MATEMATIK:
                validation = self.math_validator.validate_math_question(
                    question.question_text, question.correct_answer, question.options
                )

                if not validation["valid"]:
                    logger.warning(f"Matematik sorusu gecersiz: {validation['errors']}")
                    question.validation_errors = validation["errors"]
                    question.is_validated = False
                else:
                    question.is_validated = True

            # 4. Gorsel uret (istenirse)
            if include_visual and subject == SubjectType.MATEMATIK:
                visual_path = f"generated_visuals/question_{question.id}.png"
                visual_result = self.visual_generator.generate_function_graph(
                    "x**2", output_path=visual_path  # Ornek fonksiyon
                )

                if visual_result["success"]:
                    question.source_materials.append(visual_path)

            logger.info(f"Tam soru uretildi: {question.id}")
            return question

        except Exception as e:
            logger.error(f"Tam soru uretim hatasi: {e}")
            return None
