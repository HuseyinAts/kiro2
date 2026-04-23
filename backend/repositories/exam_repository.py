"""
Exam Repositories - Session, Answer, and Result Management
Phase 2.8: Replaces in-memory storage in sinav_motoru_service.py

IMPORTANT: Using synchronous Session (not AsyncSession) for consistency with SessionRepository pattern
"""
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session as DBSession

from models.database import (
    ExamQuestion,
    ExamSession,
    ExamType,
    StudentAnswer,
)


class ExamSessionRepository:
    """
    Repository for exam session management
    Replaces: self.aktif_oturumlar: Dict[str, SinavOturumu] = {}
    Replaces: self.zaman_takip: Dict[str, Dict] = {} (time tracking now in ExamSession)
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_session(
        self,
        student_id: str,
        exam_type: ExamType,
        exam_name: str,
        total_questions: int,
        duration_minutes: int,
        question_ids: list[str],
    ) -> ExamSession:
        """
        Create new exam session
        Replaces: self.aktif_oturumlar[sinav_id] = sinav_oturumu
        """
        session = ExamSession(
            student_id=student_id,
            exam_type=exam_type,
            exam_name=exam_name,
            total_questions=total_questions,
            duration_minutes=duration_minutes,
            status="not_started",
            current_question_index=0,
            total_correct=0,
            total_wrong=0,
            total_empty=0,
            raw_score=0.0,
            estimated_ability=0.0,
            ability_confidence=0.0,
        )

        self.db.add(session)
        self.db.flush()

        # Create exam questions (relationship)
        for index, question_id in enumerate(question_ids):
            exam_question = ExamQuestion(
                exam_session_id=session.id,
                question_id=question_id,
                question_order=index,
            )
            self.db.add(exam_question)

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session(self, session_id: str) -> ExamSession | None:
        """
        Get exam session by ID
        Replaces: self.aktif_oturumlar.get(sinav_id)
        """
        return self.db.query(ExamSession).filter_by(id=session_id).first()

    def get_active_sessions_for_student(self, student_id: str) -> list[ExamSession]:
        """Get all active (not completed) sessions for a student"""
        return (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.student_id == student_id,
                    ExamSession.status.in_(["not_started", "in_progress"]),
                )
            )
            .order_by(ExamSession.created_at.desc())
            .all()
        )

    def get_all_sessions_for_student(
        self,
        student_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[ExamSession]:
        """
        Get all exam sessions for a student
        Replaces: [oturum for oturum in self.aktif_oturumlar.values() if oturum.ogrenci_id == ogrenci_id]
        """
        return (
            self.db.query(ExamSession)
            .filter_by(student_id=student_id)
            .order_by(ExamSession.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def start_session(self, session_id: str) -> ExamSession | None:
        """
        Start exam session
        Updates status and timing fields
        """
        session = self.get_session(session_id)
        if not session:
            return None

        if session.status != "not_started":
            raise ValueError("Exam session already started or completed")

        # Update session
        session.status = "in_progress"
        session.started_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(session)

        return session

    def update_current_question(
        self, session_id: str, question_index: int
    ) -> ExamSession | None:
        """Update current question index"""
        session = self.get_session(session_id)
        if not session:
            return None

        session.current_question_index = question_index
        session.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(session)

        return session

    def complete_session(
        self,
        session_id: str,
        total_correct: int,
        total_wrong: int,
        total_empty: int,
        raw_score: float,
        time_spent_seconds: int,
    ) -> ExamSession | None:
        """
        Complete exam session and store results
        Replaces: self.sinav_sonuclari[sinav_id] = sonuc
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Update session with results
        session.status = "completed"
        session.completed_at = datetime.now(UTC)
        session.time_spent_seconds = time_spent_seconds
        session.total_correct = total_correct
        session.total_wrong = total_wrong
        session.total_empty = total_empty
        session.raw_score = raw_score
        session.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(session)

        return session

    def abandon_session(self, session_id: str) -> ExamSession | None:
        """
        Mark session as abandoned (cancelled)
        Replaces: oturum.durum = SinavDurumu.IPTAL_EDILDI
        """
        session = self.get_session(session_id)
        if not session:
            return None

        session.status = "abandoned"
        session.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session_with_questions(self, session_id: str) -> ExamSession | None:
        """Get session with eager-loaded questions"""
        from sqlalchemy.orm import selectinload

        return (
            self.db.query(ExamSession)
            .options(selectinload(ExamSession.exam_questions))
            .filter_by(id=session_id)
            .first()
        )

    def get_question_ids_for_session(self, session_id: str) -> list[str]:
        """Get ordered list of question IDs for an exam session"""
        exam_questions = (
            self.db.query(ExamQuestion)
            .filter_by(exam_session_id=session_id)
            .order_by(ExamQuestion.question_order)
            .all()
        )

        return [eq.question_id for eq in exam_questions]

    def update_irt_analysis(
        self,
        session_id: str,
        estimated_ability: float,
        ability_confidence: float,
    ) -> ExamSession | None:
        """Update IRT analysis results"""
        session = self.get_session(session_id)
        if not session:
            return None

        session.estimated_ability = estimated_ability
        session.ability_confidence = ability_confidence
        session.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_sessions_by_type(
        self, exam_type: ExamType, limit: int = 100
    ) -> list[ExamSession]:
        """Get all sessions of a specific exam type"""
        return (
            self.db.query(ExamSession)
            .filter_by(exam_type=exam_type)
            .order_by(ExamSession.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_completed_sessions_count(self, student_id: str) -> int:
        """Get count of completed exams for a student"""
        return (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.student_id == student_id,
                    ExamSession.status == "completed",
                )
            )
            .count()
        )

    def get_average_score(self, student_id: str, exam_type: ExamType | None = None) -> float:
        """Get average score for a student (optionally filtered by exam type)"""
        query = self.db.query(func.avg(ExamSession.raw_score)).filter(
            and_(
                ExamSession.student_id == student_id,
                ExamSession.status == "completed",
            )
        )

        if exam_type:
            query = query.filter(ExamSession.exam_type == exam_type)

        result = query.scalar()
        return float(result) if result else 0.0


class ExamAnswerRepository:
    """
    Repository for student answer management
    Replaces: self.sinav_cevaplari: Dict[str, List[SinavCevabi]] = {}
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_answer(
        self,
        exam_session_id: str,
        question_id: str,
        selected_answer: str | None = None,
        response_time_seconds: float = 0.0,
    ) -> StudentAnswer:
        """
        Create or update student answer
        Replaces: self.sinav_cevaplari[sinav_id].append(sinav_cevabi)
        """
        # Check if answer already exists (user changed answer)
        existing_answer = (
            self.db.query(StudentAnswer)
            .filter(
                and_(
                    StudentAnswer.exam_session_id == exam_session_id,
                    StudentAnswer.question_id == question_id,
                )
            )
            .first()
        )

        if existing_answer:
            # Update existing answer (answer change)
            existing_answer.selected_answer = selected_answer
            existing_answer.response_time_seconds = response_time_seconds
            existing_answer.answer_changes += 1
            existing_answer.answered_at = datetime.now(UTC)

            self.db.commit()
            self.db.refresh(existing_answer)
            return existing_answer
        # Create new answer
        answer = StudentAnswer(
            exam_session_id=exam_session_id,
            question_id=question_id,
            selected_answer=selected_answer,
            response_time_seconds=response_time_seconds,
            answer_changes=0,
            time_to_first_answer=response_time_seconds,
        )

        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)

        return answer

    def get_answers_for_session(self, exam_session_id: str) -> list[StudentAnswer]:
        """
        Get all answers for an exam session
        Replaces: self.sinav_cevaplari.get(sinav_id, [])
        """
        return (
            self.db.query(StudentAnswer)
            .filter_by(exam_session_id=exam_session_id)
            .all()
        )

    def get_answer(
        self, exam_session_id: str, question_id: str
    ) -> StudentAnswer | None:
        """Get specific answer for a question in an exam"""
        return (
            self.db.query(StudentAnswer)
            .filter(
                and_(
                    StudentAnswer.exam_session_id == exam_session_id,
                    StudentAnswer.question_id == question_id,
                )
            )
            .first()
        )

    def mark_answer_correctness(
        self,
        exam_session_id: str,
        question_id: str,
        is_correct: bool,
    ) -> StudentAnswer | None:
        """Mark answer as correct/incorrect (for grading)"""
        answer = self.get_answer(exam_session_id, question_id)
        if not answer:
            return None

        answer.is_correct = is_correct

        self.db.commit()
        self.db.refresh(answer)

        return answer

    def get_answer_statistics(
        self, exam_session_id: str
    ) -> dict[str, int]:
        """Get answer statistics (correct, wrong, empty)"""
        answers = self.get_answers_for_session(exam_session_id)

        correct = sum(1 for a in answers if a.is_correct is True)
        wrong = sum(1 for a in answers if a.is_correct is False)
        empty = sum(1 for a in answers if a.selected_answer is None)

        return {
            "correct": correct,
            "wrong": wrong,
            "empty": empty,
            "total": len(answers),
        }

    def get_average_response_time(self, exam_session_id: str) -> float:
        """Get average response time for all questions"""
        result = (
            self.db.query(func.avg(StudentAnswer.response_time_seconds))
            .filter_by(exam_session_id=exam_session_id)
            .scalar()
        )

        return float(result) if result else 0.0

    def get_answer_change_count(self, exam_session_id: str) -> int:
        """Get total number of answer changes"""
        result = (
            self.db.query(func.sum(StudentAnswer.answer_changes))
            .filter_by(exam_session_id=exam_session_id)
            .scalar()
        )

        return int(result) if result else 0

    def bulk_mark_answers(
        self, exam_session_id: str, correct_answers: dict[str, str]
    ) -> int:
        """
        Bulk mark answers as correct/incorrect
        Returns count of answers marked

        Args:
            exam_session_id: The exam session ID
            correct_answers: Dict mapping question_id -> correct_answer (e.g., {"q1": "A", "q2": "B"})
        """
        answers = self.get_answers_for_session(exam_session_id)
        count = 0

        for answer in answers:
            if answer.question_id in correct_answers:
                correct_answer = correct_answers[answer.question_id]
                answer.is_correct = answer.selected_answer == correct_answer
                count += 1

        self.db.commit()

        return count


class ExamResultRepository:
    """
    Repository for exam result queries
    Note: Results are stored in ExamSession model, this provides convenience methods
    """

    def __init__(self, db: DBSession):
        self.db = db

    def get_result(self, session_id: str) -> ExamSession | None:
        """
        Get exam result
        Replaces: self.sinav_sonuclari.get(sinav_id)
        """
        return (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.id == session_id,
                    ExamSession.status == "completed",
                )
            )
            .first()
        )

    def get_student_results(
        self,
        student_id: str,
        exam_type: ExamType | None = None,
        limit: int = 20,
    ) -> list[ExamSession]:
        """Get all completed exam results for a student"""
        query = self.db.query(ExamSession).filter(
            and_(
                ExamSession.student_id == student_id,
                ExamSession.status == "completed",
            )
        )

        if exam_type:
            query = query.filter(ExamSession.exam_type == exam_type)

        return query.order_by(ExamSession.completed_at.desc()).limit(limit).all()

    def get_recent_results(self, days: int = 30, limit: int = 100) -> list[ExamSession]:
        """Get recent exam results (last N days)"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        return (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.status == "completed",
                    ExamSession.completed_at >= cutoff_date,
                )
            )
            .order_by(ExamSession.completed_at.desc())
            .limit(limit)
            .all()
        )

    def get_performance_trend(
        self, student_id: str, exam_type: ExamType, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get performance trend (scores over time)"""
        results = (
            self.db.query(ExamSession)
            .filter(
                and_(
                    ExamSession.student_id == student_id,
                    ExamSession.exam_type == exam_type,
                    ExamSession.status == "completed",
                )
            )
            .order_by(ExamSession.completed_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "date": result.completed_at,
                "score": result.raw_score,
                "correct": result.total_correct,
                "wrong": result.total_wrong,
                "empty": result.total_empty,
            }
            for result in results
        ]
