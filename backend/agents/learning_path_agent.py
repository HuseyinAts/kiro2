"""
Kişiselleştirilmiş Öğrenme Yolu Oluşturan YZ Ajanı
Teknofest 2025 - Eğitim Eylemci Projesi

Bu ajan öğrencinin:
- Öğrenme hedeflerini belirler
- Mevcut bilgi seviyesini ölçer
- Tercih ettiği öğrenme stilini anlar
- Kişiselleştirilmiş öğrenme yolu oluşturur
"""

import json
import logging
import os

# Core services
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.assessment_system import AssessmentResult, AssessmentType, assessment_system
from core.chat_interface import chat_interface
from core.form_interface import FormType, form_interface
from core.learning_style_detector import BehavioralIndicator, learning_style_detector
from core.llm_service import llm_service
from core.rag_service import rag_service
from core.structured_learning_path import structured_path_generator
from core.unified_resource_ranker import unified_resource_ranker
from integrations.khan_academy_service import khan_academy_service
from integrations.oer_service import OERResource, oer_service
from integrations.youtube_service import youtube_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LearningStyle(Enum):
    """Öğrenme stilleri"""

    VISUAL = "visual"  # Görsel öğrenme (video, infografik)
    AUDITORY = "auditory"  # İşitsel öğrenme (podcast, anlatım)
    READING = "reading"  # Okuma-yazma (metin, makale)
    KINESTHETIC = "kinesthetic"  # Uygulamalı öğrenme (pratik, proje)
    MIXED = "mixed"  # Karma


class KnowledgeLevel(Enum):
    """Bilgi seviyeleri"""

    BEGINNER = "beginner"  # Başlangıç
    ELEMENTARY = "elementary"  # Temel
    INTERMEDIATE = "intermediate"  # Orta
    ADVANCED = "advanced"  # İleri
    EXPERT = "expert"  # Uzman


@dataclass
class StudentProfile:
    """Öğrenci profili"""

    student_id: str
    name: str
    grade: str  # Sınıf seviyesi
    exam_target: str  # LGS veya YKS
    learning_goal: str  # Öğrenme hedefi
    learning_style: LearningStyle
    knowledge_level: KnowledgeLevel
    interests: list[str]
    available_time: int  # Günlük dakika
    metadata: dict[str, Any]


@dataclass
class LearningResource:
    """Öğrenme kaynağı"""

    resource_id: str
    title: str
    source: str  # YouTube, Khan Academy, Wikipedia, etc.
    url: str
    resource_type: str  # video, article, course, quiz, etc.
    difficulty_level: KnowledgeLevel
    estimated_time: int  # Dakika
    language: str
    description: str
    tags: list[str]
    rating: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class LearningPath:
    """Öğrenme yolu"""

    path_id: str
    student_profile: StudentProfile
    resources: list[LearningResource]
    total_time: int  # Toplam süre (dakika)
    phases: list[dict[str, Any]]  # Öğrenme aşamaları
    created_at: datetime
    reasoning: str  # Neden bu yol önerildi
    metadata: dict[str, Any]


class LearningPathAgent:
    """Kişiselleştirilmiş Öğrenme Yolu Oluşturan Ajan"""

    def __init__(self, rag_service: Any | None = None):
        self.profiles: dict[str, StudentProfile] = {}
        self.learning_paths: dict[str, Any] = {}
        self.resource_cache: dict[str, Any] = {}
        self.rag_service = rag_service

        # Initialize ZPD+Maarif system for culturally-adapted difficulty selection
        try:
            from algorithms.turkish_zpd_maarif_system import TurkishZPDMaarifSystem

            self.zpd_system = TurkishZPDMaarifSystem()
            logger.info("ZPD+Maarif system initialized for LearningPathAgent")
        except ImportError:
            self.zpd_system = None
            logger.warning("TurkishZPDMaarifSystem not available")

    async def _get_exam_history(self, student_id: str) -> dict[str, Any]:
        """
        Sınav geçmişinden bilgi seviyesi ve zayıf/güçlü konuları hesapla.

        Returns:
            {
                "has_data": bool,
                "overall_accuracy": float (0-1),
                "knowledge_level": str,  # beginner/elementary/intermediate/advanced/expert
                "subject_stats": {subject: {"correct": int, "total": int, "accuracy": float}},
                "weak_topics": [str],
                "strong_topics": [str],
            }
        """
        try:
            from sqlalchemy import Integer, select
            from sqlalchemy import func as sa_func

            from core.database import get_db_session_context
            from models.exam_db import ExamSession, StudentAnswer

            async with get_db_session_context() as session:
                # Get completed exam sessions for this student
                result = await session.execute(
                    select(ExamSession).where(
                        ExamSession.student_id == student_id,
                        ExamSession.status == "completed",
                    )
                )
                exams = result.scalars().all()

                if not exams:
                    return {"has_data": False}

                # Calculate overall accuracy
                total_correct = sum(e.total_correct for e in exams)
                total_questions = sum(e.total_questions for e in exams)
                overall_accuracy = (
                    total_correct / total_questions if total_questions > 0 else 0
                )

                # Determine knowledge level from accuracy
                if overall_accuracy >= 0.90:
                    level = "expert"
                elif overall_accuracy >= 0.70:
                    level = "advanced"
                elif overall_accuracy >= 0.50:
                    level = "intermediate"
                elif overall_accuracy >= 0.30:
                    level = "elementary"
                else:
                    level = "beginner"

                # Get per-question results with topic info
                from models.question_bank import QuestionBankItem

                answer_result = await session.execute(
                    select(
                        QuestionBankItem.subject_area,
                        sa_func.count().label("total"),
                        sa_func.sum(
                            sa_func.cast(StudentAnswer.is_correct, Integer)
                        ).label("correct"),
                    )
                    .join(
                        StudentAnswer,
                        StudentAnswer.question_id == QuestionBankItem.id,
                    )
                    .join(
                        ExamSession,
                        ExamSession.id == StudentAnswer.exam_session_id,
                    )
                    .where(
                        ExamSession.student_id == student_id,
                        ExamSession.status == "completed",
                        StudentAnswer.is_correct.isnot(None),
                    )
                    .group_by(QuestionBankItem.subject_area)
                )
                rows = answer_result.all()

                subject_stats = {}
                weak_topics = []
                strong_topics = []
                for row in rows:
                    subj = row.subject_area or "Genel"
                    correct = int(row.correct or 0)
                    total = int(row.total or 0)
                    acc = correct / total if total > 0 else 0
                    subject_stats[subj] = {
                        "correct": correct,
                        "total": total,
                        "accuracy": round(acc, 2),
                    }
                    if acc < 0.50:
                        weak_topics.append(f"{subj} (%{int(acc * 100)})")
                    elif acc >= 0.70:
                        strong_topics.append(f"{subj} (%{int(acc * 100)})")

                return {
                    "has_data": True,
                    "overall_accuracy": round(overall_accuracy, 2),
                    "knowledge_level": level,
                    "subject_stats": subject_stats,
                    "weak_topics": weak_topics,
                    "strong_topics": strong_topics,
                    "exam_count": len(exams),
                    "total_questions": total_questions,
                }

        except Exception as e:
            logger.warning(f"Could not load exam history for {student_id}: {e}")
            return {"has_data": False}

    async def analyze_student(
        self, student_id: str, initial_data: dict[str, Any]
    ) -> StudentProfile:
        """
        Öğrenci analizi yap ve profil oluştur.
        Sınav geçmişi varsa gerçek veriden bilgi seviyesi hesaplar,
        yoksa LLM tahmini kullanır.
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        if not initial_data or not isinstance(initial_data, dict):
            raise ValueError("initial_data must be a non-empty dictionary")

        try:
            # 1. Sınav geçmişinden gerçek bilgi seviyesi hesapla
            exam_history = await self._get_exam_history(student_id)

            if exam_history.get("has_data"):
                # Gerçek veriden analiz — LLM tahmininden çok daha güvenilir
                logger.info(
                    f"Using real exam data for {student_id}: "
                    f"accuracy={exam_history['overall_accuracy']}, "
                    f"level={exam_history['knowledge_level']}, "
                    f"exams={exam_history.get('exam_count', 0)}"
                )
                analysis = {
                    "learning_style": initial_data.get("learning_style", "mixed"),
                    "knowledge_level": exam_history["knowledge_level"],
                    "interests": list(exam_history.get("subject_stats", {}).keys()),
                    "goal_summary": initial_data.get("goal", "YKS hazırlık"),
                    "exam_history": exam_history,
                }
            else:
                # Sınav verisi yok — LLM tahmini kullan (fallback)
                analysis_prompt = f"""
                Öğrenci verisini analiz et ve profil oluştur:

                Veri: {json.dumps(initial_data, ensure_ascii=False)}

                Şunları belirle:
                1. Öğrenme stili (görsel/işitsel/okuma/kinestetik/karma)
                2. Bilgi seviyesi (başlangıç/temel/orta/ileri/uzman)
                3. İlgi alanları
                4. Öğrenme hedefi özeti

                JSON formatında yanıtla:
                {{
                    "learning_style": "...",
                    "knowledge_level": "...",
                    "interests": [...],
                    "goal_summary": "..."
                }}
                """

                result = await llm_service.generate(
                    prompt=analysis_prompt, temperature=0.3, max_tokens=300
                )

                try:
                    analysis = json.loads(result) if isinstance(result, str) else result
                    if (
                        not isinstance(analysis, dict)
                        or "learning_style" not in analysis
                    ):
                        raise ValueError("Missing expected keys in analysis")
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    logger.debug(f"JSON parsing failed for student analysis: {e}")
                    analysis = {
                        "learning_style": "mixed",
                        "knowledge_level": "beginner",
                        "interests": [],
                        "goal_summary": initial_data.get("goal", "Genel öğrenme"),
                    }

            # Normalize Turkish LLM outputs to enum values
            _style_map = {
                "karma": "mixed",
                "görsel": "visual",
                "işitsel": "auditory",
                "okuma": "reading",
                "uygulama": "kinesthetic",
            }
            _level_map = {
                "başlangıç": "beginner",
                "temel": "elementary",
                "orta": "intermediate",
                "ileri": "advanced",
                "uzman": "expert",
            }
            raw_style = analysis.get("learning_style", "mixed").lower()
            raw_level = analysis.get("knowledge_level", "beginner").lower()
            style_val = _style_map.get(raw_style, raw_style)
            level_val = _level_map.get(raw_level, raw_level)

            try:
                learning_style = LearningStyle(style_val)
            except ValueError:
                learning_style = LearningStyle.MIXED
            try:
                knowledge_level = KnowledgeLevel(level_val)
            except ValueError:
                knowledge_level = KnowledgeLevel.BEGINNER

            # Profil oluştur
            profile = StudentProfile(
                student_id=student_id,
                name=initial_data.get("name", "Öğrenci"),
                grade=initial_data.get("grade", ""),
                exam_target=initial_data.get("exam_target", ""),
                learning_goal=initial_data.get("goal", ""),
                learning_style=learning_style,
                knowledge_level=knowledge_level,
                interests=analysis.get("interests", []),
                available_time=initial_data.get(
                    "available_time", 60
                ),  # Default: 60 dakika/gün
                metadata={
                    "analysis": analysis,
                    "initial_data": initial_data,
                    "created_at": datetime.now().isoformat(),
                    "data_source": "exam_history"
                    if exam_history.get("has_data")
                    else "llm_estimate",
                },
            )

            # Cache'e kaydet
            self.profiles[student_id] = profile

            logger.info(
                f"Student profile created: {student_id} (source: {'exam_history' if exam_history.get('has_data') else 'llm_estimate'})"
            )
            return profile

        except Exception as e:
            logger.error(f"Student analysis error: {e!s}")
            raise

    async def assess_knowledge_level(
        self,
        student_id: str,
        subject: str,
        test_results: dict[str, Any] | None = None,
    ) -> KnowledgeLevel:
        """
        Bilgi seviyesi değerlendirmesi (Eski metod - geriye uyumluluk için)

        Args:
            student_id: Öğrenci ID
            subject: Konu/ders
            test_results: Test sonuçları (opsiyonel)

        Returns:
            Bilgi seviyesi
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        if not subject or not isinstance(subject, str):
            raise ValueError("subject must be a non-empty string")

        try:
            if test_results:
                # Test sonuçlarından seviye belirleme
                score = test_results.get("score", 0)
                total = test_results.get("total", 100)
                percentage = (score / total) * 100 if total > 0 else 0

                if percentage < 30:
                    return KnowledgeLevel.BEGINNER
                if percentage < 50:
                    return KnowledgeLevel.ELEMENTARY
                if percentage < 70:
                    return KnowledgeLevel.INTERMEDIATE
                if percentage < 90:
                    return KnowledgeLevel.ADVANCED
                return KnowledgeLevel.EXPERT
            # Öğrenci profilinden tahmin
            profile = self.profiles.get(student_id)
            if profile:
                return profile.knowledge_level
            return KnowledgeLevel.BEGINNER

        except Exception as e:
            logger.error(f"Knowledge assessment error: {e!s}")
            raise

    async def create_quick_assessment(
        self,
        student_id: str,
        subject: str,
        topic: str | None = None,
        question_count: int = 5,
    ) -> dict[str, Any]:
        """
        Enhanced quick assessment with dynamic question selection

        Args:
            student_id: Öğrenci ID
            subject: Ders konusu
            topic: Spesifik konu (opsiyonel)
            question_count: Soru sayısı (5-10)

        Returns:
            Gelişmiş değerlendirme verisi
        """
        try:
            # Öğrenci profilini kontrol et
            profile = self.profiles.get(student_id)
            difficulty = None

            if profile:
                # Profil varsa zorluk seviyesini belirle
                if (
                    profile.knowledge_level == KnowledgeLevel.BEGINNER
                    or profile.knowledge_level == KnowledgeLevel.ELEMENTARY
                ):
                    difficulty = assessment_system.DifficultyLevel.EASY
                elif profile.knowledge_level == KnowledgeLevel.INTERMEDIATE:
                    difficulty = assessment_system.DifficultyLevel.MEDIUM
                elif profile.knowledge_level == KnowledgeLevel.ADVANCED:
                    difficulty = assessment_system.DifficultyLevel.HARD
                else:
                    difficulty = assessment_system.DifficultyLevel.VERY_HARD

            # Enhanced assessment system ile sorular oluştur
            questions = await assessment_system.generate_quick_test(
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                question_count=question_count,
            )

            assessment_data = {
                "assessment_id": f"quick_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "assessment_type": "quick_test",
                "subject": subject,
                "topic": topic,
                "difficulty_level": difficulty.value if difficulty else "medium",
                "questions": [
                    {
                        "question_id": q.question_id,
                        "question_text": q.question_text,
                        "question_type": q.question_type.value,
                        "subject": q.subject,
                        "topic": q.topic,
                        "difficulty": q.difficulty.value,
                        "options": q.options,
                        "time_limit_seconds": q.time_limit_seconds,
                        "points": q.points,
                        "explanation": q.explanation,
                        "metadata": q.metadata,
                    }
                    for q in questions
                ],
                "total_questions": len(questions),
                "estimated_time_minutes": sum(q.time_limit_seconds for q in questions)
                // 60,
                "created_at": datetime.now().isoformat(),
                "adaptive_features": {
                    "difficulty_adjusted": difficulty is not None,
                    "profile_based": profile is not None,
                    "subject_context": True,
                },
            }

            logger.info(
                f"Created enhanced quick assessment for student {student_id}: {len(questions)} questions (difficulty: {difficulty.value if difficulty else 'medium'})"
            )
            return assessment_data

        except Exception as e:
            logger.error(f"Create quick assessment error: {e!s}")
            raise

    async def create_self_assessment(
        self, student_id: str, subjects: list[str]
    ) -> dict[str, Any]:
        """
        Öz değerlendirme oluştur

        Args:
            student_id: Öğrenci ID
            subjects: Değerlendirilecek dersler

        Returns:
            Öz değerlendirme verisi
        """
        try:
            # Assessment system ile öz değerlendirme soruları oluştur
            questions = await assessment_system.create_self_assessment(
                student_id=student_id, subjects=subjects
            )

            assessment_data = {
                "assessment_id": f"self_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "assessment_type": "self_assessment",
                "subjects": subjects,
                "questions": [
                    {
                        "question_id": q.question_id,
                        "question_text": q.question_text,
                        "question_type": q.question_type.value,
                        "subject": q.subject,
                        "topic": q.topic,
                        "options": q.options,
                        "metadata": q.metadata,
                    }
                    for q in questions
                ],
                "total_questions": len(questions),
                "estimated_time_minutes": len(questions) * 2,  # 2 dakika per soru
                "created_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Created self-assessment for student {student_id}: {len(questions)} questions"
            )
            return assessment_data

        except Exception as e:
            logger.error(f"Create self-assessment error: {e!s}")
            raise

    async def create_interactive_questionnaire(
        self, student_id: str, goal: str, subjects: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Enhanced interactive questionnaire with dynamic question selection

        Args:
            student_id: Öğrenci ID
            goal: Öğrenme hedefi
            subjects: İlgili dersler (opsiyonel)

        Returns:
            Gelişmiş etkileşimli anket verisi
        """
        try:
            # Öğrenci profilini ve geçmiş değerlendirmelerini al
            profile = self.profiles.get(student_id)
            current_knowledge = None

            if profile:
                current_knowledge = {
                    "learning_style": profile.learning_style.value,
                    "knowledge_level": profile.knowledge_level.value,
                    "interests": profile.interests,
                    "grade": profile.grade,
                }

            # Enhanced assessment system ile dinamik anket oluştur
            questions = await assessment_system.generate_interactive_questionnaire(
                student_id=student_id,
                goal=goal,
                subjects=subjects or ["Genel"],
                current_knowledge=current_knowledge,
            )

            assessment_data = {
                "assessment_id": f"interactive_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "assessment_type": "interactive_questionnaire",
                "goal": goal,
                "subjects": subjects or ["Genel"],
                "questions": [
                    {
                        "question_id": q.question_id,
                        "question_text": q.question_text,
                        "question_type": q.question_type.value,
                        "subject": q.subject,
                        "topic": q.topic,
                        "difficulty": q.difficulty.value,
                        "options": q.options,
                        "time_limit_seconds": q.time_limit_seconds,
                        "points": q.points,
                        "metadata": q.metadata,
                    }
                    for q in questions
                ],
                "total_questions": len(questions),
                "estimated_time_minutes": sum(q.time_limit_seconds for q in questions)
                // 60,
                "created_at": datetime.now().isoformat(),
                "adaptive_features": {
                    "profile_based": profile is not None,
                    "dynamic_selection": True,
                    "context_aware": current_knowledge is not None,
                    "goal_oriented": True,
                },
            }

            logger.info(
                f"Created enhanced interactive questionnaire for student {student_id}: {len(questions)} questions"
            )
            return assessment_data

        except Exception as e:
            logger.error(f"Create interactive questionnaire error: {e!s}")
            raise

    async def create_guided_self_assessment(
        self, student_id: str, subjects: list[str], learning_goals: list[str]
    ) -> dict[str, Any]:
        """
        Create guided self-assessment flow

        Args:
            student_id: Öğrenci ID
            subjects: Değerlendirilecek dersler
            learning_goals: Öğrenme hedefleri

        Returns:
            Guided self-assessment flow data
        """
        try:
            flow_data = await assessment_system.create_guided_self_assessment_flow(
                student_id=student_id, subjects=subjects, learning_goals=learning_goals
            )

            logger.info(
                f"Created guided self-assessment flow for student {student_id}: {flow_data['total_steps']} steps"
            )
            return flow_data

        except Exception as e:
            logger.error(f"Create guided self-assessment error: {e!s}")
            raise

    async def evaluate_assessment_results(
        self,
        assessment_id: str,
        answers: list[str],
        time_taken_seconds: int,
        additional_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Enhanced assessment result analysis with comprehensive evaluation

        Args:
            assessment_id: Değerlendirme ID
            answers: Verilen cevaplar
            time_taken_seconds: Geçen süre
            additional_data: Ek veriler (mouse movements, pause times, etc.)

        Returns:
            Kapsamlı değerlendirme sonuçları
        """
        try:
            # Assessment ID'den student_id ve assessment tipini çıkar
            parts = assessment_id.split("_")
            if len(parts) < 2:
                raise ValueError("Invalid assessment_id format")

            assessment_type_str = parts[0]
            student_id = parts[1]

            # Assessment tipini belirle
            assessment_type = AssessmentType.QUICK_TEST
            if assessment_type_str == "self":
                assessment_type = AssessmentType.SELF_ASSESSMENT
            elif assessment_type_str == "interactive":
                assessment_type = AssessmentType.INTERACTIVE_QUESTIONNAIRE
            elif assessment_type_str == "guided":
                assessment_type = AssessmentType.COMPREHENSIVE

            # Gerçek uygulamada assessment cache'den sorular alınacak
            # Şimdilik öğrenci profiline göre mock questions oluştur
            profile = self.profiles.get(student_id)
            subject = "Genel"
            difficulty = assessment_system.DifficultyLevel.MEDIUM

            if profile:
                subject = profile.learning_goal or "Genel"
                if profile.knowledge_level == KnowledgeLevel.BEGINNER:
                    difficulty = assessment_system.DifficultyLevel.EASY
                elif profile.knowledge_level == KnowledgeLevel.ADVANCED:
                    difficulty = assessment_system.DifficultyLevel.HARD
                elif profile.knowledge_level == KnowledgeLevel.EXPERT:
                    difficulty = assessment_system.DifficultyLevel.VERY_HARD

            # Mock questions oluştur (gerçek uygulamada cache'den alınacak)
            from core.assessment_system import Question, QuestionType

            mock_questions = []

            for i in range(len(answers)):
                if assessment_type == AssessmentType.SELF_ASSESSMENT:
                    # Self-assessment için scale questions
                    question = Question(
                        question_id=f"q_{i}",
                        question_text=f"Self-assessment soru {i + 1}",
                        question_type=QuestionType.SCALE,
                        subject=subject,
                        topic=f"Konu {i + 1}",
                        difficulty=difficulty,
                        options=["1", "2", "3", "4", "5"],
                        points=1,
                    )
                elif assessment_type == AssessmentType.INTERACTIVE_QUESTIONNAIRE:
                    # Interactive için mixed questions
                    q_type = (
                        QuestionType.MULTIPLE_CHOICE
                        if i % 2 == 0
                        else QuestionType.SCALE
                    )
                    question = Question(
                        question_id=f"q_{i}",
                        question_text=f"Interactive soru {i + 1}",
                        question_type=q_type,
                        subject=subject,
                        topic=f"Konu {i + 1}",
                        difficulty=difficulty,
                        correct_answer="A"
                        if q_type == QuestionType.MULTIPLE_CHOICE
                        else None,
                        options=["A", "B", "C", "D"]
                        if q_type == QuestionType.MULTIPLE_CHOICE
                        else ["1", "2", "3", "4", "5"],
                        points=1,
                    )
                else:
                    # Quick test için multiple choice
                    question = Question(
                        question_id=f"q_{i}",
                        question_text=f"Test soru {i + 1}",
                        question_type=QuestionType.MULTIPLE_CHOICE,
                        subject=subject,
                        topic=f"Konu {i + 1}",
                        difficulty=difficulty,
                        correct_answer="A" if i % 2 == 0 else "B",
                        options=["A", "B", "C", "D"],
                        points=1,
                    )

                mock_questions.append(question)

            # Comprehensive assessment system ile değerlendir
            result = await assessment_system.evaluate_assessment_comprehensive(
                student_id=student_id,
                assessment_type=assessment_type,
                questions=mock_questions,
                answers=answers,
                time_taken_seconds=time_taken_seconds,
                additional_data=additional_data,
            )

            # Öğrenci profilini güncelle
            if profile and result.knowledge_level:
                # Knowledge level'ı güncelle
                level_mapping = {
                    "beginner": KnowledgeLevel.BEGINNER,
                    "elementary": KnowledgeLevel.ELEMENTARY,
                    "intermediate": KnowledgeLevel.INTERMEDIATE,
                    "advanced": KnowledgeLevel.ADVANCED,
                    "expert": KnowledgeLevel.EXPERT,
                }

                new_level = level_mapping.get(
                    result.knowledge_level, profile.knowledge_level
                )
                if new_level != profile.knowledge_level:
                    profile.knowledge_level = new_level
                    profile.metadata["last_assessment_update"] = (
                        datetime.now().isoformat()
                    )
                    logger.info(
                        f"Updated student {student_id} knowledge level to {new_level.value}"
                    )

            # Sonucu comprehensive dict'e çevir
            result_data = {
                "assessment_id": result.assessment_id,
                "student_id": result.student_id,
                "assessment_type": result.assessment_type.value,
                "subject": result.subject,
                "total_score": result.total_score,
                "knowledge_level": result.knowledge_level,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "recommendations": result.recommendations,
                "time_taken_seconds": result.time_taken_seconds,
                "created_at": result.created_at.isoformat(),
                # Enhanced metrics
                "detailed_metrics": {
                    "accuracy": result.metadata.get("accuracy", 0),
                    "avg_time_per_question": result.metadata.get(
                        "avg_time_per_question", 0
                    ),
                    "topic_performance": result.metadata.get("topic_performance", {}),
                    "difficulty_performance": result.metadata.get(
                        "difficulty_performance", {}
                    ),
                    "question_times": result.metadata.get("question_times", []),
                },
                # Analysis insights
                "insights": {
                    "performance_trend": self._analyze_performance_trend(
                        student_id, result.total_score
                    ),
                    "learning_style_indicators": self._extract_learning_style_indicators(
                        result, additional_data
                    ),
                    "improvement_areas": result.weaknesses[
                        :3
                    ],  # Top 3 improvement areas
                    "next_steps": result.recommendations[:3],  # Top 3 next steps
                },
                # Additional data
                "additional_data": additional_data or {},
            }

            logger.info(
                f"Comprehensively evaluated assessment {assessment_id}: {result.total_score:.1f}% ({result.knowledge_level})"
            )
            return result_data

        except Exception as e:
            logger.error(f"Evaluate assessment results error: {e!s}")
            raise

    def _analyze_performance_trend(self, student_id: str, current_score: float) -> str:
        """Performans trendini analiz et"""
        try:
            previous_assessments = assessment_system.get_student_assessments(student_id)
            if len(previous_assessments) < 2:
                return "insufficient_data"

            # Son 3 değerlendirmenin ortalaması
            recent_scores = [a.total_score for a in previous_assessments[-3:]]
            avg_recent = sum(recent_scores) / len(recent_scores)

            if current_score > avg_recent + 10:
                return "improving"
            if current_score < avg_recent - 10:
                return "declining"
            return "stable"

        except Exception:
            return "unknown"

    def _extract_learning_style_indicators(
        self, result: AssessmentResult, additional_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Öğrenme stili göstergelerini çıkar"""
        indicators = {
            "response_speed": "normal",
            "question_preference": "mixed",
            "confidence_pattern": "consistent",
        }

        try:
            # Cevap hızı analizi
            avg_time = result.metadata.get("avg_time_per_question", 0)
            if avg_time < 30:
                indicators["response_speed"] = "fast"
            elif avg_time > 120:
                indicators["response_speed"] = "slow"

            # Soru türü tercihi
            if additional_data and "question_interactions" in additional_data:
                # Gelecekte mouse movements, pause times gibi verilerle analiz edilebilir
                pass

            # Güven paterni
            topic_performance = result.metadata.get("topic_performance", {})
            if topic_performance:
                scores = list(topic_performance.values())
                if max(scores) - min(scores) > 0.4:
                    indicators["confidence_pattern"] = "variable"

        except Exception:
            pass

        return indicators

    async def search_resources(
        self,
        topic: str,
        learning_style: LearningStyle,
        level: KnowledgeLevel,
        language: str = "tr",
        limit: int = 20,
    ) -> list[LearningResource]:
        """
        Kaynak arama ve toplama

        Args:
            topic: Konu
            learning_style: Öğrenme stili
            level: Seviye
            language: Dil
            limit: Maksimum kaynak sayısı

        Returns:
            Kaynak listesi
        """
        # Input validation
        if not topic or not isinstance(topic, str):
            raise ValueError("topic must be a non-empty string")

        if not isinstance(learning_style, LearningStyle):
            raise ValueError("learning_style must be a LearningStyle enum")

        if not isinstance(level, KnowledgeLevel):
            raise ValueError("level must be a KnowledgeLevel enum")

        if limit <= 0:
            raise ValueError("limit must be a positive integer")

        resources = []

        try:
            # Kaynak tiplerini belirle (öğrenme stiline göre)
            resource_types = {
                LearningStyle.VISUAL: ["video", "infographic", "animation"],
                LearningStyle.AUDITORY: ["podcast", "audio", "lecture"],
                LearningStyle.READING: ["article", "book", "pdf", "blog"],
                LearningStyle.KINESTHETIC: ["interactive", "simulation", "project"],
                LearningStyle.MIXED: ["video", "article", "interactive", "quiz"],
            }

            preferred_types = resource_types.get(learning_style, ["video", "article"])

            # RAG'den ilgili kaynakları ara
            # Seviyeye göre sınav tipini belirle (BEGINNER/ELEMENTARY -> LGS, diğerleri -> YKS)
            exam_type = (
                "LGS"
                if level in [KnowledgeLevel.BEGINNER, KnowledgeLevel.ELEMENTARY]
                else "YKS"
            )
            rag_results = await rag_service.search_educational_content(
                query=topic, exam_type=exam_type, k=10
            )

            # RAG sonuçlarını kaynaklara dönüştür
            for result in rag_results:
                resources.append(
                    LearningResource(
                        resource_id=f"rag_{len(resources)}",
                        title=result.get("metadata", {}).get("title", "İçerik"),
                        source="internal",
                        url="",
                        resource_type=result.get("metadata", {}).get(
                            "content_type", "article"
                        ),
                        difficulty_level=level,
                        estimated_time=15,
                        language=language,
                        description=result["content"][:200],
                        tags=[topic],
                        metadata=result.get("metadata", {}),
                    )
                )

            # YouTube'dan video kaynakları ara (görsel öğrenme stili için)
            if "video" in preferred_types:
                try:
                    # Seviyeye göre grade level belirle
                    grade_level = None
                    if level in [KnowledgeLevel.BEGINNER, KnowledgeLevel.ELEMENTARY]:
                        grade_level = "8"  # LGS seviyesi
                    elif level in [
                        KnowledgeLevel.INTERMEDIATE,
                        KnowledgeLevel.ADVANCED,
                    ]:
                        grade_level = "11"  # YKS seviyesi

                    youtube_videos = await youtube_service.search_educational_videos(
                        query=topic,
                        grade_level=grade_level,
                        language=language,
                        max_results=min(
                            limit // 2, 10
                        ),  # Toplam limitin yarısı kadar YouTube videosu
                    )

                    # YouTube videolarını kaynaklara dönüştür
                    for video in youtube_videos:
                        resources.append(
                            LearningResource(
                                resource_id=f"youtube_{video.video_id}",
                                title=video.title,
                                source="YouTube",
                                url=f"https://www.youtube.com/watch?v={video.video_id}",
                                resource_type="video",
                                difficulty_level=level,
                                estimated_time=self._parse_youtube_duration_to_minutes(
                                    video.duration
                                ),
                                language=video.language,
                                description=video.description[:200]
                                if video.description
                                else video.title,
                                tags=video.tags + [topic],
                                rating=video.educational_score,
                                metadata={
                                    "channel_name": video.channel_name,
                                    "channel_id": video.channel_id,
                                    "view_count": video.view_count,
                                    "like_count": video.like_count,
                                    "published_at": video.published_at.isoformat(),
                                    "caption_available": video.caption_available,
                                    "educational_score": video.educational_score,
                                    "thumbnail_url": video.thumbnail_url,
                                },
                            )
                        )

                    logger.info(
                        f"Found {len(youtube_videos)} YouTube videos for topic: {topic}"
                    )

                except Exception as e:
                    logger.warning(f"YouTube search failed for topic {topic}: {e!s}")
                    # YouTube hatası durumunda devam et

            # Khan Academy'den yapılandırılmış içerik ara
            try:
                # Seviyeye göre grade level belirle
                grade_level = None
                if level in [KnowledgeLevel.BEGINNER, KnowledgeLevel.ELEMENTARY]:
                    grade_level = "8"  # LGS seviyesi
                elif level in [KnowledgeLevel.INTERMEDIATE]:
                    grade_level = "10"  # Lise orta seviye
                elif level in [KnowledgeLevel.ADVANCED, KnowledgeLevel.EXPERT]:
                    grade_level = "12"  # Lise ileri seviye

                # Konu için uygun subject belirle
                subject = self._map_topic_to_subject(topic)

                khan_courses = await khan_academy_service.search_courses(
                    subject=subject,
                    grade_level=grade_level,
                    language=language,
                    limit=min(
                        limit // 3, 5
                    ),  # Toplam limitin 1/3'ü kadar Khan Academy içeriği
                )

                # Khan Academy kurslarını kaynaklara dönüştür
                for course in khan_courses:
                    # Her kurs için temel kaynak oluştur
                    resources.append(
                        LearningResource(
                            resource_id=f"khan_course_{course.course_id}",
                            title=course.title,
                            source="Khan Academy",
                            url=f"https://tr.khanacademy.org/course/{course.course_id}",
                            resource_type="course",
                            difficulty_level=level,
                            estimated_time=int(
                                course.estimated_hours * 60
                            ),  # Saati dakikaya çevir
                            language=course.language,
                            description=course.description[:200]
                            if course.description
                            else course.title,
                            tags=course.topics + [topic, subject],
                            rating=0.9,  # Khan Academy yüksek kalite
                            metadata={
                                "subject": course.subject,
                                "grade_level": course.grade_level,
                                "total_lessons": course.total_lessons,
                                "difficulty": course.difficulty,
                                "prerequisites": course.prerequisites,
                                "skills": course.skills,
                                "topics": course.topics,
                            },
                        )
                    )

                    # Kurs içeriğini de al (lesson'lar)
                    try:
                        lessons = await khan_academy_service.get_course_content(
                            course.course_id
                        )
                        for lesson in lessons[:3]:  # Her kurstan en fazla 3 lesson
                            resources.append(
                                LearningResource(
                                    resource_id=f"khan_lesson_{lesson.lesson_id}",
                                    title=lesson.title,
                                    source="Khan Academy",
                                    url=lesson.video_url
                                    or lesson.exercise_url
                                    or lesson.article_url
                                    or "",
                                    resource_type=lesson.content_type,
                                    difficulty_level=level,
                                    estimated_time=lesson.duration_minutes,
                                    language=language,
                                    description=lesson.description[:200]
                                    if lesson.description
                                    else lesson.title,
                                    tags=[topic, subject, lesson.content_type],
                                    rating=0.85,
                                    metadata={
                                        "course_id": lesson.course_id,
                                        "mastery_points": lesson.mastery_points,
                                        "content_type": lesson.content_type,
                                        "difficulty": lesson.difficulty,
                                    },
                                )
                            )
                    except Exception as lesson_error:
                        logger.warning(
                            f"Failed to get lessons for course {course.course_id}: {lesson_error!s}"
                        )

                logger.info(
                    f"Found {len(khan_courses)} Khan Academy courses for topic: {topic}"
                )

            except Exception as e:
                logger.warning(f"Khan Academy search failed for topic {topic}: {e!s}")
                # Khan Academy hatası durumunda devam et

            # OER (Open Educational Resources) kaynaklarını ara
            try:
                # Seviyeye göre educational level belirle
                educational_level = None
                if level in [KnowledgeLevel.BEGINNER, KnowledgeLevel.ELEMENTARY]:
                    educational_level = "K-12"
                elif level in [KnowledgeLevel.INTERMEDIATE, KnowledgeLevel.ADVANCED]:
                    educational_level = "undergraduate"
                elif level == KnowledgeLevel.EXPERT:
                    educational_level = "graduate"

                # Öğrenme stiline göre content type belirle
                preferred_oer_types = []
                if learning_style == LearningStyle.VISUAL:
                    preferred_oer_types = ["video", "interactive", "image"]
                elif learning_style == LearningStyle.AUDITORY:
                    preferred_oer_types = ["audio", "video"]
                elif learning_style == LearningStyle.READING:
                    preferred_oer_types = ["article", "document", "course"]
                elif learning_style == LearningStyle.KINESTHETIC:
                    preferred_oer_types = ["interactive", "simulation", "activity"]
                else:
                    preferred_oer_types = ["course", "video", "article"]

                # Her content type için arama yap
                for content_type in preferred_oer_types[:2]:  # En fazla 2 tür
                    oer_resources = await oer_service.search_oer_resources(
                        query=topic,
                        subject=subject,
                        educational_level=educational_level,
                        content_type=content_type,
                        language=language,
                        limit=3,  # Her türden 3 kaynak
                    )

                    # OER kaynaklarını learning resource'a dönüştür
                    for oer_resource in oer_resources:
                        resources.append(
                            LearningResource(
                                resource_id=f"oer_{oer_resource.resource_id}",
                                title=oer_resource.title,
                                source=oer_resource.source_platform,
                                url=oer_resource.url,
                                resource_type=oer_resource.content_type,
                                difficulty_level=level,
                                estimated_time=self._estimate_oer_time(oer_resource),
                                language=oer_resource.language,
                                description=oer_resource.description[:200]
                                if oer_resource.description
                                else oer_resource.title,
                                tags=oer_resource.tags + [topic, subject],
                                rating=oer_resource.educational_quality_score,
                                metadata={
                                    "source_platform": oer_resource.source_platform,
                                    "educational_level": oer_resource.educational_level,
                                    "license_type": oer_resource.license_type,
                                    "author": oer_resource.author,
                                    "institution": oer_resource.institution,
                                    "file_formats": oer_resource.file_formats,
                                    "view_count": oer_resource.view_count,
                                    "download_count": oer_resource.download_count,
                                    "educational_quality_score": oer_resource.educational_quality_score,
                                    "thumbnail_url": oer_resource.thumbnail_url,
                                },
                            )
                        )

                logger.info(f"Found OER resources for topic: {topic}")

            except Exception as e:
                logger.warning(f"OER search failed for topic {topic}: {e!s}")
                # OER hatası durumunda devam et

            # Harici kaynak önerileri (simüle edilmiş)
            # Gerçek uygulamada YouTube API, Khan Academy API vs. kullanılacak
            external_sources = [
                {
                    "title": f"{topic} - Khan Academy Türkçe",
                    "source": "Khan Academy",
                    "url": f"https://tr.khanacademy.org/search?q={topic}",
                    "type": "video",
                    "time": 20,
                },
                {
                    "title": f"{topic} - YouTube Eğitim",
                    "source": "YouTube",
                    "url": f"https://youtube.com/results?q={topic}+ders",
                    "type": "video",
                    "time": 15,
                },
                {
                    "title": f"{topic} - Wikipedia",
                    "source": "Wikipedia",
                    "url": f"https://tr.wikipedia.org/wiki/{topic}",
                    "type": "article",
                    "time": 10,
                },
                {
                    "title": f"{topic} - EBA",
                    "source": "EBA",
                    "url": f"https://eba.gov.tr/search?q={topic}",
                    "type": "interactive",
                    "time": 25,
                },
            ]

            # Öğrenme stiline göre filtrele ve ekle
            for source in external_sources:
                if source["type"] in preferred_types:
                    resources.append(
                        LearningResource(
                            resource_id=f"ext_{len(resources)}",
                            title=source["title"],
                            source=source["source"],
                            url=source["url"],
                            resource_type=source["type"],
                            difficulty_level=level,
                            estimated_time=source["time"],
                            language=language,
                            description=f"{topic} konusunda {source['source']} kaynağı",
                            tags=[topic, source["source"]],
                        )
                    )

            # Öğrenme stiline göre içerikleri filtrele ve sırala
            # Önce kaynakları dict formatına çevir
            resource_dicts = []
            for resource in resources:
                resource_dict = {
                    "resource_id": resource.resource_id,
                    "title": resource.title,
                    "source": resource.source,
                    "url": resource.url,
                    "content_type": resource.resource_type,
                    "difficulty_level": resource.difficulty_level.value,
                    "estimated_time": resource.estimated_time,
                    "language": resource.language,
                    "description": resource.description,
                    "tags": resource.tags,
                    "rating": resource.rating,
                    "metadata": resource.metadata or {},
                }
                resource_dicts.append(resource_dict)

            # Öğrenme stiline göre filtrele ve sırala (student_id gerekli, burada genel stil kullan)
            # Bu method'da student_id yok, bu yüzden genel stil filtrelemesi yap
            style_filtered_resources = []
            for resource_dict in resource_dicts:
                content_type = resource_dict["content_type"]

                # İçerik türünün öğrenme stili ile uyumunu kontrol et
                style_match_score = self._calculate_style_match_score(
                    content_type, learning_style
                )

                if style_match_score >= 0.3:  # Minimum eşik
                    resource_dict["style_score"] = style_match_score
                    resource_dict["style_match"] = self._get_style_match_description(
                        style_match_score
                    )
                    style_filtered_resources.append(resource_dict)

            # Stil skoruna göre sırala
            style_filtered_resources.sort(
                key=lambda x: x.get("style_score", 0), reverse=True
            )

            # Dict'leri tekrar LearningResource'a çevir
            filtered_learning_resources = []
            for resource_dict in style_filtered_resources[:limit]:
                filtered_learning_resources.append(
                    LearningResource(
                        resource_id=resource_dict["resource_id"],
                        title=resource_dict["title"],
                        source=resource_dict["source"],
                        url=resource_dict["url"],
                        resource_type=resource_dict["content_type"],
                        difficulty_level=KnowledgeLevel(
                            resource_dict["difficulty_level"]
                        ),
                        estimated_time=resource_dict["estimated_time"],
                        language=resource_dict["language"],
                        description=resource_dict["description"],
                        tags=resource_dict["tags"],
                        rating=resource_dict.get("rating"),
                        metadata=resource_dict.get("metadata", {}),
                    )
                )

            logger.info(
                f"Found {len(resources)} resources, filtered to {len(filtered_learning_resources)} based on learning style {learning_style.value}"
            )
            return filtered_learning_resources

        except Exception as e:
            logger.error(f"Resource search error: {e!s}")
            raise

    async def _assign_questions_to_phases(
        self, phases: list[dict], subject: str, knowledge_level: str
    ) -> list[dict]:
        """
        Her faz için soru bankasından gerçek sorular ata.
        ZPD seviyesine göre optimal zorluk + faz bazlı artan zorluk.
        İlk fazlar kolay, son fazlar zor (progressive difficulty).
        """
        try:
            from sqlalchemy import func as sa_func
            from sqlalchemy import select

            from core.database import get_db_session_context
            from models.question_bank import QuestionBankItem

            # Ordered difficulty levels for progressive ramping
            ALL_DIFFICULTIES = ["VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD"]

            # Base ZPD index from knowledge level
            _zpd_base = {
                "beginner": 0,  # starts at VERY_EASY
                "elementary": 1,  # starts at EASY
                "intermediate": 2,  # starts at MEDIUM
                "advanced": 3,  # starts at HARD
                "expert": 4,  # starts at VERY_HARD
            }
            base_idx = _zpd_base.get(knowledge_level, 2)

            total_phases = len(phases)

            async with get_db_session_context() as session:
                for i, phase in enumerate(phases):
                    # Progressive difficulty: shift up by phase position
                    # e.g. beginner with 4 phases: phase0=VERY_EASY/EASY, phase1=EASY/MEDIUM, ...
                    phase_shift = (
                        int((i / max(total_phases - 1, 1)) * 2)
                        if total_phases > 1
                        else 0
                    )
                    low = min(base_idx + phase_shift, len(ALL_DIFFICULTIES) - 1)
                    high = min(low + 1, len(ALL_DIFFICULTIES) - 1)
                    target_difficulties = list(
                        set([ALL_DIFFICULTIES[low], ALL_DIFFICULTIES[high]])
                    )

                    query = (
                        select(QuestionBankItem.id, QuestionBankItem.difficulty_level)
                        .where(
                            QuestionBankItem.is_active == True,
                            QuestionBankItem.subject_area == subject.upper(),
                            QuestionBankItem.difficulty_level.in_(target_difficulties),
                        )
                        .order_by(sa_func.random())
                        .limit(10)
                    )

                    result = await session.execute(query)
                    questions = result.all()

                    phase["quiz"] = {
                        "question_ids": [str(q.id) for q in questions],
                        "question_count": len(questions),
                        "passing_score": 60,
                        "difficulty_range": target_difficulties,
                    }

                    logger.info(
                        f"Phase {i + 1}/{total_phases} '{phase.get('title', '?')}': "
                        f"{len(questions)} questions (difficulty: {target_difficulties})"
                    )

        except Exception as e:
            logger.warning(f"Could not assign questions to phases: {e}")

        return phases

    async def create_learning_path(
        self, student_id: str, goal: str, duration_weeks: int = 4
    ) -> LearningPath:
        """
        Kişiselleştirilmiş öğrenme yolu oluştur.
        Sınav geçmişi varsa zayıf konulara öncelik verir.
        Soru bankasından ZPD-uyumlu sorular atar.
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        if not goal or not isinstance(goal, str):
            raise ValueError("goal must be a non-empty string")

        if duration_weeks <= 0:
            raise ValueError("duration_weeks must be a positive integer")

        try:
            # Öğrenci profilini al
            profile = self.profiles.get(student_id)
            if not profile:
                profile = await self.analyze_student(student_id, {"goal": goal})

            # Sınav geçmişini al (Faz 2 — gerçek veri ile LLM prompt zenginleştirme)
            exam_history = profile.metadata.get("analysis", {}).get("exam_history", {})
            exam_context = ""
            if exam_history.get("has_data"):
                weak = ", ".join(exam_history.get("weak_topics", [])) or "Belirlenemedi"
                strong = (
                    ", ".join(exam_history.get("strong_topics", [])) or "Belirlenemedi"
                )
                exam_context = f"""

            ÖĞRENCİNİN SINAV GEÇMİŞİ (gerçek veri):
            - Genel doğru oranı: %{int(exam_history["overall_accuracy"] * 100)}
            - Zayıf konular: {weak}
            - Güçlü konular: {strong}
            - Toplam sınav: {exam_history.get("exam_count", 0)}

            ZAYIF konulara öncelik veren bir plan oluştur.
            Güçlü konuları pekiştirme olarak dahil et."""

            # LLM ile öğrenme planı oluştur
            planning_prompt = f"""
            Öğrenci için öğrenme planı oluştur:

            Hedef: {goal}
            Seviye: {profile.knowledge_level.value}
            Öğrenme Stili: {profile.learning_style.value}
            Süre: {duration_weeks} hafta
            Günlük Çalışma Süresi: {profile.available_time} dakika
            {exam_context}

            Aşamalı bir öğrenme planı oluştur. Her aşama için:
            1. Konu başlığı
            2. Hedefler
            3. Önerilen süre
            4. Önkoşullar

            JSON formatında yanıtla:
            {{
                "phases": [
                    {{
                        "phase_number": 1,
                        "title": "...",
                        "objectives": [...],
                        "duration_days": ...,
                        "prerequisites": [...],
                        "topics": [...]
                    }}
                ],
                "reasoning": "Plan açıklaması"
            }}
            """

            result = await llm_service.generate(
                prompt=planning_prompt, temperature=0.5, max_tokens=800
            )

            try:
                plan = json.loads(result) if isinstance(result, str) else result
                if not isinstance(plan, dict) or "phases" not in plan:
                    raise ValueError("Missing 'phases' in plan")
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.debug(f"JSON parsing failed for learning plan: {e}")
                plan = {
                    "phases": [
                        {
                            "phase_number": 1,
                            "title": "Temel Kavramlar",
                            "objectives": ["Temel kavramları öğrenme"],
                            "duration_days": 7,
                            "prerequisites": [],
                            "topics": [goal],
                        }
                    ],
                    "reasoning": "Standart öğrenme planı",
                }

            # Faz 3+4: Soru bankasından ZPD-uyumlu sorular ata
            phases = await self._assign_questions_to_phases(
                plan["phases"],
                subject=goal,
                knowledge_level=profile.knowledge_level.value,
            )

            # Kaynak arama devre dışı — external API'ler (YouTube/Khan/OER)
            # çalışmıyor (403/timeout), 12+ çağrı × timeout = 338s blokluyor.
            all_resources = []

            # Öğrenme yolu oluştur
            path_id = f"path_{student_id}_{datetime.now().timestamp()}"
            learning_path = LearningPath(
                path_id=path_id,
                student_profile=profile,
                resources=all_resources,
                total_time=sum([r.estimated_time for r in all_resources]),
                phases=phases,
                created_at=datetime.now(),
                reasoning=plan["reasoning"],
                metadata={
                    "goal": goal,
                    "duration_weeks": duration_weeks,
                    "plan": plan,
                    "exam_data_used": exam_history.get("has_data", False),
                    "questions_assigned": any(p.get("quiz") for p in phases),
                },
            )

            # Cache'e kaydet
            self.learning_paths[path_id] = learning_path

            logger.info(
                f"Learning path created: {path_id} (exam_data={exam_history.get('has_data', False)})"
            )
            return learning_path

        except Exception as e:
            logger.error(f"Create learning path error: {e!s}")
            raise

    async def adapt_learning_path(
        self, path_id: str, progress_data: dict[str, Any]
    ) -> LearningPath:
        """
        Öğrenme yolunu ilerlemeye göre adapte et

        Args:
            path_id: Öğrenme yolu ID
            progress_data: İlerleme verisi

        Returns:
            Güncellenmiş öğrenme yolu
        """
        try:
            # Mevcut yolu al
            path = self.learning_paths.get(path_id)
            if not path:
                raise ValueError(f"Learning path not found: {path_id}")

            # İlerleme analizi
            completed_resources = progress_data.get("completed_resources", [])
            quiz_scores = progress_data.get("quiz_scores", {})
            feedback = progress_data.get("feedback", "")

            # Ortalama performans hesapla
            avg_score = (
                sum(quiz_scores.values()) / len(quiz_scores) if quiz_scores else 0
            )

            # Adaptasyon kararı
            if avg_score < 50:
                # Daha basit kaynaklar ekle
                logger.info(f"Adding easier resources for path {path_id}")
                # Seviyeyi düşür
                new_level = KnowledgeLevel.BEGINNER
            elif avg_score > 80:
                # Daha zor kaynaklar ekle
                logger.info(f"Adding advanced resources for path {path_id}")
                # Seviyeyi yükselt
                new_level = KnowledgeLevel.ADVANCED
            else:
                # Mevcut seviyede devam
                new_level = path.student_profile.knowledge_level

            # Yeni kaynaklar ekle (gerekirse)
            if new_level != path.student_profile.knowledge_level:
                # Ek kaynaklar ara
                additional_resources = await self.search_resources(
                    topic=path.student_profile.learning_goal,
                    learning_style=path.student_profile.learning_style,
                    level=new_level,
                    limit=3,
                )
                path.resources.extend(additional_resources)
                path.total_time = sum([r.estimated_time for r in path.resources])

            # Metadata güncelle
            path.metadata["last_adapted"] = datetime.now().isoformat()
            path.metadata["adaptation_reason"] = f"Performance: {avg_score:.1f}%"

            return path

        except Exception as e:
            logger.error(f"Adapt learning path error: {e!s}")
            raise

    def get_student_profile(self, student_id: str) -> StudentProfile | None:
        """Öğrenci profilini getir"""
        return self.profiles.get(student_id)

    def get_learning_path(self, path_id: str) -> LearningPath | None:
        """Öğrenme yolunu getir"""
        return self.learning_paths.get(path_id)

    def list_student_paths(self, student_id: str) -> list[LearningPath]:
        """Öğrencinin tüm öğrenme yollarını listele"""
        paths = []
        for path in self.learning_paths.values():
            if path.student_profile.student_id == student_id:
                paths.append(path)
        return paths

    # Learning Style Detection Methods

    async def create_learning_style_questionnaire(
        self, student_id: str
    ) -> dict[str, Any]:
        """
        Öğrenme stili anketi oluştur

        Args:
            student_id: Öğrenci ID

        Returns:
            Anket verisi
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        try:
            questions = (
                await learning_style_detector.create_learning_style_questionnaire(
                    student_id
                )
            )

            questionnaire_data = {
                "questionnaire_id": f"style_questionnaire_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "questionnaire_type": "learning_style_detection",
                "questions": questions,
                "estimated_time_minutes": len(questions) * 1,  # 1 dakika per soru
                "instructions": [
                    "Her soruyu dikkatlice okuyun",
                    "Size en uygun seçeneği işaretleyin",
                    "Doğru veya yanlış cevap yoktur",
                    "İlk içgüdünüzle cevap verin",
                ],
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "purpose": "learning_style_detection",
                    "total_questions": len(questions),
                },
            }

            logger.info(
                f"Learning style questionnaire created for student {student_id}"
            )
            return questionnaire_data

        except Exception as e:
            logger.error(f"Create learning style questionnaire error: {e!s}")
            raise

    async def analyze_learning_style_responses(
        self,
        student_id: str,
        questionnaire_id: str,
        questions: list[dict[str, Any]],
        answers: list[str],
    ) -> dict[str, Any]:
        """
        Öğrenme stili anket cevaplarını analiz et

        Args:
            student_id: Öğrenci ID
            questionnaire_id: Anket ID
            questions: Sorular
            answers: Cevaplar

        Returns:
            Analiz sonucu
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        if not questions or not answers:
            raise ValueError("questions and answers are required")

        if len(questions) != len(answers):
            raise ValueError("questions and answers must have the same length")

        try:
            # Learning style detector ile analiz et
            profile = await learning_style_detector.analyze_questionnaire_responses(
                student_id=student_id, questions=questions, answers=answers
            )

            # Mevcut öğrenci profilini güncelle
            if student_id in self.profiles:
                student_profile = self.profiles[student_id]
                student_profile.learning_style = profile.primary_style
                student_profile.metadata["learning_style_profile"] = {
                    "primary_style": profile.primary_style.value,
                    "secondary_style": profile.secondary_style.value
                    if profile.secondary_style
                    else None,
                    "confidence_level": profile.confidence_level,
                    "detection_method": "questionnaire",
                    "detected_at": datetime.now().isoformat(),
                }

            # Sonuç verisi oluştur
            result_data = {
                "analysis_id": f"style_analysis_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "questionnaire_id": questionnaire_id,
                "primary_learning_style": profile.primary_style.value,
                "secondary_learning_style": profile.secondary_style.value
                if profile.secondary_style
                else None,
                "style_scores": {
                    style.value: score for style, score in profile.style_scores.items()
                },
                "confidence_level": profile.confidence_level,
                "behavioral_patterns": profile.behavioral_patterns,
                "preferences": profile.preferences,
                "recommendations": [
                    f"İçerik türü tercihiniz: {', '.join(profile.preferences.get('primary_content_types', []))}",
                    f"Önerilen format: {', '.join(profile.preferences.get('recommended_formats', []))}",
                    f"Etkileşim tercihi: {', '.join(profile.preferences.get('interaction_preferences', []))}",
                ],
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "total_questions": len(questions),
                    "analysis_method": "weighted_scoring",
                    "detection_confidence": profile.confidence_level,
                },
            }

            logger.info(
                f"Learning style analysis completed for student {student_id}: {profile.primary_style.value}"
            )
            return result_data

        except Exception as e:
            logger.error(f"Analyze learning style responses error: {e!s}")
            raise

    def record_learning_behavior(
        self, student_id: str, content_type: str, interaction_data: dict[str, Any]
    ):
        """
        Öğrenme davranışını kaydet

        Args:
            student_id: Öğrenci ID
            content_type: İçerik türü
            interaction_data: Etkileşim verisi
        """
        try:
            # Farklı davranışsal göstergeleri kaydet
            if "time_spent_seconds" in interaction_data:
                # Zaman harcama verisi (normalize edilmiş)
                time_spent = interaction_data["time_spent_seconds"]
                normalized_time = min(time_spent / 3600, 1.0)  # 1 saat = 1.0

                learning_style_detector.record_behavioral_data(
                    student_id=student_id,
                    indicator=BehavioralIndicator.TIME_SPENT,
                    content_type=content_type,
                    value=normalized_time,
                    context={"raw_time_seconds": time_spent},
                )

            if "engagement_score" in interaction_data:
                # Etkileşim seviyesi (0-1 arası)
                engagement = max(0.0, min(1.0, interaction_data["engagement_score"]))

                learning_style_detector.record_behavioral_data(
                    student_id=student_id,
                    indicator=BehavioralIndicator.ENGAGEMENT_LEVEL,
                    content_type=content_type,
                    value=engagement,
                    context=interaction_data,
                )

            if "completion_rate" in interaction_data:
                # Tamamlama oranı (0-1 arası)
                completion = max(0.0, min(1.0, interaction_data["completion_rate"]))

                learning_style_detector.record_behavioral_data(
                    student_id=student_id,
                    indicator=BehavioralIndicator.COMPLETION_RATE,
                    content_type=content_type,
                    value=completion,
                    context=interaction_data,
                )

            if "preference_rating" in interaction_data:
                # İçerik tercihi (0-1 arası)
                preference = max(
                    0.0, min(1.0, interaction_data["preference_rating"] / 5.0)
                )

                learning_style_detector.record_behavioral_data(
                    student_id=student_id,
                    indicator=BehavioralIndicator.CONTENT_PREFERENCE,
                    content_type=content_type,
                    value=preference,
                    context=interaction_data,
                )

            logger.debug(
                f"Recorded learning behavior for student {student_id}: {content_type}"
            )

        except Exception as e:
            logger.error(f"Record learning behavior error: {e!s}")

    async def analyze_behavioral_learning_style(
        self, student_id: str
    ) -> dict[str, Any] | None:
        """
        Davranışsal verilerden öğrenme stilini analiz et

        Args:
            student_id: Öğrenci ID

        Returns:
            Analiz sonucu (yeterli veri varsa)
        """
        # Input validation
        if not student_id or not isinstance(student_id, str):
            raise ValueError("student_id must be a non-empty string")

        try:
            # Davranışsal analiz yap
            profile = await learning_style_detector.analyze_behavioral_patterns(
                student_id
            )

            if not profile:
                return None

            # Mevcut öğrenci profilini güncelle
            if student_id in self.profiles:
                student_profile = self.profiles[student_id]
                student_profile.learning_style = profile.primary_style
                student_profile.metadata["learning_style_profile"] = {
                    "primary_style": profile.primary_style.value,
                    "secondary_style": profile.secondary_style.value
                    if profile.secondary_style
                    else None,
                    "confidence_level": profile.confidence_level,
                    "detection_method": "behavioral_analysis",
                    "detected_at": datetime.now().isoformat(),
                }

            # Sonuç verisi oluştur
            result_data = {
                "analysis_id": f"behavioral_analysis_{student_id}_{datetime.now().timestamp()}",
                "student_id": student_id,
                "primary_learning_style": profile.primary_style.value,
                "secondary_learning_style": profile.secondary_style.value
                if profile.secondary_style
                else None,
                "style_scores": {
                    style.value: score for style, score in profile.style_scores.items()
                },
                "confidence_level": profile.confidence_level,
                "behavioral_patterns": profile.behavioral_patterns,
                "preferences": profile.preferences,
                "data_points_analyzed": profile.metadata.get("data_points", 0),
                "recommendations": [
                    f"Davranışsal verilerinize göre {profile.primary_style.value} öğrenme stiline sahipsiniz",
                    f"En çok etkileşim kurduğunuz içerik türleri: {', '.join(profile.preferences.get('primary_content_types', []))}",
                    f"Önerilen çalışma süresi: {profile.preferences.get('pacing_preferences', {}).get('preferred_duration', '15 dakika')}",
                ],
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "analysis_method": "behavioral_analysis",
                    "detection_confidence": profile.confidence_level,
                    "data_based": True,
                },
            }

            logger.info(
                f"Behavioral learning style analysis completed for student {student_id}: {profile.primary_style.value}"
            )
            return result_data

        except Exception as e:
            logger.error(f"Analyze behavioral learning style error: {e!s}")
            raise

    async def search_and_rank_resources_unified(
        self,
        student_id: str,
        topic: str,
        level: KnowledgeLevel,
        language: str = "tr",
        limit: int = 20,
        learning_goals: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Birleşik algoritma ile kaynakları ara, sırala ve puanla

        Args:
            student_id: Öğrenci ID
            topic: Konu
            level: Seviye
            language: Dil
            limit: Maksimum kaynak sayısı
            learning_goals: Öğrenme hedefleri

        Returns:
            Puanlanmış ve sıralanmış kaynak listesi
        """
        try:
            # Öğrenci profilini al
            student_profile = self.profiles.get(student_id)
            learning_style = (
                student_profile.learning_style
                if student_profile
                else LearningStyle.MIXED
            )

            # Temel kaynak araması yap
            resources = await self.search_resources(
                topic=topic,
                learning_style=learning_style,
                level=level,
                language=language,
                limit=limit * 3,  # Daha fazla kaynak al, sonra filtrele
            )

            # Kaynakları dict formatına çevir
            resource_dicts = []
            for resource in resources:
                resource_dict = {
                    "resource_id": resource.resource_id,
                    "title": resource.title,
                    "source": resource.source,
                    "url": resource.url,
                    "content_type": resource.resource_type,
                    "difficulty_level": resource.difficulty_level.value,
                    "estimated_time": resource.estimated_time,
                    "language": resource.language,
                    "description": resource.description,
                    "tags": resource.tags,
                    "rating": resource.rating,
                    "metadata": resource.metadata or {},
                }
                resource_dicts.append(resource_dict)

            # Öğrenci profili dict formatına çevir
            profile_dict = None
            if student_profile:
                profile_dict = {
                    "student_id": student_id,
                    "learning_style": student_profile.learning_style.value,
                    "knowledge_level": student_profile.knowledge_level.value,
                    "learning_goal": student_profile.learning_goal,
                    "interests": student_profile.interests,
                    "available_time": student_profile.available_time,
                }

            # Birleşik algoritma ile sırala
            scored_resources = await unified_resource_ranker.rank_resources(
                resources=resource_dicts,
                student_profile=profile_dict,
                topic=topic,
                learning_goals=learning_goals,
            )

            # En iyi kaynakları seç
            top_resources = scored_resources[:limit]

            # Sonuçları formatla
            result_resources = []
            for scored_resource in top_resources:
                # Orijinal kaynak bilgilerini al
                original_resource = next(
                    (
                        r
                        for r in resource_dicts
                        if r["resource_id"] == scored_resource.resource_id
                    ),
                    None,
                )

                if original_resource:
                    result_resource = original_resource.copy()
                    result_resource.update(
                        {
                            "quality_score": scored_resource.quality_score.overall_score,
                            "relevance_score": scored_resource.relevance_score.overall_relevance,
                            "final_score": scored_resource.final_score,
                            "ranking_position": scored_resource.ranking_position,
                            "recommendation_strength": scored_resource.recommendation_strength,
                            "quality_reasoning": scored_resource.quality_score.reasoning,
                            "relevance_reasoning": scored_resource.relevance_score.reasoning,
                            "enriched_metadata": scored_resource.metadata_enriched,
                        }
                    )
                    result_resources.append(result_resource)

            logger.info(
                f"Unified ranking: {len(resources)} resources -> {len(result_resources)} top results for student {student_id}"
            )
            return result_resources

        except Exception as e:
            logger.error(f"Search and rank resources unified error: {e!s}")
            # Fallback: basit arama yap
            fallback_resources = await self.search_resources(
                topic, learning_style, level, language, limit
            )
            return [
                {
                    "resource_id": r.resource_id,
                    "title": r.title,
                    "source": r.source,
                    "url": r.url,
                    "content_type": r.resource_type,
                    "difficulty_level": r.difficulty_level.value,
                    "estimated_time": r.estimated_time,
                    "language": r.language,
                    "description": r.description,
                    "tags": r.tags,
                    "rating": r.rating,
                    "metadata": r.metadata or {},
                    "final_score": 0.7,  # Varsayılan skor
                    "recommendation_strength": "moderate",
                }
                for r in fallback_resources
            ]

    async def search_and_filter_resources_by_style(
        self,
        student_id: str,
        topic: str,
        level: KnowledgeLevel,
        language: str = "tr",
        limit: int = 20,
    ) -> list[LearningResource]:
        """
        Öğrenci profiline göre kaynakları ara ve filtrele

        Args:
            student_id: Öğrenci ID
            topic: Konu
            level: Seviye
            language: Dil
            limit: Maksimum kaynak sayısı

        Returns:
            Filtrelenmiş kaynak listesi
        """
        try:
            # Öğrenci profilini al
            student_profile = self.profiles.get(student_id)
            learning_style = (
                student_profile.learning_style
                if student_profile
                else LearningStyle.MIXED
            )

            # Temel kaynak araması yap
            resources = await self.search_resources(
                topic=topic,
                learning_style=learning_style,
                level=level,
                language=language,
                limit=limit * 2,  # Daha fazla kaynak al, sonra filtrele
            )

            # Öğrenme stili profilini al
            style_profile = learning_style_detector.get_learning_style_profile(
                student_id
            )

            if style_profile:
                # Kaynakları dict formatına çevir
                resource_dicts = []
                for resource in resources:
                    resource_dict = {
                        "resource_id": resource.resource_id,
                        "title": resource.title,
                        "source": resource.source,
                        "url": resource.url,
                        "content_type": resource.resource_type,
                        "difficulty_level": resource.difficulty_level.value,
                        "estimated_time": resource.estimated_time,
                        "language": resource.language,
                        "description": resource.description,
                        "tags": resource.tags,
                        "rating": resource.rating,
                        "metadata": resource.metadata or {},
                    }
                    resource_dicts.append(resource_dict)

                # Öğrenme stiline göre filtrele ve sırala
                filtered_dicts = learning_style_detector.filter_and_rank_content(
                    student_id=student_id, content_list=resource_dicts
                )

                # Dict'leri tekrar LearningResource'a çevir
                filtered_resources = []
                for resource_dict in filtered_dicts[:limit]:
                    filtered_resources.append(
                        LearningResource(
                            resource_id=resource_dict["resource_id"],
                            title=resource_dict["title"],
                            source=resource_dict["source"],
                            url=resource_dict["url"],
                            resource_type=resource_dict["content_type"],
                            difficulty_level=KnowledgeLevel(
                                resource_dict["difficulty_level"]
                            ),
                            estimated_time=resource_dict["estimated_time"],
                            language=resource_dict["language"],
                            description=resource_dict["description"],
                            tags=resource_dict["tags"],
                            rating=resource_dict.get("rating"),
                            metadata=resource_dict.get("metadata", {}),
                        )
                    )

                logger.info(
                    f"Filtered {len(resources)} resources to {len(filtered_resources)} based on student {student_id} learning style"
                )
                return filtered_resources
            # Stil profili yoksa orijinal kaynakları döndür
            return resources[:limit]

        except Exception as e:
            logger.error(f"Search and filter resources by style error: {e!s}")
            # Hata durumunda temel arama yap
            return await self.search_resources(
                topic, learning_style, level, language, limit
            )

    def get_style_based_content_recommendations(
        self, student_id: str, available_content_types: list[str]
    ) -> list[dict[str, Any]]:
        """
        Öğrenme stiline göre içerik önerileri

        Args:
            student_id: Öğrenci ID
            available_content_types: Mevcut içerik türleri

        Returns:
            Stil tabanlı öneriler
        """
        try:
            recommendations = learning_style_detector.get_style_based_recommendations(
                student_id=student_id, content_types=available_content_types
            )

            # Önerileri dict formatına çevir
            recommendation_list = []
            for rec in recommendations:
                recommendation_list.append(
                    {
                        "content_type": rec.content_type,
                        "priority_score": rec.priority,
                        "reasoning": rec.reasoning,
                        "adaptation_suggestions": rec.adaptation_suggestions,
                        "recommended": rec.priority > 0.5,
                    }
                )

            logger.info(
                f"Generated {len(recommendation_list)} style-based content recommendations for student {student_id}"
            )
            return recommendation_list

        except Exception as e:
            logger.error(f"Get style-based content recommendations error: {e!s}")
            return []

    def _calculate_style_match_score(
        self, content_type: str, learning_style: LearningStyle
    ) -> float:
        """İçerik türü ile öğrenme stili arasındaki uyum skorunu hesapla"""
        content_style_mapping = {
            "video": LearningStyle.VISUAL,
            "animation": LearningStyle.VISUAL,
            "infographic": LearningStyle.VISUAL,
            "image": LearningStyle.VISUAL,
            "diagram": LearningStyle.VISUAL,
            "audio": LearningStyle.AUDITORY,
            "podcast": LearningStyle.AUDITORY,
            "lecture": LearningStyle.AUDITORY,
            "music": LearningStyle.AUDITORY,
            "article": LearningStyle.READING,
            "text": LearningStyle.READING,
            "book": LearningStyle.READING,
            "pdf": LearningStyle.READING,
            "blog": LearningStyle.READING,
            "course": LearningStyle.READING,
            "interactive": LearningStyle.KINESTHETIC,
            "simulation": LearningStyle.KINESTHETIC,
            "project": LearningStyle.KINESTHETIC,
            "quiz": LearningStyle.KINESTHETIC,
            "exercise": LearningStyle.KINESTHETIC,
        }

        mapped_style = content_style_mapping.get(content_type)

        if not mapped_style:
            return 0.5  # Bilinmeyen içerik türü için orta skor

        if mapped_style == learning_style:
            return 1.0  # Tam uyum
        if learning_style == LearningStyle.MIXED:
            return 0.8  # Karma stil her şeyi kabul eder
        return 0.4  # Kısmi uyum

    def _get_style_match_description(self, score: float) -> str:
        """Stil uyum skorunu açıklamaya çevir"""
        if score >= 0.8:
            return "excellent"
        if score >= 0.6:
            return "good"
        if score >= 0.4:
            return "moderate"
        return "low"

    def _parse_youtube_duration_to_minutes(self, duration: str | None) -> int:
        """
        YouTube duration formatını dakikaya çevir

        Uses centralized ISO 8601 parser for consistent behavior.

        Args:
            duration: PT15M30S formatında süre (ISO 8601)

        Returns:
            Dakika cinsinden süre
        """
        # Use centralized parser for consistent ISO 8601 handling
        from agents.learning_path.utils.duration_parser import parse_iso8601_duration

        return parse_iso8601_duration(duration, default=10)

    def _map_topic_to_subject(self, topic: str) -> str:
        """
        Konuyu ana derse eşle

        Args:
            topic: Konu adı

        Returns:
            Ana ders adı
        """
        topic_lower = topic.lower()

        # Matematik konuları
        math_keywords = [
            "matematik",
            "cebir",
            "geometri",
            "trigonometri",
            "analiz",
            "türev",
            "integral",
            "denklem",
            "fonksiyon",
            "logaritma",
            "üstel",
            "matris",
            "vektör",
            "olasılık",
            "istatistik",
            "sayılar",
            "kesir",
            "oran",
            "orantı",
        ]

        # Fen bilimleri konuları
        science_keywords = [
            "fen",
            "fizik",
            "kimya",
            "biyoloji",
            "kuvvet",
            "hareket",
            "enerji",
            "madde",
            "atom",
            "molekül",
            "hücre",
            "genetik",
            "evrim",
            "ekosistem",
            "ışık",
            "ses",
            "elektrik",
            "manyetizma",
            "asit",
            "baz",
            "reaksiyon",
        ]

        # Türkçe konuları
        turkish_keywords = [
            "türkçe",
            "edebiyat",
            "dil",
            "gramer",
            "yazım",
            "noktalama",
            "paragraf",
            "metin",
            "şiir",
            "roman",
            "hikaye",
            "anlatım",
            "sözcük",
        ]

        # Tarih konuları
        history_keywords = [
            "tarih",
            "medeniyet",
            "devlet",
            "savaş",
            "antlaşma",
            "reform",
            "devrim",
            "osmanlı",
            "cumhuriyet",
            "atatürk",
            "milli",
            "bağımsızlık",
        ]

        # Coğrafya konuları
        geography_keywords = [
            "coğrafya",
            "harita",
            "iklim",
            "nüfus",
            "şehir",
            "kıta",
            "okyanus",
            "dağ",
            "nehir",
            "göl",
            "bölge",
            "ülke",
            "ekonomi",
            "tarım",
        ]

        # Eşleştirme yap
        if any(keyword in topic_lower for keyword in math_keywords):
            return "matematik"
        if any(keyword in topic_lower for keyword in science_keywords):
            if any(
                keyword in topic_lower
                for keyword in [
                    "fizik",
                    "kuvvet",
                    "hareket",
                    "enerji",
                    "ışık",
                    "ses",
                    "elektrik",
                ]
            ):
                return "fizik"
            if any(
                keyword in topic_lower
                for keyword in ["kimya", "atom", "molekül", "asit", "baz", "reaksiyon"]
            ):
                return "kimya"
            if any(
                keyword in topic_lower
                for keyword in ["biyoloji", "hücre", "genetik", "evrim", "ekosistem"]
            ):
                return "biyoloji"
            return "fen"
        if any(keyword in topic_lower for keyword in turkish_keywords):
            return "türkçe"
        if any(keyword in topic_lower for keyword in history_keywords):
            return "tarih"
        if any(keyword in topic_lower for keyword in geography_keywords):
            return "coğrafya"
        return "genel"  # Default

    # Chat Interface Methods

    async def process_chat_message(
        self, session_id: str, message: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """
        Chat mesajını işle

        Args:
            session_id: Oturum ID
            message: Kullanıcı mesajı
            user_id: Kullanıcı ID (opsiyonel)

        Returns:
            Chat yanıtı
        """
        try:
            # Chat interface ile mesajı işle
            response = await chat_interface.process_message(
                session_id, message, user_id
            )

            # Eğer eylem gerekiyorsa işle
            if response.metadata.get("action_required"):
                action = response.metadata["action_required"]

                if action == "start_learning_style_questionnaire":
                    # Öğrenme stili anketi başlat
                    questionnaire_data = await self.create_learning_style_questionnaire(
                        student_id=user_id or session_id
                    )
                    response.metadata["questionnaire"] = questionnaire_data

                elif action == "create_learning_path":
                    # Öğrenme yolu oluştur
                    collected_data = response.metadata.get("collected_data", {})
                    if collected_data:
                        # Önce profil oluştur
                        profile_data = {
                            "name": "Chat Kullanıcısı",
                            "grade": collected_data.get("grade", "9"),
                            "subjects": [collected_data.get("subject", "matematik")],
                            "goal": collected_data.get("subject", "genel öğrenme"),
                            "exam_target": collected_data.get("exam_target", ""),
                            "available_time": collected_data.get("available_time", 60),
                        }

                        student_id = user_id or session_id
                        await self.analyze_student(student_id, profile_data)

                        # Öğrenme yolu oluştur
                        learning_path = await self.create_learning_path(
                            student_id=student_id,
                            goal=collected_data.get("subject", "genel öğrenme"),
                            duration_weeks=4,
                        )

                        response.metadata["learning_path_created"] = {
                            "path_id": learning_path.path_id,
                            "total_resources": len(learning_path.resources),
                            "estimated_time": learning_path.total_time,
                        }

            # Yanıtı dict formatına çevir
            return {
                "message": response.message,
                "message_type": response.message_type.value,
                "suggested_actions": response.suggested_actions,
                "requires_input": response.requires_input,
                "metadata": response.metadata,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Process chat message error: {e!s}")
            return {
                "message": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
                "message_type": "assistant",
                "suggested_actions": [],
                "requires_input": True,
                "metadata": {"error": str(e)},
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }

    def get_chat_conversation_history(self, session_id: str) -> dict[str, Any] | None:
        """
        Chat konuşma geçmişini getir

        Args:
            session_id: Oturum ID

        Returns:
            Konuşma geçmişi
        """
        try:
            context = chat_interface.get_conversation_context(session_id)
            if not context:
                return None

            return {
                "session_id": session_id,
                "student_id": context.student_id,
                "current_state": context.current_state.value,
                "collected_data": context.collected_data,
                "conversation_history": [
                    {
                        "message_id": msg.message_id,
                        "message_type": msg.message_type.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata,
                    }
                    for msg in context.conversation_history
                ],
                "last_activity": context.last_activity.isoformat(),
            }

        except Exception as e:
            logger.error(f"Get chat conversation history error: {e!s}")
            return None

    def clear_chat_conversation(self, session_id: str) -> bool:
        """
        Chat konuşmasını temizle

        Args:
            session_id: Oturum ID

        Returns:
            Başarı durumu
        """
        try:
            chat_interface.clear_conversation(session_id)
            return True
        except Exception as e:
            logger.error(f"Clear chat conversation error: {e!s}")
            return False

    async def handle_chat_goal_setting(
        self, session_id: str, goal_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Chat üzerinden hedef belirleme

        Args:
            session_id: Oturum ID
            goal_data: Hedef verisi

        Returns:
            İşlem sonucu
        """
        try:
            context = chat_interface.get_conversation_context(session_id)
            if context:
                context.collected_data.update(goal_data)

                return {
                    "success": True,
                    "message": "Hedefin kaydedildi! Şimdi profil bilgilerini tamamlayalım.",
                    "next_step": "profile_creation",
                    "collected_data": context.collected_data,
                }
            return {"success": False, "error": "Konuşma bağlamı bulunamadı"}

        except Exception as e:
            logger.error(f"Handle chat goal setting error: {e!s}")
            return {"success": False, "error": str(e)}

    async def handle_chat_assessment_completion(
        self, session_id: str, assessment_results: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Chat üzerinden değerlendirme tamamlama

        Args:
            session_id: Oturum ID
            assessment_results: Değerlendirme sonuçları

        Returns:
            İşlem sonucu
        """
        try:
            context = chat_interface.get_conversation_context(session_id)
            if not context:
                return {"success": False, "error": "Konuşma bağlamı bulunamadı"}

            # Değerlendirme sonuçlarını kaydet
            context.collected_data["assessment_results"] = assessment_results

            # Sonuçlara göre öğrenme yolu önerisi
            knowledge_level = assessment_results.get("knowledge_level", "beginner")
            subject = context.collected_data.get("subject", "matematik")

            suggestion_message = f"""
            Değerlendirme tamamlandı! Sonuçlarına göre {subject} konusunda {knowledge_level} seviyedesin.
            
            Şimdi sana özel bir öğrenme yolu oluşturabilirim. Hazır mısın?
            """

            return {
                "success": True,
                "message": suggestion_message,
                "assessment_results": assessment_results,
                "next_step": "create_learning_path",
                "suggested_actions": [
                    {"text": "Öğrenme yolu oluştur", "action": "create_path"},
                    {"text": "Önce daha fazla bilgi ver", "action": "more_info"},
                ],
            }

        except Exception as e:
            logger.error(f"Handle chat assessment completion error: {e!s}")
            return {"success": False, "error": str(e)}

    async def get_chat_based_recommendations(
        self, session_id: str, request_type: str = "general"
    ) -> dict[str, Any]:
        """
        Chat tabanlı öneriler getir

        Args:
            session_id: Oturum ID
            request_type: Öneri türü

        Returns:
            Öneriler
        """
        try:
            context = chat_interface.get_conversation_context(session_id)
            if not context:
                return {"success": False, "error": "Konuşma bağlamı bulunamadı"}

            collected_data = context.collected_data
            student_id = context.student_id or session_id

            recommendations = []

            if request_type == "resources":
                # Kaynak önerileri
                subject = collected_data.get("subject", "matematik")

                # Öğrenci profili varsa stil tabanlı öneriler
                if student_id in self.profiles:
                    profile = self.profiles[student_id]
                    content_types = ["video", "article", "interactive", "course"]
                    style_recommendations = (
                        self.get_style_based_content_recommendations(
                            student_id, content_types
                        )
                    )
                    recommendations.extend(style_recommendations)

                # Genel kaynak önerileri
                general_resources = await self.search_resources(
                    topic=subject,
                    learning_style=LearningStyle.MIXED,
                    level=KnowledgeLevel.INTERMEDIATE,
                    limit=5,
                )

                for resource in general_resources:
                    recommendations.append(
                        {
                            "title": resource.title,
                            "source": resource.source,
                            "type": resource.resource_type,
                            "url": resource.url,
                            "estimated_time": resource.estimated_time,
                            "description": resource.description,
                        }
                    )

            elif request_type == "study_plan":
                # Çalışma planı önerileri
                available_time = collected_data.get("available_time", 60)
                subject = collected_data.get("subject", "matematik")

                recommendations = [
                    {
                        "type": "daily_schedule",
                        "title": "Günlük Çalışma Programı",
                        "description": f"{available_time} dakikalık günlük {subject} çalışma planı",
                        "details": [
                            "İlk 15 dakika: Konu tekrarı",
                            f"Sonraki {available_time - 30} dakika: Yeni konu öğrenme",
                            "Son 15 dakika: Soru çözümü",
                        ],
                    },
                    {
                        "type": "weekly_goals",
                        "title": "Haftalık Hedefler",
                        "description": f"{subject} için haftalık ilerleme hedefleri",
                        "details": [
                            "Haftada 2 yeni konu",
                            "Günde en az 10 soru",
                            "Hafta sonu genel tekrar",
                        ],
                    },
                ]

            return {
                "success": True,
                "recommendations": recommendations,
                "request_type": request_type,
                "based_on": collected_data,
            }

        except Exception as e:
            logger.error(f"Get chat based recommendations error: {e!s}")
            return {"success": False, "error": str(e)}

    # Form Interface Methods

    def get_profile_creation_form(self) -> dict[str, Any]:
        """
        Profil oluşturma formunu getir

        Returns:
            Form tanımı
        """
        try:
            form_def = form_interface.get_form_definition(FormType.PROFILE_CREATION)
            if not form_def:
                return {"success": False, "error": "Form tanımı bulunamadı"}

            return {
                "success": True,
                "form": {
                    "form_id": form_def.form_id,
                    "form_type": form_def.form_type.value,
                    "title": form_def.title,
                    "description": form_def.description,
                    "sections": [
                        {
                            "section_id": section.section_id,
                            "title": section.title,
                            "description": section.description,
                            "order": section.order,
                            "fields": [
                                {
                                    "field_id": field.field_id,
                                    "field_type": field.field_type.value,
                                    "label": field.label,
                                    "description": field.description,
                                    "placeholder": field.placeholder,
                                    "default_value": field.default_value,
                                    "options": field.options,
                                    "validation_rules": field.validation_rules,
                                    "metadata": field.metadata,
                                }
                                for field in section.fields
                            ],
                        }
                        for section in form_def.sections
                    ],
                    "submit_button_text": form_def.submit_button_text,
                    "multi_step": form_def.multi_step,
                    "allow_save_draft": form_def.allow_save_draft,
                },
            }

        except Exception as e:
            logger.error(f"Get profile creation form error: {e!s}")
            return {"success": False, "error": str(e)}

    def get_learning_style_form(self) -> dict[str, Any]:
        """
        Öğrenme stili formunu getir

        Returns:
            Form tanımı
        """
        try:
            form_def = form_interface.get_form_definition(FormType.LEARNING_STYLE)
            if not form_def:
                return {"success": False, "error": "Form tanımı bulunamadı"}

            return {
                "success": True,
                "form": {
                    "form_id": form_def.form_id,
                    "form_type": form_def.form_type.value,
                    "title": form_def.title,
                    "description": form_def.description,
                    "sections": [
                        {
                            "section_id": section.section_id,
                            "title": section.title,
                            "description": section.description,
                            "order": section.order,
                            "fields": [
                                {
                                    "field_id": field.field_id,
                                    "field_type": field.field_type.value,
                                    "label": field.label,
                                    "description": field.description,
                                    "options": field.options,
                                    "validation_rules": field.validation_rules,
                                }
                                for field in section.fields
                            ],
                        }
                        for section in form_def.sections
                    ],
                    "submit_button_text": form_def.submit_button_text,
                },
            }

        except Exception as e:
            logger.error(f"Get learning style form error: {e!s}")
            return {"success": False, "error": str(e)}

    def get_progress_report_form(self) -> dict[str, Any]:
        """
        İlerleme raporu formunu getir

        Returns:
            Form tanımı
        """
        try:
            form_def = form_interface.get_form_definition(FormType.PROGRESS_REPORT)
            if not form_def:
                return {"success": False, "error": "Form tanımı bulunamadı"}

            return {
                "success": True,
                "form": {
                    "form_id": form_def.form_id,
                    "form_type": form_def.form_type.value,
                    "title": form_def.title,
                    "description": form_def.description,
                    "sections": [
                        {
                            "section_id": section.section_id,
                            "title": section.title,
                            "description": section.description,
                            "order": section.order,
                            "fields": [
                                {
                                    "field_id": field.field_id,
                                    "field_type": field.field_type.value,
                                    "label": field.label,
                                    "description": field.description,
                                    "placeholder": field.placeholder,
                                    "default_value": field.default_value,
                                    "options": field.options,
                                    "validation_rules": field.validation_rules,
                                    "metadata": field.metadata,
                                }
                                for field in section.fields
                            ],
                        }
                        for section in form_def.sections
                    ],
                    "submit_button_text": form_def.submit_button_text,
                },
            }

        except Exception as e:
            logger.error(f"Get progress report form error: {e!s}")
            return {"success": False, "error": str(e)}

    async def submit_profile_form(
        self,
        form_data: dict[str, Any],
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Profil formunu gönder ve profil oluştur

        Args:
            form_data: Form verileri
            user_id: Kullanıcı ID
            session_id: Oturum ID

        Returns:
            İşlem sonucu
        """
        try:
            # Form gönderimini kaydet
            submission = form_interface.submit_form(
                form_id="profile_creation_v1",
                form_data=form_data,
                user_id=user_id,
                session_id=session_id,
            )

            if not submission.is_complete:
                return {
                    "success": False,
                    "submission_id": submission.submission_id,
                    "validation_errors": submission.validation_errors,
                    "message": "Form verilerinde hatalar var",
                }

            # Form verilerinden profil oluştur
            student_id = (
                user_id or session_id or f"student_{datetime.now().timestamp()}"
            )

            profile_data = {
                "name": form_data.get("name", "Öğrenci"),
                "grade": form_data.get("grade", "9"),
                "subjects": form_data.get("subjects", ["matematik"]),
                "goal": form_data.get("primary_goal", "Genel öğrenme"),
                "exam_target": form_data.get("exam_target", ""),
                "available_time": form_data.get("available_time_daily", 60),
                "study_time_preference": form_data.get(
                    "study_time_preference", "flexible"
                ),
                "difficulty_areas": form_data.get("difficulty_areas", []),
            }

            # Öğrenci profilini oluştur
            profile = await self.analyze_student(student_id, profile_data)

            return {
                "success": True,
                "submission_id": submission.submission_id,
                "student_id": student_id,
                "profile": {
                    "name": profile.name,
                    "grade": profile.grade,
                    "learning_style": profile.learning_style.value,
                    "knowledge_level": profile.knowledge_level.value,
                    "learning_goal": profile.learning_goal,
                    "available_time": profile.available_time,
                },
                "message": "Profil başarıyla oluşturuldu",
                "next_steps": [
                    {
                        "action": "learning_style_detection",
                        "title": "Öğrenme Stili Tespiti",
                    },
                    {
                        "action": "create_learning_path",
                        "title": "Öğrenme Yolu Oluşturma",
                    },
                ],
            }

        except Exception as e:
            logger.error(f"Submit profile form error: {e!s}")
            return {"success": False, "error": str(e)}

    async def submit_learning_style_form(
        self,
        form_data: dict[str, Any],
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Öğrenme stili formunu gönder ve analiz et

        Args:
            form_data: Form verileri
            user_id: Kullanıcı ID
            session_id: Oturum ID

        Returns:
            İşlem sonucu
        """
        try:
            # Form gönderimini kaydet
            submission = form_interface.submit_form(
                form_id="learning_style_v1",
                form_data=form_data,
                user_id=user_id,
                session_id=session_id,
            )

            if not submission.is_complete:
                return {
                    "success": False,
                    "submission_id": submission.submission_id,
                    "validation_errors": submission.validation_errors,
                    "message": "Form verilerinde hatalar var",
                }

            # Form verilerinden öğrenme stilini analiz et
            student_id = (
                user_id or session_id or f"student_{datetime.now().timestamp()}"
            )

            # Cevapları analiz et
            style_scores = {"visual": 0, "auditory": 0, "reading": 0, "kinesthetic": 0}

            # Her cevap için puan ver
            for field_id, answer in form_data.items():
                if answer in style_scores:
                    style_scores[answer] += 1

            # En yüksek puanlı stili belirle
            dominant_style = max(style_scores, key=style_scores.get)

            # Öğrenci profilini güncelle
            if student_id in self.profiles:
                profile = self.profiles[student_id]
                profile.learning_style = LearningStyle(dominant_style)
                profile.metadata["learning_style_analysis"] = {
                    "form_based": True,
                    "style_scores": style_scores,
                    "detected_style": dominant_style,
                    "confidence": style_scores[dominant_style]
                    / sum(style_scores.values())
                    if sum(style_scores.values()) > 0
                    else 0,
                }

            return {
                "success": True,
                "submission_id": submission.submission_id,
                "student_id": student_id,
                "learning_style_analysis": {
                    "dominant_style": dominant_style,
                    "style_scores": style_scores,
                    "confidence": style_scores[dominant_style]
                    / sum(style_scores.values())
                    if sum(style_scores.values()) > 0
                    else 0,
                    "content_preferences": form_data.get("content_preference", []),
                },
                "message": f"Öğrenme stilin '{dominant_style}' olarak belirlendi",
                "recommendations": self._get_style_recommendations(dominant_style),
                "next_steps": [
                    {
                        "action": "create_learning_path",
                        "title": "Öğrenme Yolu Oluşturma",
                    },
                    {"action": "get_resources", "title": "Kaynak Önerileri"},
                ],
            }

        except Exception as e:
            logger.error(f"Submit learning style form error: {e!s}")
            return {"success": False, "error": str(e)}

    def submit_progress_report_form(
        self,
        form_data: dict[str, Any],
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        İlerleme raporu formunu gönder

        Args:
            form_data: Form verileri
            user_id: Kullanıcı ID
            session_id: Oturum ID

        Returns:
            İşlem sonucu
        """
        try:
            # Form gönderimini kaydet
            submission = form_interface.submit_form(
                form_id="progress_report_v1",
                form_data=form_data,
                user_id=user_id,
                session_id=session_id,
            )

            if not submission.is_complete:
                return {
                    "success": False,
                    "submission_id": submission.submission_id,
                    "validation_errors": submission.validation_errors,
                    "message": "Form verilerinde hatalar var",
                }

            # İlerleme verilerini analiz et
            student_id = user_id or session_id

            progress_analysis = {
                "overall_satisfaction": form_data.get("overall_satisfaction", 5),
                "difficulty_level": form_data.get("difficulty_level", "just_right"),
                "time_spent_daily": form_data.get("time_spent_daily", 0),
                "completed_resources": form_data.get("completed_resources", 0),
                "helpful_resources": form_data.get("helpful_resources", []),
                "struggling_topics": form_data.get("struggling_topics", ""),
                "suggestions": form_data.get("suggestions", ""),
            }

            # Öneriler oluştur
            recommendations = self._generate_progress_recommendations(progress_analysis)

            # Davranışsal veri kaydet (eğer öğrenci profili varsa)
            if student_id and student_id in self.profiles:
                self.record_learning_behavior(
                    student_id=student_id,
                    content_type="progress_report",
                    interaction_data={
                        "satisfaction_score": progress_analysis["overall_satisfaction"]
                        / 10,
                        "completion_rate": min(
                            progress_analysis["completed_resources"] / 10, 1.0
                        ),
                        "time_spent_seconds": progress_analysis["time_spent_daily"]
                        * 60,
                        "engagement_score": progress_analysis["overall_satisfaction"]
                        / 10,
                    },
                )

            return {
                "success": True,
                "submission_id": submission.submission_id,
                "student_id": student_id,
                "progress_analysis": progress_analysis,
                "recommendations": recommendations,
                "message": "İlerleme raporu başarıyla kaydedildi",
                "next_steps": [
                    {
                        "action": "adjust_learning_path",
                        "title": "Öğrenme Yolunu Güncelle",
                    },
                    {"action": "get_new_resources", "title": "Yeni Kaynak Önerileri"},
                ],
            }

        except Exception as e:
            logger.error(f"Submit progress report form error: {e!s}")
            return {"success": False, "error": str(e)}

    def get_user_form_submissions(
        self, user_id: str, form_type: str | None = None
    ) -> dict[str, Any]:
        """
        Kullanıcının form gönderimlerini getir

        Args:
            user_id: Kullanıcı ID
            form_type: Form türü filtresi

        Returns:
            Form gönderimleri
        """
        try:
            form_type_enum = None
            if form_type:
                try:
                    form_type_enum = FormType(form_type)
                except ValueError:
                    return {"success": False, "error": "Geçersiz form türü"}

            submissions = form_interface.get_user_submissions(user_id, form_type_enum)

            submission_list = []
            for submission in submissions:
                submission_list.append(
                    {
                        "submission_id": submission.submission_id,
                        "form_id": submission.form_id,
                        "form_data": submission.form_data,
                        "is_complete": submission.is_complete,
                        "is_draft": submission.is_draft,
                        "submitted_at": submission.submitted_at.isoformat(),
                        "validation_errors": submission.validation_errors,
                    }
                )

            return {
                "success": True,
                "submissions": submission_list,
                "total_count": len(submission_list),
            }

        except Exception as e:
            logger.error(f"Get user form submissions error: {e!s}")
            return {"success": False, "error": str(e)}

    def _get_style_recommendations(self, style: str) -> list[str]:
        """Öğrenme stiline göre öneriler"""
        recommendations = {
            "visual": [
                "Video dersler ve animasyonlar izle",
                "Renkli notlar al ve diyagramlar çiz",
                "İnfografikler ve görsel materyaller kullan",
                "Zihin haritaları oluştur",
            ],
            "auditory": [
                "Podcast'ler ve sesli kitaplar dinle",
                "Ders notlarını sesli oku",
                "Grup tartışmalarına katıl",
                "Müzik eşliğinde çalış",
            ],
            "reading": [
                "Detaylı notlar al ve düzenli oku",
                "Kitaplar ve makaleler oku",
                "Yazarak öğren",
                "Özet çıkar ve tekrar et",
            ],
            "kinesthetic": [
                "Uygulamalı projeler yap",
                "Hareket ederek öğren",
                "Simülasyonlar ve deneyler kullan",
                "Kısa aralıklarla çalış",
            ],
        }

        return recommendations.get(style, ["Karma öğrenme yöntemleri kullan"])

    def _generate_progress_recommendations(
        self, progress_data: dict[str, Any]
    ) -> list[str]:
        """İlerleme verilerine göre öneriler oluştur"""
        recommendations = []

        satisfaction = progress_data.get("overall_satisfaction", 5)
        difficulty = progress_data.get("difficulty_level", "just_right")
        time_spent = progress_data.get("time_spent_daily", 0)

        # Memnuniyet bazlı öneriler
        if satisfaction < 4:
            recommendations.append("Öğrenme yöntemini değiştirmeyi dene")
            recommendations.append("Daha eğlenceli içerikler ara")
        elif satisfaction > 8:
            recommendations.append("Harika gidiyorsun! Bu tempoda devam et")

        # Zorluk bazlı öneriler
        if difficulty == "too_easy":
            recommendations.append("Daha zor içeriklere geç")
            recommendations.append("İleri seviye konulara odaklan")
        elif difficulty == "too_hard":
            recommendations.append("Daha temel konulardan başla")
            recommendations.append("Adım adım ilerle")

        # Zaman bazlı öneriler
        if time_spent < 30:
            recommendations.append("Günlük çalışma süresini artırmayı dene")
        elif time_spent > 180:
            recommendations.append("Çok uzun çalışma molalar vermeyi unutma")

        return (
            recommendations if recommendations else ["Mevcut çalışma düzenini sürdür"]
        )

    def _estimate_oer_time(self, oer_resource: OERResource) -> int:
        """
        OER kaynağı için tahmini süre hesapla

        Args:
            oer_resource: OER kaynağı

        Returns:
            Tahmini süre (dakika)
        """
        content_type = oer_resource.content_type.lower()

        # İçerik türüne göre tahmini süreler
        time_estimates = {
            "video": 20,
            "course": 120,  # 2 saat
            "lesson": 45,
            "article": 15,
            "document": 30,
            "interactive": 25,
            "simulation": 30,
            "activity": 20,
            "image": 5,
            "audio": 15,
            "quiz": 10,
            "assessment": 30,
        }

        base_time = time_estimates.get(content_type, 20)

        # Eğitim seviyesine göre ayarlama
        level_multipliers = {"K-12": 0.8, "undergraduate": 1.0, "graduate": 1.3}

        multiplier = level_multipliers.get(oer_resource.educational_level, 1.0)
        estimated_time = int(base_time * multiplier)

        return max(estimated_time, 5)  # En az 5 dakika

    # Structured Learning Path Methods

    async def create_structured_learning_path(
        self,
        student_id: str,
        learning_goal: str,
        subject: str,
        duration_weeks: int = 8,
        difficulty_preference: float = 0.5,
    ) -> dict[str, Any]:
        """
        Yapılandırılmış öğrenme yolu oluştur

        Args:
            student_id: Öğrenci ID
            learning_goal: Öğrenme hedefi
            subject: Konu alanı
            duration_weeks: Süre (hafta)
            difficulty_preference: Zorluk tercihi

        Returns:
            Yapılandırılmış öğrenme yolu
        """
        try:
            # Öğrenci profilini al
            profile = self.profiles.get(student_id)
            learning_style = profile.learning_style.value if profile else "mixed"

            # Yapılandırılmış yol oluştur
            structured_path = await structured_path_generator.generate_structured_path(
                student_id=student_id,
                learning_goal=learning_goal,
                subject=subject,
                duration_weeks=duration_weeks,
                difficulty_preference=difficulty_preference,
                learning_style=learning_style,
            )

            # Sonucu dict formatına çevir
            return {
                "success": True,
                "structured_path": {
                    "path_id": structured_path.path_id,
                    "title": structured_path.title,
                    "description": structured_path.description,
                    "student_id": structured_path.student_id,
                    "learning_goal": structured_path.learning_goal,
                    "phases": [
                        {
                            "phase_id": phase.phase_id,
                            "title": phase.title,
                            "description": phase.description,
                            "estimated_duration_days": phase.estimated_duration_days,
                            "objectives": [
                                {
                                    "objective_id": obj.objective_id,
                                    "title": obj.title,
                                    "description": obj.description,
                                    "type": obj.objective_type.value,
                                    "bloom_level": obj.bloom_level,
                                    "estimated_time_minutes": obj.estimated_time_minutes,
                                    "difficulty_level": obj.difficulty_level,
                                    "measurable_outcomes": obj.measurable_outcomes,
                                    "prerequisites": obj.prerequisites,
                                }
                                for obj in phase.objectives
                            ],
                            "milestones": [
                                {
                                    "milestone_id": milestone.milestone_id,
                                    "title": milestone.title,
                                    "description": milestone.description,
                                    "type": milestone.milestone_type.value,
                                    "estimated_time_minutes": milestone.estimated_time_minutes,
                                    "required_score": milestone.required_score,
                                    "completion_criteria": milestone.completion_criteria,
                                    "rewards": milestone.rewards,
                                }
                                for milestone in phase.milestones
                            ],
                            "learning_activities": phase.learning_activities,
                            "assessment_methods": phase.assessment_methods,
                            "difficulty_progression": phase.difficulty_progression,
                        }
                        for phase in structured_path.phases
                    ],
                    "total_objectives": structured_path.total_objectives,
                    "total_milestones": structured_path.total_milestones,
                    "estimated_total_time_hours": structured_path.estimated_total_time_hours,
                    "difficulty_curve": structured_path.difficulty_curve,
                    "current_phase": structured_path.current_phase,
                    "adaptive_parameters": structured_path.adaptive_parameters,
                    "created_at": structured_path.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Create structured learning path error: {e!s}")
            return {"success": False, "error": str(e)}

    def create_milestone_checkpoints(self, path_id: str) -> dict[str, Any]:
        """
        Kilometre taşı kontrol noktaları oluştur

        Args:
            path_id: Öğrenme yolu ID

        Returns:
            Kontrol noktaları
        """
        try:
            # Bu basit implementasyonda structured path'i cache'den alamıyoruz
            # Gerçek uygulamada database'den alınacak

            # Örnek checkpoints oluştur
            checkpoints = [
                {
                    "checkpoint_id": f"checkpoint_1_{path_id}",
                    "title": "Temel Kavramlar Kontrolü",
                    "description": "İlk aşama temel kavramlarının değerlendirilmesi",
                    "position": 1,
                    "requirements": {
                        "objectives_completed": ["obj_1", "obj_2"],
                        "minimum_score": 0.7,
                        "time_limit_minutes": 30,
                    },
                    "rewards": ["Seviye 1 tamamlandı", "Yeni içerikler açıldı"],
                    "assessment_type": "knowledge_check",
                },
                {
                    "checkpoint_id": f"checkpoint_2_{path_id}",
                    "title": "Uygulama Becerileri Kontrolü",
                    "description": "Öğrenilen kavramların uygulanması",
                    "position": 2,
                    "requirements": {
                        "objectives_completed": ["obj_3", "obj_4"],
                        "minimum_score": 0.75,
                        "time_limit_minutes": 45,
                    },
                    "rewards": ["Seviye 2 tamamlandı", "Proje aşaması açıldı"],
                    "assessment_type": "skill_assessment",
                },
            ]

            return {
                "success": True,
                "path_id": path_id,
                "checkpoints": checkpoints,
                "total_checkpoints": len(checkpoints),
            }

        except Exception as e:
            logger.error(f"Create milestone checkpoints error: {e!s}")
            return {"success": False, "error": str(e)}

    def generate_time_based_schedule(
        self,
        student_id: str,
        path_id: str,
        start_date: str,
        daily_study_minutes: int = 60,
        study_days_per_week: int = 5,
    ) -> dict[str, Any]:
        """
        Zaman tabanlı çalışma programı oluştur

        Args:
            student_id: Öğrenci ID
            path_id: Öğrenme yolu ID
            start_date: Başlangıç tarihi (ISO format)
            daily_study_minutes: Günlük çalışma süresi
            study_days_per_week: Haftalık çalışma günü

        Returns:
            Çalışma programı
        """
        try:
            from datetime import datetime

            start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            # Basit program oluştur (gerçek uygulamada structured path'den alınacak)
            schedule_items = []
            current_date = start_datetime

            # Örnek program öğeleri
            sample_objectives = [
                {"title": "Temel Kavramlar", "duration": 45, "type": "objective"},
                {
                    "title": "Uygulama Alıştırmaları",
                    "duration": 60,
                    "type": "objective",
                },
                {"title": "Problem Çözme", "duration": 75, "type": "objective"},
                {"title": "İlk Değerlendirme", "duration": 30, "type": "milestone"},
                {"title": "İleri Konular", "duration": 90, "type": "objective"},
                {"title": "Proje Çalışması", "duration": 120, "type": "objective"},
                {"title": "Final Değerlendirmesi", "duration": 45, "type": "milestone"},
            ]

            for i, item in enumerate(sample_objectives):
                # Hafta sonu kontrolü
                while current_date.weekday() >= study_days_per_week:
                    current_date += timedelta(days=1)

                schedule_item = {
                    "item_id": f"schedule_item_{i}",
                    "title": item["title"],
                    "type": item["type"],
                    "scheduled_date": current_date.isoformat(),
                    "estimated_duration_minutes": item["duration"],
                    "priority": 5 if item["type"] == "milestone" else 3,
                    "flexible": item["type"] != "milestone",
                    "status": "scheduled",
                }
                schedule_items.append(schedule_item)

                # Sonraki çalışma gününe geç
                current_date += timedelta(days=1)

            return {
                "success": True,
                "student_id": student_id,
                "path_id": path_id,
                "schedule": {
                    "start_date": start_date,
                    "daily_study_minutes": daily_study_minutes,
                    "study_days_per_week": study_days_per_week,
                    "total_items": len(schedule_items),
                    "estimated_completion_date": current_date.isoformat(),
                    "items": schedule_items,
                },
            }

        except Exception as e:
            logger.error(f"Generate time-based schedule error: {e!s}")
            return {"success": False, "error": str(e)}

    def track_learning_objectives(
        self,
        student_id: str,
        path_id: str,
        completed_objectives: list[str],
        objective_scores: dict[str, float],
    ) -> dict[str, Any]:
        """
        Öğrenme hedeflerini takip et

        Args:
            student_id: Öğrenci ID
            path_id: Öğrenme yolu ID
            completed_objectives: Tamamlanan hedefler
            objective_scores: Hedef skorları

        Returns:
            Takip verisi
        """
        try:
            # Basit takip verisi oluştur
            total_objectives = 10  # Örnek toplam hedef sayısı
            completed_count = len(completed_objectives)
            completion_percentage = (
                (completed_count / total_objectives) * 100
                if total_objectives > 0
                else 0
            )

            average_score = (
                sum(objective_scores.values()) / len(objective_scores)
                if objective_scores
                else 0
            )

            # Performans analizi
            performance_analysis = {
                "average_score": average_score,
                "completion_rate": completion_percentage,
                "strong_areas": [
                    obj_id for obj_id, score in objective_scores.items() if score > 0.8
                ],
                "improvement_areas": [
                    obj_id for obj_id, score in objective_scores.items() if score < 0.6
                ],
                "consistency": self._calculate_score_consistency(
                    list(objective_scores.values())
                ),
                "trend": "improving" if len(objective_scores) > 1 else "stable",
            }

            # Sonraki öneriler
            next_recommendations = []
            if completion_percentage < 100:
                next_recommendations.extend(
                    [
                        "Sonraki hedeflere odaklanın",
                        "Düşük skorlu konuları tekrar edin",
                        "Düzenli çalışma programınızı sürdürün",
                    ]
                )

            if average_score < 0.7:
                next_recommendations.append("Temel konuları pekiştirin")
            elif average_score > 0.9:
                next_recommendations.append("İleri seviye konulara geçebilirsiniz")

            return {
                "success": True,
                "student_id": student_id,
                "path_id": path_id,
                "tracking_data": {
                    "total_objectives": total_objectives,
                    "completed_count": completed_count,
                    "completion_percentage": completion_percentage,
                    "average_score": average_score,
                    "performance_analysis": performance_analysis,
                    "next_recommendations": next_recommendations,
                    "last_updated": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Track learning objectives error: {e!s}")
            return {"success": False, "error": str(e)}

    def _calculate_score_consistency(self, scores: list[float]) -> float:
        """Skor tutarlılığını hesapla"""
        if len(scores) < 2:
            return 1.0

        # Standart sapma ile tutarlılık ölç
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance**0.5

        # Tutarlılık skoru (düşük sapma = yüksek tutarlılık)
        consistency = max(0.0, 1.0 - std_dev)
        return consistency

    def optimize_learning_sequence(
        self, student_id: str, path_id: str, performance_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Öğrenme sırasını optimize et

        Args:
            student_id: Öğrenci ID
            path_id: Öğrenme yolu ID
            performance_data: Performans verisi

        Returns:
            Optimizasyon sonucu
        """
        try:
            avg_performance = performance_data.get("average_score", 0.5)
            completion_rate = performance_data.get("completion_rate", 0.0)

            optimizations = []

            # Performans bazlı optimizasyonlar
            if avg_performance < 0.6:
                optimizations.extend(
                    [
                        "Zorluk seviyesi düşürüldü",
                        "Ek destekleyici materyaller eklendi",
                        "Daha fazla tekrar aktivitesi planlandı",
                    ]
                )
            elif avg_performance > 0.85:
                optimizations.extend(
                    [
                        "Zorlayıcı içerikler eklendi",
                        "İleri seviye hedefler dahil edildi",
                        "Hızlandırılmış program önerildi",
                    ]
                )

            # Tamamlama oranı bazlı optimizasyonlar
            if completion_rate < 30:
                optimizations.extend(
                    [
                        "Motivasyon artırıcı aktiviteler eklendi",
                        "Daha kısa hedefler tanımlandı",
                        "Ödül sistemi güçlendirildi",
                    ]
                )

            # Öğrenme stili bazlı optimizasyonlar
            profile = self.profiles.get(student_id)
            if profile:
                style = profile.learning_style.value
                if style == "visual":
                    optimizations.append("Görsel materyaller önceliklendirildi")
                elif style == "auditory":
                    optimizations.append("Sesli içerikler artırıldı")
                elif style == "kinesthetic":
                    optimizations.append("Uygulamalı aktiviteler çoğaltıldı")

            return {
                "success": True,
                "student_id": student_id,
                "path_id": path_id,
                "optimization_result": {
                    "optimizations_applied": optimizations,
                    "performance_trigger": avg_performance,
                    "completion_trigger": completion_rate,
                    "optimization_date": datetime.now().isoformat(),
                    "next_review_date": (
                        datetime.now() + timedelta(weeks=2)
                    ).isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Optimize learning sequence error: {e!s}")
            return {"success": False, "error": str(e)}


# Singleton instance
learning_path_agent = LearningPathAgent()
