"""
Question Repository
Soru bankası ve sınav yönetimi için özel repository
"""

import logging
import random
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database import (
    ExamQuestion,
    ExamSession,
    ExamType,
    QuestionDifficulty,
    StudentAnswer,
    SubjectArea,
)
from models.question_bank import QuestionBankItem as Question

from .base import BaseRepository

logger = logging.getLogger(__name__)


class QuestionRepository(BaseRepository[Question]):
    """Question repository with specialized query methods"""

    def __init__(self, session: AsyncSession):
        super().__init__(Question, session)

    async def get_by_exam_type(
        self, exam_type: ExamType, skip: int = 0, limit: int = 100
    ) -> list[Question]:
        """Get questions by exam type"""
        return await self.get_all(
            skip=skip, limit=limit, filters={"exam_type": exam_type, "is_active": True}
        )

    async def get_by_subject_and_topic(
        self,
        subject_area: SubjectArea,
        topic: str,
        difficulty: QuestionDifficulty | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Question]:
        """Get questions by subject, topic and optional difficulty"""
        filters = {"subject_area": subject_area, "topic": topic, "is_active": True}

        if difficulty:
            filters["difficulty"] = difficulty

        return await self.get_all(skip=skip, limit=limit, filters=filters)

    async def get_random_questions(
        self,
        exam_type: ExamType,
        subject_area: SubjectArea,
        count: int,
        difficulty_distribution: dict[QuestionDifficulty, int] | None = None,
    ) -> list[Question]:
        """Get random questions with optional difficulty distribution"""
        try:
            if difficulty_distribution:
                # Get questions by difficulty levels
                all_questions = []
                for difficulty, needed_count in difficulty_distribution.items():
                    questions = await self.get_all(
                        filters={
                            "exam_type": exam_type,
                            "subject_area": subject_area,
                            "difficulty": difficulty,
                            "is_active": True,
                        },
                        limit=needed_count * 2,  # Get more to have selection
                    )

                    # Randomly select needed count
                    selected = random.sample(
                        questions, min(needed_count, len(questions))
                    )
                    all_questions.extend(selected)

                return all_questions
            # Get random questions without difficulty constraint
            questions = await self.get_all(
                filters={
                    "exam_type": exam_type,
                    "subject_area": subject_area,
                    "is_active": True,
                },
                limit=count * 2,  # Get more to have selection
            )

            return random.sample(questions, min(count, len(questions)))

        except Exception as e:
            logger.error(f"Error getting random questions: {e!s}")
            raise

    async def get_by_irt_difficulty_range(
        self,
        exam_type: ExamType,
        subject_area: SubjectArea,
        min_difficulty: float,
        max_difficulty: float,
        count: int,
    ) -> list[Question]:
        """Get questions within IRT difficulty range"""
        try:
            result = await self.session.execute(
                select(Question)
                .where(
                    and_(
                        Question.exam_type == exam_type,
                        Question.subject_area == subject_area,
                        Question.irt_difficulty >= min_difficulty,
                        Question.irt_difficulty <= max_difficulty,
                        Question.is_active == True,
                    )
                )
                .order_by(func.random())
                .limit(count)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting questions by IRT difficulty: {e!s}")
            raise

    async def update_question_statistics(
        self, question_id: str, is_correct: bool, response_time: float
    ) -> Question | None:
        """Update question statistics after student answer"""
        try:
            question = await self.get_by_id(question_id)
            if not question:
                return None

            # Update statistics
            new_times_asked = question.times_asked + 1
            new_times_correct = question.times_correct + (1 if is_correct else 0)

            # Update average response time
            current_avg = question.average_response_time
            new_avg = (
                (current_avg * question.times_asked) + response_time
            ) / new_times_asked

            return await self.update(
                question_id,
                times_asked=new_times_asked,
                times_correct=new_times_correct,
                average_response_time=new_avg,
            )
        except Exception as e:
            logger.error(f"Error updating question statistics: {e!s}")
            raise

    async def get_question_performance_stats(self, question_id: str) -> dict[str, Any]:
        """Get detailed performance statistics for a question"""
        try:
            question = await self.get_by_id(question_id)
            if not question:
                return {}

            # Calculate additional stats
            success_rate = (
                (question.times_correct / question.times_asked)
                if question.times_asked > 0
                else 0
            )

            return {
                "question_id": question_id,
                "times_asked": question.times_asked,
                "times_correct": question.times_correct,
                "success_rate": success_rate,
                "average_response_time": question.average_response_time,
                "irt_difficulty": question.irt_difficulty,
                "irt_discrimination": question.irt_discrimination,
                "morphology_complexity": question.morphology_complexity,
                "readability_score": question.readability_score,
            }
        except Exception as e:
            logger.error(f"Error getting question performance stats: {e!s}")
            raise


class ExamSessionRepository(BaseRepository[ExamSession]):
    """Exam session repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(ExamSession, session)

    async def get_by_student_id(
        self, student_id: str, skip: int = 0, limit: int = 100
    ) -> list[ExamSession]:
        """Get exam sessions by student ID"""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"student_id": student_id},
            order_by="created_at",
        )

    async def get_active_session(self, student_id: str) -> ExamSession | None:
        """Get active exam session for student"""
        try:
            result = await self.session.execute(
                select(ExamSession)
                .where(
                    and_(
                        ExamSession.student_id == student_id,
                        ExamSession.status.in_(["not_started", "in_progress"]),
                    )
                )
                .order_by(desc(ExamSession.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting active session: {e!s}")
            raise

    async def create_exam_session(
        self,
        student_id: str,
        exam_type: ExamType,
        exam_name: str,
        questions: list[Question],
        duration_minutes: int,
    ) -> ExamSession:
        """Create new exam session with questions"""
        try:
            # Create exam session
            session_data = {
                "student_id": student_id,
                "exam_type": exam_type,
                "exam_name": exam_name,
                "total_questions": len(questions),
                "duration_minutes": duration_minutes,
                "status": "not_started",
            }

            exam_session = await self.create(**session_data)

            # Create exam questions
            exam_questions = []
            for i, question in enumerate(questions):
                exam_question = ExamQuestion(
                    exam_session_id=exam_session.id,
                    question_id=question.id,
                    question_order=i + 1,
                )
                exam_questions.append(exam_question)

            self.session.add_all(exam_questions)
            await self.session.flush()

            return exam_session
        except Exception as e:
            logger.error(f"Error creating exam session: {e!s}")
            await self.session.rollback()
            raise

    async def start_exam(self, session_id: str) -> ExamSession | None:
        """Start exam session"""
        return await self.update(
            session_id, status="in_progress", started_at=datetime.now()
        )

    async def complete_exam(
        self,
        session_id: str,
        total_correct: int,
        total_wrong: int,
        total_empty: int,
        raw_score: float,
        estimated_ability: float = 0.0,
    ) -> ExamSession | None:
        """Complete exam session with results"""
        return await self.update(
            session_id,
            status="completed",
            completed_at=datetime.now(),
            total_correct=total_correct,
            total_wrong=total_wrong,
            total_empty=total_empty,
            raw_score=raw_score,
            estimated_ability=estimated_ability,
        )

    async def get_session_with_questions(
        self, session_id: str
    ) -> ExamSession | None:
        """Get exam session with questions loaded"""
        try:
            result = await self.session.execute(
                select(ExamSession)
                .options(
                    selectinload(ExamSession.exam_questions).selectinload(
                        ExamQuestion.question
                    ),
                    selectinload(ExamSession.student_answers),
                )
                .where(ExamSession.id == session_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting session with questions: {e!s}")
            raise


class StudentAnswerRepository(BaseRepository[StudentAnswer]):
    """Student answer repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(StudentAnswer, session)

    async def save_answer(
        self,
        exam_session_id: str,
        question_id: str,
        selected_answer: str | None,
        response_time_seconds: float,
        answer_changes: int = 0,
        time_to_first_answer: float = 0.0,
        confidence_level: float | None = None,
    ) -> StudentAnswer:
        """Save or update student answer"""
        try:
            # Check if answer already exists
            existing = await self.session.execute(
                select(StudentAnswer).where(
                    and_(
                        StudentAnswer.exam_session_id == exam_session_id,
                        StudentAnswer.question_id == question_id,
                    )
                )
            )
            existing_answer = existing.scalar_one_or_none()

            # Get question to check correct answer
            question_result = await self.session.execute(
                select(Question).where(
                    and_(Question.id == question_id, Question.is_active == True)
                )
            )
            question = question_result.scalar_one()

            is_correct = (
                selected_answer == question.correct_answer if selected_answer else None
            )

            if existing_answer:
                # Update existing answer
                return await self.update(
                    existing_answer.id,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                    response_time_seconds=response_time_seconds,
                    answer_changes=answer_changes,
                    time_to_first_answer=time_to_first_answer,
                    confidence_level=confidence_level,
                    answered_at=datetime.now(),
                )
            # Create new answer
            return await self.create(
                exam_session_id=exam_session_id,
                question_id=question_id,
                selected_answer=selected_answer,
                is_correct=is_correct,
                response_time_seconds=response_time_seconds,
                answer_changes=answer_changes,
                time_to_first_answer=time_to_first_answer,
                confidence_level=confidence_level,
            )
        except Exception as e:
            logger.error(f"Error saving student answer: {e!s}")
            raise

    async def get_session_answers(self, exam_session_id: str) -> list[StudentAnswer]:
        """Get all answers for an exam session"""
        return await self.get_all(
            filters={"exam_session_id": exam_session_id}, order_by="answered_at"
        )

    async def get_student_performance_by_subject(
        self, student_id: str, subject_area: SubjectArea, days_back: int = 30
    ) -> dict[str, Any]:
        """Get student performance statistics by subject"""
        try:
            # This would require joining multiple tables
            # For now, return basic structure
            return {
                "student_id": student_id,
                "subject_area": subject_area.value,
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0.0,
                "average_response_time": 0.0,
                "improvement_trend": 0.0,
            }
        except Exception as e:
            logger.error(f"Error getting student performance: {e!s}")
            raise
