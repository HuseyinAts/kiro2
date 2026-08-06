import logging
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.cqrs.base import Command, CommandHandler
from models.learning_path_models import (
    LearningPath,
    LearningPathStudentProfile,
    Quiz,
    QuizQuestion,
    TopicCompletion,
    TopicProgress,
)
from models.learning_path_models import QuizSubmission as QuizSubmissionModel
from models.question_bank import QuestionBankItem as Question

logger = logging.getLogger(__name__)


# --- Existing CreateStudentProfile ---
class CreateStudentProfileCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    name: str
    grade: int
    subjects: list[str]
    goals: list[str]
    learning_style: str | None = None
    available_time: int | None = None
    db: Any  # AsyncSession


class CreateStudentProfileCommandHandler(
    CommandHandler[CreateStudentProfileCommand, dict[str, Any]]
):
    async def handle(self, command: CreateStudentProfileCommand) -> dict[str, Any]:
        db: AsyncSession = command.db

        try:
            existing = await db.execute(
                select(LearningPathStudentProfile).where(
                    LearningPathStudentProfile.user_id == command.user_id
                )
            )
            existing_profile = existing.scalars().first()
            if existing_profile:
                logger.info(
                    f"Returning existing profile for user {command.user_id}: {existing_profile.student_id}"
                )
                return {
                    "success": True,
                    "student_id": existing_profile.student_id,
                    "profile": {
                        "name": existing_profile.name,
                        "grade": int(existing_profile.grade)
                        if existing_profile.grade
                        else None,
                        "subjects": existing_profile.interests,
                        "goals": existing_profile.goals,
                        "learning_style": existing_profile.learning_style,
                        "available_time": existing_profile.available_time,
                        "exam_target": existing_profile.exam_target,
                        "created_at": existing_profile.created_at.isoformat()
                        if existing_profile.created_at
                        else None,
                    },
                    "message": "Mevcut profil döndürüldü",
                }

            logger.info(
                f"Creating student profile: {command.name}, grade {command.grade}"
            )

            student_id = f"STU_{uuid.uuid4().hex[:12]}"
            exam_target = "LGS" if command.grade <= 8 else "YKS"

            new_profile = LearningPathStudentProfile(
                student_id=student_id,
                user_id=command.user_id,
                name=command.name,
                grade=str(command.grade),
                exam_target=exam_target,
                learning_style=command.learning_style or "mixed",
                knowledge_level="beginner",
                interests=command.subjects,
                goals=command.goals,
                available_time=command.available_time or 60,
                metadata_json={"created_via": "learning_path_api_v2_cqrs"},
            )

            db.add(new_profile)
            await db.commit()
            await db.refresh(new_profile)

            logger.info(f"Student profile created successfully: {student_id}")
            return {
                "success": True,
                "student_id": student_id,
                "profile": {
                    "name": new_profile.name,
                    "grade": int(new_profile.grade),
                    "subjects": new_profile.interests,
                    "goals": new_profile.goals,
                    "learning_style": new_profile.learning_style,
                    "available_time": new_profile.available_time,
                    "exam_target": new_profile.exam_target,
                    "created_at": new_profile.created_at.isoformat(),
                },
                "message": "Öğrenci profili başarıyla oluşturuldu",
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating student profile: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Assess Knowledge ---
class AssessKnowledgeCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    subject: str
    questions: list[str] | None = None
    db: Any


class AssessKnowledgeCommandHandler(
    CommandHandler[AssessKnowledgeCommand, dict[str, Any]]
):
    async def handle(self, command: AssessKnowledgeCommand) -> dict[str, Any]:
        db: AsyncSession = command.db

        try:
            logger.info(
                f"Assessing knowledge for student {command.student_id}, subject: {command.subject}"
            )

            result = await db.execute(
                select(LearningPathStudentProfile).filter(
                    LearningPathStudentProfile.student_id == command.student_id
                )
            )
            profile = result.scalars().first()

            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Student profile not found: {command.student_id}",
                )

            result = await db.execute(
                select(QuizSubmissionModel).filter(
                    QuizSubmissionModel.student_id == command.student_id,
                    QuizSubmissionModel.quiz_id.startswith(command.subject),
                )
            )
            quiz_results = result.scalars().all()

            if quiz_results and len(quiz_results) > 0:
                avg_score = sum(q.score for q in quiz_results) / len(quiz_results)

                if avg_score >= 85:
                    knowledge_level = "expert"
                elif avg_score >= 70:
                    knowledge_level = "advanced"
                elif avg_score >= 55:
                    knowledge_level = "intermediate"
                elif avg_score >= 40:
                    knowledge_level = "elementary"
                else:
                    knowledge_level = "beginner"

                strengths = []
                weaknesses = []
                recommendations = []

                if avg_score >= 70:
                    strengths.append("Konuyu iyi kavramışsınız")
                    strengths.append("Temel kavramlar güçlü")
                    recommendations.append("İleri seviye problemlere odaklanın")
                elif avg_score >= 55:
                    strengths.append("Temel kavramları anlayabiliyorsunuz")
                    weaknesses.append("İleri seviye konularda zorluk yaşıyorsunuz")
                    recommendations.append("Daha fazla pratik yapın")
                    recommendations.append("Zayıf konuları tekrar edin")
                else:
                    weaknesses.append("Temel kavramlarda eksiklikler var")
                    weaknesses.append("Daha fazla çalışma gerekiyor")
                    recommendations.append("Temel konulardan başlayın")
                    recommendations.append("Düzenli tekrar yapın")

                score = int(avg_score)
            else:
                knowledge_level = profile.knowledge_level
                score = 50
                strengths = ["Henüz yeterli veri yok"]
                weaknesses = ["Daha fazla değerlendirme gerekiyor"]
                recommendations = [
                    "Quiz'lere katılarak bilgi seviyenizi ölçün",
                    "Düzenli pratik yapın",
                ]

            profile.knowledge_level = knowledge_level
            profile.updated_at = datetime.now()
            await db.commit()

            logger.info(
                f"Knowledge assessed: {knowledge_level} (score: {score}) for student {command.student_id}"
            )

            return {
                "success": True,
                "assessment": {
                    "student_id": command.student_id,
                    "subject": command.subject,
                    "level": knowledge_level,
                    "score": score,
                    "quiz_count": len(quiz_results),
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "recommendations": recommendations,
                    "assessed_at": datetime.now().isoformat(),
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error assessing knowledge: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Create Learning Path ---
class CreateLearningPathCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    subject: str
    target_date: str | None = None
    difficulty_level: str | None = "medium"
    db: Any
    facade: Any


class CreateLearningPathCommandHandler(
    CommandHandler[CreateLearningPathCommand, dict[str, Any]]
):
    async def handle(self, command: CreateLearningPathCommand) -> dict[str, Any]:
        from core.circuit_breaker import (
            CircuitBreakerHalfOpenError,
            CircuitBreakerOpenError,
        )
        from core.learning_path_circuit_breakers import (
            ai_agent_fallback_handler,
            get_ai_agent_circuit_breaker,
        )
        from core.metrics_collector import get_metrics_collector

        try:
            from agents.learning_path.models import KnowledgeLevel

            def _map_difficulty_to_knowledge_level(difficulty: str) -> KnowledgeLevel:
                mapping = {
                    "easy": KnowledgeLevel.BEGINNER,
                    "kolay": KnowledgeLevel.BEGINNER,
                    "medium": KnowledgeLevel.INTERMEDIATE,
                    "orta": KnowledgeLevel.INTERMEDIATE,
                    "hard": KnowledgeLevel.ADVANCED,
                    "zor": KnowledgeLevel.ADVANCED,
                }
                return mapping.get(difficulty.lower(), KnowledgeLevel.INTERMEDIATE)
        except ImportError:

            def _map_difficulty_to_knowledge_level(difficulty: str) -> Any:
                return None

        metrics = get_metrics_collector()
        ai_agent_circuit_breaker = get_ai_agent_circuit_breaker()
        start_time = time.time()
        db: AsyncSession = command.db

        try:
            target_level = _map_difficulty_to_knowledge_level(
                command.difficulty_level or "medium"
            )

            try:
                result = await ai_agent_circuit_breaker.call(
                    command.facade.create_path_for_student,
                    student_id=command.student_id,
                    subject=command.subject,
                    topics=None,
                    target_level=target_level,
                )
            except (CircuitBreakerOpenError, CircuitBreakerHalfOpenError) as cb_error:
                logger.warning(f"Circuit breaker triggered: {cb_error.message}")
                return await ai_agent_fallback_handler(
                    cb_error, command.student_id, command.subject
                )

            modules = []
            for idx, node in enumerate(result.nodes, start=1):
                module = {
                    "module_id": f"MOD{idx}",
                    "title": node.topic,
                    "order": idx,
                    "estimated_duration": f"{node.estimated_time} dakika",
                    "prerequisite": f"MOD{idx - 1}" if idx > 1 else None,
                    "topics": [
                        {
                            "topic_id": node.node_id,
                            "name": node.topic,
                            "duration_minutes": node.estimated_time,
                            "resources": [
                                {
                                    "resource_id": r.id,
                                    "title": r.title,
                                    "url": r.url,
                                    "type": r.resource_type,
                                }
                                for r in node.resources
                            ],
                            "quiz": {
                                "quiz_id": f"QZ_{node.node_id}",
                                "question_count": 10,
                                "passing_score": 70,
                            },
                        }
                    ],
                }
                modules.append(module)

            path_id = (
                f"LP_{command.student_id[:8]}_{int(time.time())}_{uuid.uuid4().hex[:4]}"
            )

            learning_path = {
                "path_id": path_id,
                "student_id": command.student_id,
                "subject": command.subject,
                "difficulty_level": command.difficulty_level,
                "target_date": command.target_date,
                "modules": modules,
                "progress": {
                    "completed_modules": 0,
                    "total_modules": len(modules),
                    "completed_topics": 0,
                    "total_topics": len(modules),
                    "overall_progress": 0,
                },
                "total_time": result.total_duration_minutes,
                "created_at": datetime.now().isoformat(),
                "ai_generated": True,
            }

            db_path = LearningPath(
                path_id=path_id,
                student_id=command.student_id,
                subject=command.subject,
                difficulty_level=command.difficulty_level or "intermediate",
                target_date=datetime.fromisoformat(command.target_date)
                if command.target_date
                else None,
                modules=modules,
                ai_generated=True,
                total_modules=len(modules),
                completed_modules=0,
                total_topics=len(modules),
                completed_topics=0,
                overall_progress=0.0,
                total_time=result.total_duration_minutes or 0,
            )
            db.add(db_path)
            await db.commit()

            duration_seconds = time.time() - start_time
            metrics.record_learning_path_creation(
                subject=command.subject,
                duration_seconds=duration_seconds,
                success=True,
            )

            return {
                "success": True,
                "learning_path": learning_path,
                "message": "Öğrenme yolu başarıyla oluşturuldu",
            }
        except Exception as e:
            duration_seconds = time.time() - start_time
            metrics.record_learning_path_creation(
                subject=command.subject,
                duration_seconds=duration_seconds,
                success=False,
            )
            logger.error(f"Error creating learning path: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Search Resources ---
class SearchResourcesCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    subject: str
    topic: str | None = None
    difficulty: str | None = "orta"
    resource_type: str | None = None
    max_results: int | None = 10
    student_profile: dict[str, Any] | None = None
    facade: Any


class SearchResourcesCommandHandler(
    CommandHandler[SearchResourcesCommand, dict[str, Any]]
):
    async def handle(self, command: SearchResourcesCommand) -> dict[str, Any]:
        import unicodedata

        from core.metrics_collector import get_metrics_collector
        from core.youtube_channels import is_trusted_channel

        def _normalize_turkish(text: str) -> str:
            text = unicodedata.normalize("NFC", text)
            return text.replace("İ", "i").replace("I", "ı").lower().strip()

        def _compute_relevance(resource: Any, search: Any) -> float:
            score = 0.0
            subject = _normalize_turkish(search.subject)
            topic = _normalize_turkish(search.topic or "")
            title_lower = _normalize_turkish(resource.title)
            desc_lower = (
                _normalize_turkish(resource.description) if resource.description else ""
            )
            if subject and subject in title_lower:
                score += 0.2
            if topic and len(topic) > 2 and topic in title_lower:
                score += 0.3
            elif topic and any(w in title_lower for w in topic.split() if len(w) > 2):
                score += 0.15
            if topic and desc_lower and topic in desc_lower:
                score += 0.1
            if resource.language == "tr":
                score += 0.2
            metadata = getattr(resource, "metadata", None)
            if isinstance(metadata, dict):
                channel = metadata.get("channel", "")
                if channel and is_trusted_channel(channel):
                    score += 0.1
            return min(score, 1.0)

        def _compute_final_score(
            resource: Any, search: Any, learning_style: str | None = None
        ) -> float:
            relevance = _compute_relevance(resource, search)
            metadata = getattr(resource, "metadata", None) or {}
            if resource.rating and resource.rating > 0:
                quality = resource.rating / 5.0
            else:
                view_count = int(metadata.get("view_count", 0) or 0)
                like_count = int(metadata.get("like_count", 0) or 0)
                if view_count > 0 and like_count > 0:
                    like_ratio = min(like_count / view_count, 0.1) / 0.1
                    quality = 0.5 + like_ratio * 0.5
                elif view_count > 100_000:
                    quality = 0.7
                elif view_count > 10_000:
                    quality = 0.6
                else:
                    quality = 0.5
            view_count = int(metadata.get("view_count", 0) or 0)
            if view_count >= 1_000_000:
                popularity = 1.0
            elif view_count >= 100_000:
                popularity = 0.7
            elif view_count >= 10_000:
                popularity = 0.4
            elif view_count >= 1_000:
                popularity = 0.2
            else:
                popularity = 0.1
            turkish = 1.0 if resource.language == "tr" else 0.3
            score = (
                relevance * 0.35 + quality * 0.25 + popularity * 0.15 + turkish * 0.25
            )
            if learning_style and resource.resource_type:
                rt = resource.resource_type.lower()
                style_match = {
                    "visual": ["video", "infographic", "diagram"],
                    "auditory": ["video", "podcast", "audio", "lecture"],
                    "reading": ["article", "book", "text"],
                    "kinesthetic": ["quiz", "practice", "interactive", "exercise"],
                }
                preferred = style_match.get(learning_style, [])
                if any(p in rt for p in preferred):
                    score = min(score + 0.05, 1.0)
            if isinstance(metadata, dict):
                rank_pos = metadata.get("discovery_rank", 50)
                score += max(0.0, 0.05 - rank_pos * 0.005)
            return min(score, 1.0)

        metrics = get_metrics_collector()
        start_time = time.time()

        try:
            learning_style = None
            if command.student_profile:
                learning_style = command.student_profile.get("learning_style")

            resources = await command.facade.search_resources(
                query=f"{command.subject} {command.topic or ''}".strip(),
                subject=command.subject,
                difficulty=command.difficulty,
                limit=command.max_results or 10,
            )

            response_resources = []
            for resource in resources:
                metadata = resource.metadata or {}
                diff_val = (
                    resource.difficulty_level.value
                    if hasattr(resource.difficulty_level, "value")
                    else str(resource.difficulty_level)
                )
                response_resources.append(
                    {
                        "resource_id": resource.resource_id,
                        "video_id": resource.resource_id,
                        "type": resource.resource_type,
                        "title": resource.title,
                        "description": resource.description or "",
                        "url": resource.url,
                        "thumbnail": metadata.get("thumbnail", ""),
                        "duration_minutes": resource.estimated_time,
                        "duration": metadata.get(
                            "duration_iso", f"PT{resource.estimated_time}M"
                        ),
                        "difficulty": diff_val,
                        "platform": resource.source,
                        "channel": metadata.get("channel", resource.source),
                        "channel_id": metadata.get("channel_id", ""),
                        "view_count": int(metadata.get("view_count", 0)),
                        "upload_date": metadata.get("published_at", ""),
                        "subject": command.subject,
                        "exam_type": metadata.get("exam_type", "TYT"),
                        "quality_score": (resource.rating or 3.0) / 5.0,
                        "is_accessible": True,
                        "is_turkish": resource.language == "tr",
                        "definition": metadata.get("definition", "sd"),
                        "caption_available": metadata.get("caption_available", False),
                        "scores": {
                            "relevance_score": _compute_relevance(resource, command),
                            "quality_score": (resource.rating or 3.0) / 5.0,
                            "turkish_score": (
                                1.0 if resource.language == "tr" else 0.3
                            ),
                            "final_score": _compute_final_score(
                                resource, command, learning_style
                            ),
                        },
                    }
                )

            duration_seconds = time.time() - start_time
            metrics.record_resource_search(
                subject=command.subject,
                duration_seconds=duration_seconds,
                result_count=len(response_resources),
            )
            return {
                "success": True,
                "resources": response_resources,
                "total": len(response_resources),
                "filters": {
                    "subject": command.subject,
                    "topic": command.topic,
                    "difficulty": command.difficulty,
                    "resource_type": command.resource_type,
                    "max_results": command.max_results or 10,
                },
                "metadata": {
                    "engine": "LearningPathFacade",
                    "version": "2.0",
                    "features": [
                        "multi_strategy_search",
                        "youtube_integration",
                        "khan_integration",
                        "oer_integration",
                        "rag_semantic_search",
                    ],
                },
            }
        except Exception as engine_error:
            logger.error(f"Resource discovery error: {engine_error!s}", exc_info=True)
            duration_seconds = time.time() - start_time
            metrics.record_resource_search(
                subject=command.subject,
                duration_seconds=duration_seconds,
                result_count=0,
            )
            return {
                "success": False,
                "resources": [],
                "total": 0,
                "filters": {
                    "subject": command.subject,
                    "topic": command.topic,
                    "difficulty": command.difficulty,
                    "resource_type": command.resource_type,
                },
                "error": {
                    "message": "Kaynaklar şu anda alınamıyor. Lütfen daha sonra tekrar deneyin.",
                    "code": "DISCOVERY_ERROR",
                },
            }


# --- Adapt Learning Path ---
class AdaptLearningPathCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    path_id: str
    performance_data: dict[str, Any]
    facade: Any


class AdaptLearningPathCommandHandler(
    CommandHandler[AdaptLearningPathCommand, dict[str, Any]]
):
    async def handle(self, command: AdaptLearningPathCommand) -> dict[str, Any]:
        try:
            from agents.learning_path.services.path_adaptation import PerformanceMetrics

            performance_metrics = [
                PerformanceMetrics(
                    topic=command.performance_data.get("topic_id", ""),
                    quiz_score=command.performance_data.get("score"),
                    completion_time_minutes=command.performance_data.get("time_spent"),
                    attempts=command.performance_data.get("attempts", 1),
                )
            ]
            result = await command.facade.adapt_student_path(
                student_id=command.student_id,
                performance=performance_metrics,
            )
            return {
                "success": True,
                "adaptations": [
                    {
                        "type": a.adaptation_type.value,
                        "action": a.description,
                        "recommendation": a.reason,
                    }
                    for a in result.actions_taken
                ],
                "updated_path": {
                    "path_id": command.path_id,
                    "student_id": command.student_id,
                    "current_difficulty": result.new_difficulty or "maintained",
                    "next_steps": result.next_steps,
                    "adapted_at": datetime.now().isoformat(),
                },
                "message": (
                    f"{len(result.actions_taken)} uyarlama yapıldı"
                    if result.actions_taken
                    else "Yol değişikliği gerekmiyor"
                ),
            }
        except Exception as e:
            logger.error(f"Error adapting learning path: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Update Completion Status ---
class UpdateCompletionStatusCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    completions: dict[str, bool]
    db: Any


class UpdateCompletionStatusCommandHandler(
    CommandHandler[UpdateCompletionStatusCommand, dict[str, Any]]
):
    async def handle(self, command: UpdateCompletionStatusCommand) -> dict[str, Any]:
        from core.metrics_collector import get_metrics_collector

        db: AsyncSession = command.db
        metrics = get_metrics_collector()
        try:
            for node_id, completed in command.completions.items():
                result = await db.execute(
                    select(TopicCompletion).filter(
                        TopicCompletion.student_id == command.student_id,
                        TopicCompletion.node_id == node_id,
                    )
                )
                existing = result.scalars().first()

                if existing:
                    existing.completed = completed
                    existing.updated_at = datetime.now()
                else:
                    new_completion = TopicCompletion(
                        student_id=command.student_id,
                        node_id=node_id,
                        completed=completed,
                    )
                    db.add(new_completion)
            await db.commit()

            # Cache invalidation should happen here or outside?
            # Best handled here by doing nothing and letting caller deal with it, or import cache
            from api.learning_path_v2 import _get_cache

            cache = _get_cache()
            if cache._initialized:
                await cache.delete(f"completion:{command.student_id}")

            updated_count = len(command.completions)
            for _ in range(updated_count):
                metrics.record_topic_completion(success=True)

            return {
                "success": True,
                "student_id": command.student_id,
                "updated_count": updated_count,
                "completions": command.completions,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating completion status: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Submit Quiz ---
class QuizAnswerModel(BaseModel):
    question_id: str
    answer: str
    time_spent: int | None = None


class SubmitQuizCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    quiz_id: str
    student_id: str
    answers: list[QuizAnswerModel]
    db: Any


class SubmitQuizCommandHandler(CommandHandler[SubmitQuizCommand, dict[str, Any]]):
    async def handle(self, command: SubmitQuizCommand) -> dict[str, Any]:
        db: AsyncSession = command.db
        from core.metrics_collector import get_metrics_collector

        metrics = get_metrics_collector()

        try:
            result = await db.execute(select(Quiz).filter(Quiz.id == command.quiz_id))
            quiz = result.scalars().first()

            correct_answers: dict[str, str] = {}
            q_meta: dict[str, dict] = {}
            passing_score = 70.0

            if quiz:
                passing_score = quiz.passing_score
                quiz_questions_result = await db.execute(
                    select(QuizQuestion, Question)
                    .join(Question, QuizQuestion.question_id == Question.id)
                    .filter(
                        QuizQuestion.quiz_id == command.quiz_id,
                        Question.is_active == True,
                    )
                    .order_by(QuizQuestion.order_number)
                )
                for quiz_question, question in quiz_questions_result.all():
                    correct_answers[question.id] = question.correct_answer
                    q_meta[question.id] = {
                        "topic_id": question.primary_topic_id,
                        "subject": (question.subject_area or "matematik").lower(),
                        "irt_a": float(
                            getattr(question, "irt_discrimination", 1.0) or 1.0
                        ),
                        "irt_b": float(getattr(question, "irt_difficulty", 0.0) or 0.0),
                        "irt_c": float(getattr(question, "irt_guessing", 0.2) or 0.2),
                    }
            else:
                question_ids = [a.question_id for a in command.answers]
                if question_ids:
                    questions_result = await db.execute(
                        select(
                            Question.id,
                            Question.correct_answer,
                            Question.primary_topic_id,
                            Question.subject_area,
                            Question.irt_discrimination,
                            Question.irt_difficulty,
                            Question.irt_guessing,
                        ).filter(
                            Question.id.in_(question_ids), Question.is_active == True
                        )
                    )
                    for question in questions_result.fetchall():
                        correct_answers[question.id] = question.correct_answer
                        q_meta[question.id] = {
                            "topic_id": question.primary_topic_id,
                            "subject": (question.subject_area or "matematik").lower(),
                            "irt_a": float(question.irt_discrimination or 1.0),
                            "irt_b": float(question.irt_difficulty or 0.0),
                            "irt_c": float(question.irt_guessing or 0.2),
                        }

            correct_count = 0
            question_results = []
            for answer in command.answers:
                correct_answer = correct_answers.get(answer.question_id)
                is_correct = (
                    correct_answer is not None and answer.answer == correct_answer
                )
                if is_correct:
                    correct_count += 1
                question_results.append(
                    {
                        "question_id": answer.question_id,
                        "student_answer": answer.answer,
                        "correct_answer": correct_answer or "N/A",
                        "is_correct": is_correct,
                        "time_spent": answer.time_spent,
                    }
                )

            if correct_answers:
                quiz_question_count = len(correct_answers)
            else:
                quiz_question_count = len(command.answers)
            total_questions = max(quiz_question_count, len(command.answers), 1)
            score = (correct_count / total_questions) * 100
            passed = score >= passing_score
            total_time = sum(a.time_spent or 0 for a in command.answers)

            quiz_submission_record = QuizSubmissionModel(
                student_id=command.student_id,
                quiz_id=command.quiz_id,
                question_count=total_questions,
                passing_score=passing_score,
                score=score,
                correct_count=correct_count,
                passed=passed,
                answers=[
                    {
                        "question_id": r["question_id"],
                        "answer": r["student_answer"],
                        "correct": r["is_correct"],
                    }
                    for r in question_results
                ],
                total_time_seconds=total_time,
                submitted_at=datetime.now(),
            )
            db.add(quiz_submission_record)
            await db.commit()

            event_report: dict[str, Any] = {"bkt": None, "xp": None, "streak": None}
            mastery_sync_status = "ok"
            mastery_sync_error = None
            try:
                from services.learning_event_service import LearningEventService

                event_report = await LearningEventService.on_quiz_completed(
                    student_id=command.student_id,
                    question_results=question_results,
                    q_meta=q_meta,
                    score=score,
                    passed=passed,
                    db=db,
                )
                if event_report.get("bkt") != "ok":
                    mastery_sync_status = "pending"
                    mastery_sync_error = str(event_report.get("bkt"))
            except Exception as event_err:
                mastery_sync_status = "pending"
                mastery_sync_error = str(event_err)
                event_report = {
                    "bkt": f"error: {event_err}",
                    "xp": None,
                    "streak": None,
                }

            subject = "genel"
            quiz_id_lower = command.quiz_id.lower()
            for known_subject in [
                "matematik",
                "turkce",
                "fizik",
                "kimya",
                "biyoloji",
                "tarih",
                "cografya",
                "geometri",
                "edebiyat",
                "ingilizce",
            ]:
                if known_subject in quiz_id_lower:
                    subject = known_subject
                    break
            metrics.record_quiz_submission(subject=subject, score=score, passed=passed)

            return {
                "success": True,
                "quiz_id": command.quiz_id,
                "student_id": command.student_id,
                "score": round(score, 2),
                "correct_count": correct_count,
                "total_questions": total_questions,
                "passing_score": passing_score,
                "passed": passed,
                "total_time_seconds": total_time,
                "question_results": question_results,
                "timestamp": datetime.now().isoformat(),
                "feedback": (
                    "Tebrikler! Quiz'i başarıyla tamamladınız."
                    if passed
                    else f"Quiz'i geçemediniz. Geçme notu: {passing_score}%"
                ),
                "event_report": event_report,
                "mastery_sync_status": mastery_sync_status,
                "mastery_sync_error": mastery_sync_error,
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing quiz submission: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Update Progress ---
class UpdateProgressCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    node_id: str
    progress: int
    completed: bool
    time_spent: int | None
    db: Any


class UpdateProgressCommandHandler(
    CommandHandler[UpdateProgressCommand, dict[str, Any]]
):
    async def handle(self, command: UpdateProgressCommand) -> dict[str, Any]:
        db: AsyncSession = command.db
        try:
            result = await db.execute(
                select(TopicProgress).filter(
                    TopicProgress.student_id == command.student_id,
                    TopicProgress.node_id == command.node_id,
                )
            )
            existing = result.scalars().first()
            if existing:
                existing.progress = command.progress
                existing.completed = command.completed
                existing.time_spent = command.time_spent or 0
                existing.updated_at = datetime.now()
            else:
                new_record = TopicProgress(
                    student_id=command.student_id,
                    node_id=command.node_id,
                    progress=command.progress,
                    completed=command.completed,
                    time_spent=command.time_spent or 0,
                )
                db.add(new_record)

            result = await db.execute(
                select(TopicCompletion).filter(
                    TopicCompletion.student_id == command.student_id,
                    TopicCompletion.node_id == command.node_id,
                )
            )
            completion_existing = result.scalars().first()
            if completion_existing:
                completion_existing.completed = command.completed
                if command.completed:
                    completion_existing.completion_date = datetime.now()
                completion_existing.updated_at = datetime.now()
            elif command.completed:
                new_completion = TopicCompletion(
                    student_id=command.student_id,
                    node_id=command.node_id,
                    completed=True,
                    completion_date=datetime.now(),
                )
                db.add(new_completion)
            await db.commit()

            return {
                "success": True,
                "student_id": command.student_id,
                "node_id": command.node_id,
                "progress": command.progress,
                "completed": command.completed,
                "time_spent": command.time_spent,
                "timestamp": datetime.now().isoformat(),
                "message": (
                    "Topic ilerleme durumu kaydedildi (mastery pipeline etkilenmez)."
                    if command.completed
                    else f"İlerleme %{command.progress} olarak kaydedildi (mastery pipeline etkilenmez)."
                ),
                "is_mastery_signal": False,
                "mastery_source": "quiz_submissions",
                "progress_source": "update_progress_endpoint",
                "completion_source": "update_progress_endpoint",
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating progress: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Submit Review ---
class SubmitReviewCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    card_id: str
    grade: int
    student_id: str
    db: Any


class SubmitReviewCommandHandler(CommandHandler[SubmitReviewCommand, dict[str, Any]]):
    async def handle(self, command: SubmitReviewCommand) -> dict[str, Any]:
        db: AsyncSession = command.db
        try:
            from services.question_review_adapter import QuestionReviewAdapter

            adapter = QuestionReviewAdapter()
            card = await adapter.submit_review(
                command.card_id, command.grade, db, student_id=command.student_id
            )
            if not card:
                raise HTTPException(
                    status_code=404, detail="Kart bulunamadi veya gecersiz grade"
                )
            await db.commit()
            return {
                "success": True,
                "card_id": card.id,
                "next_due": card.due_date.isoformat() if card.due_date else None,
                "state": card.state,
                "stability": card.stability,
                "difficulty": card.difficulty,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting review: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# --- Register Wrong Answers ---
class RegisterWrongAnswersCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    question_ids: list[str]
    error_types: dict[str, str] | None = None
    is_timeout: bool = False
    db: Any


class RegisterWrongAnswersCommandHandler(
    CommandHandler[RegisterWrongAnswersCommand, dict[str, Any]]
):
    async def handle(self, command: RegisterWrongAnswersCommand) -> dict[str, Any]:
        db: AsyncSession = command.db
        try:
            from services.question_review_adapter import QuestionReviewAdapter

            adapter = QuestionReviewAdapter()
            created = await adapter.register_wrong_answers(
                command.student_id,
                command.question_ids,
                db,
                error_types=command.error_types,
            )
            await db.commit()
            return {
                "success": True,
                "created": created,
                "total_submitted": len(command.question_ids),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering wrong answers: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )
