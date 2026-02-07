"""
OSYM Question Generator Service
Main engine for generating OSYM questions using Multi-LLM ensemble

Author: KIRO AI Team
Date: 2025-10-19
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum

from models.osym_question import (
    OSYMQuestion,
    QuestionGenerationBatch,
)
from models.question_generation import DifficultyLevel
from services.llm.ensemble_manager import MultiLLMEnsembleManager
from services.llm.multi_llm_config import LLMProvider
from services.llm.turkish_optimizer import TurkishPromptOptimizer
from services.psychometrics.irt_model import IRTModel
from services.psychometrics.calibration import AdaptiveCalibrator
from services.quality.osym_quality_scorer import OSYMQualityScorer
from services.quality.metrics import QualityMetrics


# QuestionStatus enum for question generation status
class QuestionStatus(str, Enum):
    """Question status enumeration"""
    PENDING_REVIEW = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OSYMQuestionGenerator:
    """
    Main OSYM Question Generator

    Orchestrates:
    - Multi-LLM question generation
    - IRT parameter estimation
    - Quality scoring
    - Database persistence
    """

    def __init__(self, ensemble_manager: MultiLLMEnsembleManager, db_session=None):
        """
        Initialize question generator

        Args:
            ensemble_manager: Multi-LLM ensemble manager
            db_session: Database session (optional)
        """
        self.ensemble = ensemble_manager
        self.db = db_session
        self.quality_scorer = OSYMQualityScorer()
        self.quality_metrics = QualityMetrics()

        # Initialize Turkish prompt optimizer
        self.optimizer = TurkishPromptOptimizer(
            common_words_path="backend/data/turkish_common_words_1000.json"
        )

    async def generate_question(
        self,
        topic: str,
        subtopic: str,
        exam_type: str,
        subject: str,
        difficulty: float,
        bloom_level: int,
        generation_method: str = "ensemble",
        save_to_db: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a single OSYM question

        Args:
            topic: Main topic (e.g., "Matematik")
            subtopic: Subtopic (e.g., "Türev Alma Kuralları")
            exam_type: TYT/AYT/YDT
            subject: Subject area
            difficulty: Difficulty level 0.0-1.0
            bloom_level: Bloom taxonomy level 1-6
            generation_method: "ensemble", "openai", "claude", or "qwen"
            save_to_db: Whether to save to database

        Returns:
            Generated question dictionary
        """
        # Generate question using LLM
        if generation_method == "ensemble":
            llm_output = await self.ensemble.generate_osym_question_ensemble(
                topic=topic,
                subtopic=subtopic,
                difficulty=difficulty,
                bloom_level=bloom_level,
                exam_type=exam_type,
                use_voting=True,
            )
            gen_method = "ensemble"
        else:
            # Use specific provider
            provider_map = {
                "openai": LLMProvider.OPENAI,
                "claude": LLMProvider.CLAUDE,
                "qwen": LLMProvider.QWEN,
            }
            provider = self.ensemble.providers.get(provider_map[generation_method])
            if not provider:
                raise ValueError(f"Provider {generation_method} not available")

            llm_output = await provider.create_osym_question(
                topic, subtopic, difficulty, bloom_level, exam_type
            )
            gen_method = generation_method

        # Extract generated content
        stem = llm_output.get("stem", "")
        options = llm_output.get("options", [])
        correct_answer_index = llm_output.get("correct_answer", 0)
        explanation = llm_output.get("explanation", "")
        keywords = llm_output.get("keywords", [])
        estimated_time = llm_output.get("estimated_time_seconds", 90)

        # Validate options
        if len(options) != 5:
            raise ValueError(f"Expected 5 options, got {len(options)}")

        # Extract correct answer and distractors
        correct_answer = options[correct_answer_index]
        distractors = [
            opt for i, opt in enumerate(options) if i != correct_answer_index
        ]

        # Quality scoring
        quality_score = self.quality_scorer.score_question(
            question_stem=stem,
            options=options,
            correct_answer_index=correct_answer_index,
            topic=topic,
            difficulty_target=difficulty,
            exam_type=exam_type,
        )

        # IRT parameter estimation
        irt_model = IRTModel.create_from_difficulty(difficulty)
        irt_params = irt_model.params

        # Determine difficulty level category
        difficulty_level = self._categorize_difficulty(difficulty)

        # Create question object
        question_data = {
            "id": str(uuid4()),
            "stem": stem,
            "correct_answer": correct_answer,
            "distractor_1": distractors[0] if len(distractors) > 0 else "",
            "distractor_2": distractors[1] if len(distractors) > 1 else "",
            "distractor_3": distractors[2] if len(distractors) > 2 else "",
            "distractor_4": distractors[3] if len(distractors) > 3 else "",
            "correct_answer_index": correct_answer_index,
            "explanation": explanation,
            "keywords": keywords,
            "exam_type": exam_type,
            "subject": subject,
            "topic": topic,
            "subtopic": subtopic,
            "bloom_level": bloom_level,
            "difficulty_level": difficulty_level,
            "estimated_time_seconds": estimated_time,
            "generation_method": gen_method,
            "irt_difficulty": irt_params.b,
            "irt_discrimination": irt_params.a,
            "irt_guessing": irt_params.c,
            "irt_upper_asymptote": irt_params.d,
            "quality_score_total": quality_score.total_score,
            "quality_score_format": quality_score.format_compliance,
            "quality_score_language": quality_score.language_quality,
            "quality_score_distractors": quality_score.distractor_quality,
            "quality_score_relevance": quality_score.topic_relevance,
            "quality_score_difficulty": quality_score.difficulty_appropriate,
            "status": QuestionStatus.PENDING_REVIEW.value,
            "metadata": {
                "quality_feedback": quality_score.feedback,
                "quality_improvements": quality_score.improvements,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Save to database if requested
        if save_to_db and self.db:
            db_question = OSYMQuestion(**question_data)
            self.db.add(db_question)
            await self.db.commit()
            await self.db.refresh(db_question)

        return question_data

    async def generate_batch(
        self,
        exam_type: str,
        subject: str,
        topics: List[Dict[str, Any]],
        target_count: int,
        generation_method: str = "ensemble",
        quality_threshold: float = 70.0,
    ) -> Dict[str, Any]:
        """
        Generate batch of OSYM questions

        Args:
            exam_type: TYT/AYT/YDT
            subject: Subject area
            topics: List of topic configs [{topic, subtopic, difficulty, bloom_level, count}]
            target_count: Target number of questions
            generation_method: Generation method
            quality_threshold: Minimum quality score to accept

        Returns:
            Batch generation results
        """
        batch_id = uuid4()
        batch_start = datetime.now(timezone.utc)

        # Create batch record
        if self.db:
            batch = QuestionGenerationBatch(
                id=batch_id,
                exam_type=exam_type,
                subject=subject,
                target_count=target_count,
                generation_method=generation_method,
                status="running",
                started_at=batch_start,
                generation_config={
                    "topics": topics,
                    "quality_threshold": quality_threshold,
                },
            )
            self.db.add(batch)
            await self.db.commit()

        generated_questions = []
        total_cost = 0.0
        generation_times = []

        # Generate questions for each topic
        for topic_config in topics:
            topic = topic_config["topic"]
            subtopic = topic_config.get("subtopic", "")
            difficulty = topic_config.get("difficulty", 0.5)
            bloom_level = topic_config.get("bloom_level", 3)
            count = topic_config.get("count", 1)

            for _ in range(count):
                try:
                    start_time = datetime.now(timezone.utc)

                    question = await self.generate_question(
                        topic=topic,
                        subtopic=subtopic,
                        exam_type=exam_type,
                        subject=subject,
                        difficulty=difficulty,
                        bloom_level=bloom_level,
                        generation_method=generation_method,
                        save_to_db=True,
                    )

                    end_time = datetime.now(timezone.utc)
                    generation_time = (end_time - start_time).total_seconds()
                    generation_times.append(generation_time)

                    # Check quality threshold
                    if question["quality_score_total"] >= quality_threshold:
                        generated_questions.append(question)
                    else:
                        print(
                            f"Question rejected (quality {question['quality_score_total']:.1f} < {quality_threshold})"
                        )

                except Exception as e:
                    print(f"Error generating question: {e}")
                    continue

        # Calculate statistics
        avg_generation_time = (
            sum(generation_times) / len(generation_times) if generation_times else 0
        )
        avg_quality_score = (
            sum(q["quality_score_total"] for q in generated_questions)
            / len(generated_questions)
            if generated_questions
            else 0
        )

        # Update batch record
        if self.db:
            batch.status = "completed"
            batch.completed_at = datetime.now(timezone.utc)
            batch.generated_count = len(generated_questions)
            batch.approved_count = len(
                [q for q in generated_questions if q["quality_score_total"] >= 80]
            )
            batch.avg_generation_time_seconds = avg_generation_time
            batch.total_cost_usd = total_cost
            batch.avg_quality_score = avg_quality_score
            batch.results_summary = {
                "generated": len(generated_questions),
                "target": target_count,
                "success_rate": len(generated_questions) / target_count
                if target_count > 0
                else 0,
                "avg_quality": avg_quality_score,
            }
            await self.db.commit()

        return {
            "batch_id": str(batch_id),
            "status": "completed",
            "generated_count": len(generated_questions),
            "target_count": target_count,
            "success_rate": len(generated_questions) / target_count
            if target_count > 0
            else 0,
            "avg_quality_score": avg_quality_score,
            "avg_generation_time_seconds": avg_generation_time,
            "total_cost_usd": total_cost,
            "questions": generated_questions[:10],  # Return first 10 for preview
        }

    def _categorize_difficulty(self, difficulty: float) -> str:
        """Categorize difficulty 0-1 to label"""
        if difficulty < 0.2:
            return DifficultyLevel.VERY_EASY.value
        elif difficulty < 0.4:
            return DifficultyLevel.EASY.value
        elif difficulty < 0.6:
            return DifficultyLevel.MEDIUM.value
        elif difficulty < 0.8:
            return DifficultyLevel.HARD.value
        else:
            return DifficultyLevel.VERY_HARD.value

    async def calibrate_question(
        self, question_id: UUID, student_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calibrate IRT parameters based on student responses

        Args:
            question_id: Question ID
            student_responses: List of {student_ability, response} dicts

        Returns:
            Updated IRT parameters
        """
        # Extract abilities and responses
        abilities = [r["student_ability"] for r in student_responses]
        responses = [r["response"] for r in student_responses]

        # Use adaptive calibrator
        calibrator = AdaptiveCalibrator()
        for ability, response in zip(abilities, responses):
            calibrator.add_response(ability, response, update_now=False)

        calibrator.update_parameters()

        # Update database
        if self.db:
            question = await self.db.get(OSYMQuestion, question_id)
            if question:
                question.irt_difficulty = calibrator.params.b
                question.irt_discrimination = calibrator.params.a
                question.irt_guessing = calibrator.params.c
                question.irt_upper_asymptote = calibrator.params.d
                await self.db.commit()

        return {
            "question_id": str(question_id),
            "irt_parameters": {
                "a": calibrator.params.a,
                "b": calibrator.params.b,
                "c": calibrator.params.c,
                "d": calibrator.params.d,
            },
            "calibration_stats": calibrator.get_calibration_stats(),
        }
