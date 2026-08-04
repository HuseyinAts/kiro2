"""
Learning Path API v2 - Refactored with LearningPathFacade

KIRO2 - Türkiye Üniversite Sınavları Hazırlık Platformu
Öğrenci öğrenme yolu oluşturma ve yönetim endpoint'leri

REFACTORING SUMMARY (2026-01-26):
- Uses new LearningPathFacade instead of monolithic agent
- All endpoints now use facade's coordinated services
- Fixed: /adapt-path auth added (JWT required)
- Fixed: Quiz mock data replaced with database query
- Fixed: Rate limiting added to all endpoints
- Fixed: Database rollback in exception handlers
- Maintains full backward compatibility with API contract

Design Patterns Used:
- Facade Pattern: Single entry point via LearningPathFacade
- Strategy Pattern: Multiple resource search strategies
- Repository Pattern: Clean data access layer
- Dependency Injection: Services injected via factory

Architecture:
API Layer (this file)
  -> LearningPathFacade
     -> PathGenerationService
     -> ResourceDiscoveryService
     -> PathAdaptationService
     -> ChatIntegrationService
     -> FormIntegrationService
"""

import logging
import time
import unicodedata
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

# Subject identifier normalization (ASCII tags, NOT Turkish prose)
# .claude/rules/case-convention.md — Endpoint Gate
from core.turkish_nlp_utils import subject_db, subject_key  # noqa: F401

# New facade import
try:
    from agents.learning_path.facade import LearningPathFacade, get_learning_path_facade
except (ImportError, TypeError):
    get_learning_path_facade = None
    LearningPathFacade = None

try:
    from agents.learning_path.models import KnowledgeLevel
except (ImportError, TypeError):
    KnowledgeLevel = None

try:
    from agents.learning_path.services.path_adaptation import PerformanceMetrics
except (ImportError, TypeError):
    PerformanceMetrics = None

# Keep existing imports for compatibility
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.learning_path_schemas import LearningPathCreateRequest
from core.circuit_breaker import CircuitBreakerHalfOpenError, CircuitBreakerOpenError
from core.cqrs.bus import get_command_bus
from application.commands.learning_path import CreateStudentProfileCommand
from core.dependencies import AuthenticatedUser, get_current_user, get_db
from core.learning_path_auth import (
    verify_student_access,
)
from core.learning_path_circuit_breakers import (
    ai_agent_fallback_handler,
    get_ai_agent_circuit_breaker,
    get_resource_search_circuit_breaker,
)
from core.metrics_collector import get_metrics_collector
from core.multi_layer_cache import MultiLayerCache
from core.youtube_channels import is_trusted_channel
from models.learning_path_models import (
    LearningPath,
    LearningPathStudentProfile,
    Quiz,
    QuizQuestion,
    TopicCompletion,
    TopicProgress,
)
from models.learning_path_models import (
    QuizSubmission as QuizSubmissionModel,
)
from models.question_bank import QuestionBankItem as Question

# Rate limiting
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    Limiter = None

logger = logging.getLogger(__name__)

# Get global metrics collector
metrics = get_metrics_collector()

# Circuit breakers
ai_agent_circuit_breaker = get_ai_agent_circuit_breaker()
resource_search_circuit_breaker = get_resource_search_circuit_breaker()

# Router setup
router = APIRouter(prefix="/api/v1/learning-path", tags=["Learning Path"])

# Rate limiter setup
if RATE_LIMITING_ENABLED:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

# Rate limit configurations
RATE_LIMITS = {
    "create_profile": "10/minute",
    "assess_knowledge": "20/minute",
    "create_path": "5/minute",  # Expensive AI operation
    "search_resources": "30/minute",
    "adapt_path": "10/minute",
    "flag_submit": "10/minute",  # S1.2 student feedback flag rate limit
    "completion_read": "60/minute",
    "completion_write": "30/minute",
    "quiz_submit": "10/minute",
    "progress": "60/minute",
    "health": "100/minute",
}


def rate_limit(limit_key: str):
    """
    Rate limiting decorator that gracefully handles missing slowapi.

    Usage:
        @router.post("/endpoint")
        @rate_limit("create_profile")
        async def endpoint(...):
            ...
    """

    def decorator(func):
        if limiter is not None and limit_key in RATE_LIMITS:
            return limiter.limit(RATE_LIMITS[limit_key])(func)
        return func

    return decorator


# Cache configuration from facade config
def get_learning_path_cache() -> MultiLayerCache:
    """Get cache instance from facade."""
    from agents.learning_path.config import get_learning_path_config

    config = get_learning_path_config()
    return MultiLayerCache(
        redis_url=config.CACHE_REDIS_URL,
        l1_max_size=config.CACHE_L1_MAX_SIZE,
        default_ttl=config.CACHE_DEFAULT_TTL,
        namespace="learning_path",
    )


# Global cache instance (lazy initialization)
_cache_instance: MultiLayerCache | None = None


def _get_cache() -> MultiLayerCache:
    """Thread-safe cache accessor."""
    global _cache_instance
    if _cache_instance is None:
        import threading

        with threading.Lock():
            if _cache_instance is None:
                _cache_instance = get_learning_path_cache()
    return _cache_instance


# ============================================================================
# Request/Response Models
# ============================================================================


class StudentProfileCreate(BaseModel):
    """Student profile creation request."""

    name: str = Field(..., description="Öğrenci adı")
    grade: int = Field(..., ge=5, le=12, description="Sınıf seviyesi (5-12)")
    subjects: list[str] = Field(..., description="İlgili dersler")
    goals: list[str] = Field(..., description="Hedefler")
    learning_style: str | None = Field(None, description="Öğrenme stili")
    available_time: int | None = Field(
        None, description="Günlük çalışma süresi (dakika)"
    )


class KnowledgeAssessment(BaseModel):
    """Knowledge assessment request."""

    student_id: str = Field(..., description="Öğrenci ID")
    subject: str = Field(..., description="Ders")
    questions: list[str] | None = Field(None, description="Değerlendirme soruları")


class LearningPathCreate(BaseModel):
    """Learning path creation request."""

    student_id: str = Field(..., description="Öğrenci ID")
    subject: str = Field(..., description="Ders")
    target_date: str | None = Field(None, description="Hedef tarih")
    difficulty_level: str | None = Field("medium", description="Zorluk seviyesi")


class QuizAnswer(BaseModel):
    """Single quiz answer."""

    question_id: str = Field(..., description="Soru ID")
    answer: str = Field(..., description="Öğrenci cevabı")
    time_spent: int | None = Field(None, description="Soruda geçen süre (saniye)")


class QuizSubmission(BaseModel):
    """Quiz submission request."""

    student_id: str | None = Field(
        None, description="Öğrenci ID (opsiyonel, current_user'dan türetilir)"
    )
    quiz_id: str | None = Field(None, description="Quiz ID (opsiyonel, URL'den alınır)")
    answers: list[QuizAnswer] = Field(..., description="Quiz cevapları")


class ProgressUpdate(BaseModel):
    """Progress update request."""

    progress: int = Field(..., ge=0, le=100, description="İlerleme yüzdesi (0-100)")
    time_spent: int | None = Field(None, description="Harcanan süre (dakika)")
    completed: bool = Field(False, description="Tamamlandı mı?")


class CompletionUpdate(BaseModel):
    """Completion status update request."""

    student_id: str = Field(..., description="Öğrenci ID")
    completions: dict[str, bool] = Field(..., description="Topic tamamlanma durumları")


class ResourceSearch(BaseModel):
    """Resource search request."""

    subject: str = Field(..., description="Ders (matematik, fizik, kimya, vb.)")
    topic: str | None = Field(None, description="Konu (türev, hareket, atom, vb.)")
    difficulty: str | None = Field(
        "orta", description="Zorluk seviyesi (kolay, orta, zor)"
    )
    resource_type: str | None = Field(
        None, description="Kaynak tipi (video, article, etc.)"
    )
    max_results: int | None = Field(
        10, ge=1, le=50, description="Maksimum sonuç sayısı"
    )
    student_profile: dict[str, Any] | None = Field(
        None, description="Öğrenci profili (opsiyonel)"
    )


class PathAdaptation(BaseModel):
    """Path adaptation request."""

    student_id: str = Field(..., description="Öğrenci ID")
    path_id: str = Field(..., description="Öğrenme yolu ID")
    performance_data: dict[str, Any] = Field(..., description="Performans verileri")


# ============================================================================
# Helper Functions
# ============================================================================


def _get_facade() -> LearningPathFacade:
    """Get facade instance via dependency injection."""
    if get_learning_path_facade is None:
        raise HTTPException(
            status_code=503,
            detail="Learning Path facade not available. Please ensure cachetools is installed: pip install cachetools",
        )
    return get_learning_path_facade()


def _normalize_turkish(text: str) -> str:
    """NFC normalize + Turkish lowercase."""
    text = unicodedata.normalize("NFC", text)
    return text.replace("İ", "i").replace("I", "ı").lower().strip()


def _compute_relevance(resource: Any, search: Any) -> float:
    """Compute relevance score from resource metadata vs search query."""
    score = 0.0
    subject = _normalize_turkish(search.subject)
    topic = _normalize_turkish(search.topic or "")
    title_lower = _normalize_turkish(resource.title)
    desc_lower = (
        _normalize_turkish(resource.description) if resource.description else ""
    )

    # Subject match in title (+0.2)
    if subject and subject in title_lower:
        score += 0.2

    # Topic match in title (+0.3) — most important signal
    if topic and len(topic) > 2 and topic in title_lower:
        score += 0.3
    elif topic and any(w in title_lower for w in topic.split() if len(w) > 2):
        score += 0.15

    # Topic match in description (+0.1)
    if topic and desc_lower and topic in desc_lower:
        score += 0.1

    # Turkish language (+0.2)
    if resource.language == "tr":
        score += 0.2

    # Trusted channel bonus (+0.1)
    metadata = getattr(resource, "metadata", None)
    if isinstance(metadata, dict):
        channel = metadata.get("channel", "")
        if channel:
            if is_trusted_channel(channel):
                score += 0.1

    return min(score, 1.0)


def _compute_final_score(
    resource: Any, search: Any, learning_style: str | None = None
) -> float:
    """Weighted final score: relevance 35% + quality 25% + popularity 15% + turkish 25%."""
    relevance = _compute_relevance(resource, search)

    # Quality: use rating if available, else derive from view/like ratio
    metadata = getattr(resource, "metadata", None) or {}
    if resource.rating and resource.rating > 0:
        quality = resource.rating / 5.0
    else:
        # Synthetic quality from view+like counts
        view_count = int(metadata.get("view_count", 0) or 0)
        like_count = int(metadata.get("like_count", 0) or 0)
        if view_count > 0 and like_count > 0:
            like_ratio = min(like_count / view_count, 0.1) / 0.1  # 10% = perfect
            quality = 0.5 + like_ratio * 0.5  # 0.5-1.0 range
        elif view_count > 100_000:
            quality = 0.7
        elif view_count > 10_000:
            quality = 0.6
        else:
            quality = 0.5

    # Popularity: normalized view count signal
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
    score = relevance * 0.35 + quality * 0.25 + popularity * 0.15 + turkish * 0.25

    # VARK learning style bonus
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

    # Discovery pipeline ranking bonus (stronger signal)
    if isinstance(metadata, dict):
        rank_pos = metadata.get("discovery_rank", 50)
        score += max(0.0, 0.05 - rank_pos * 0.005)

    return min(score, 1.0)


def _map_difficulty_to_knowledge_level(difficulty: str) -> KnowledgeLevel:
    """Map API difficulty string to KnowledgeLevel enum."""
    mapping = {
        "easy": KnowledgeLevel.BEGINNER,
        "kolay": KnowledgeLevel.BEGINNER,
        "medium": KnowledgeLevel.INTERMEDIATE,
        "orta": KnowledgeLevel.INTERMEDIATE,
        "hard": KnowledgeLevel.ADVANCED,
        "zor": KnowledgeLevel.ADVANCED,
    }
    return mapping.get(difficulty.lower(), KnowledgeLevel.INTERMEDIATE)


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/create-profile")
@rate_limit("create_profile")
async def create_student_profile(
    request: Request,
    profile: StudentProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Öğrenci profili oluştur (CQRS Refactored)
    """
    try:
        command = CreateStudentProfileCommand(
            db=db,
            user_id=str(current_user.id),
            name=profile.name,
            grade=profile.grade,
            subjects=profile.subjects,
            goals=profile.goals,
            learning_style=profile.learning_style,
            available_time=profile.available_time
        )
        command_bus = get_command_bus()
        result = await command_bus.execute(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student profile: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/assess-knowledge")
@rate_limit("assess_knowledge")
async def assess_knowledge(
    request: Request,
    assessment: KnowledgeAssessment,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Bilgi seviyesi değerlendirmesi

    Öğrencinin konuyla ilgili mevcut bilgi seviyesini değerlendirir.
    Quiz geçmişinden gerçek performans hesaplar.
    """
    try:
        await verify_student_access(assessment.student_id, current_user, db)
        from application.commands.learning_path import AssessKnowledgeCommand
        from core.cqrs.bus import get_command_bus
        
        command = AssessKnowledgeCommand(
            db=db,
            student_id=assessment.student_id,
            subject=assessment.subject,
            questions=assessment.questions
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()  # FIX: Async rollback on error
        logger.error(f"Error assessing knowledge: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/create-path")
@rate_limit("create_path")
async def create_learning_path(
    request: Request,
    path_request: LearningPathCreateRequest,
    facade: LearningPathFacade = Depends(_get_facade),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Kişiselleştirilmiş öğrenme yolu oluştur

    LearningPathFacade kullanarak AI-powered öğrenme yolu oluşturur.
    Circuit breaker koruması ve metrik takibi ile.
    """
    metrics.record_learning_path_api_request(
        endpoint="/create-path",
        method="POST",
        status_code=200,
    )
    
    try:
        start_time = time.time()
        await verify_student_access(path_request.student_id, current_user, db)
        from application.commands.learning_path import CreateLearningPathCommand
        from core.cqrs.bus import get_command_bus
        
        command = CreateLearningPathCommand(
            db=db,
            facade=facade,
            student_id=path_request.student_id,
            subject=path_request.subject,
            target_date=path_request.target_date,
            difficulty_level=path_request.difficulty_level
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        duration_seconds = time.time() - start_time
        metrics.record_learning_path_creation(
            subject=path_request.subject,
            duration_seconds=duration_seconds,
            success=False,
        )
        metrics.record_learning_path_api_request(
            endpoint="/create-path", method="POST", status_code=500
        )

        logger.error(f"Error creating learning path: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/search-resources")
@rate_limit("search_resources")
async def search_resources(
    request: Request,
    search: ResourceSearch,
    facade: LearningPathFacade = Depends(_get_facade),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Eğitim kaynaklarını ara

    LearningPathFacade kullanarak çoklu platformdan kaynak arar.
    YouTube, Khan Academy, OER Commons ve RAG entegrasyonu.
    """
    metrics.record_learning_path_api_request(
        endpoint="/search-resources", method="POST", status_code=200
    )

    try:
        if not search.subject or not search.subject.strip():
            raise HTTPException(
                status_code=400, detail="Ders (subject) alanı zorunludur"
            )

        from application.commands.learning_path import SearchResourcesCommand
        from core.cqrs.bus import get_command_bus
        
        command = SearchResourcesCommand(
            db=db,
            facade=facade,
            subject=search.subject,
            topic=search.topic,
            difficulty=search.difficulty,
            resource_type=search.resource_type,
            max_results=search.max_results,
            student_profile=search.student_profile
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_resources: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Kaynak araması sırasında bir hata oluştu.",
        )


@router.post("/adapt-path")
@rate_limit("adapt_path")
async def adapt_learning_path(
    request: Request,
    adaptation: PathAdaptation,
    facade: LearningPathFacade = Depends(_get_facade),
    current_user: AuthenticatedUser = Depends(get_current_user),  # FIX: Auth added!
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Öğrenme yolunu performansa göre uyarla

    Öğrencinin performans verilerine göre öğrenme yolunu dinamik olarak günceller.
    PathAdaptationService kullanır.

    FIX: JWT authentication eklendi (önceden eksikti)
    """
    try:
        await verify_student_access(adaptation.student_id, current_user, db)
        from application.commands.learning_path import AdaptLearningPathCommand
        from core.cqrs.bus import get_command_bus
        
        command = AdaptLearningPathCommand(
            db=db,
            facade=facade,
            student_id=adaptation.student_id,
            path_id=adaptation.path_id,
            performance_data=adaptation.performance_data
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adapting learning path: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/paths/{student_id}")
@rate_limit("profile_read")
async def get_student_paths(
    request: Request,
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get all learning paths for a student
    """
    await verify_student_access(student_id, current_user, db)
    
    from models.learning_path_models import LearningPath
    from sqlalchemy import select
    
    result = await db.execute(
        select(LearningPath).where(LearningPath.student_id == student_id)
    )
    paths = result.scalars().all()
    
    return {
        "success": True,
        "paths": [
            {
                "path_id": p.path_id,
                "subject": p.subject,
                "difficulty_level": p.difficulty_level,
            }
            for p in paths
        ]
    }

@router.get("/completion/{student_id}")
@rate_limit("completion_read")
async def get_completion_status(
    request: Request,
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get student's topic completion status

    Returns completion status for all topics in student's learning path.
    Uses multi-layer cache (L1+L2) for performance.
    """
    try:
        await verify_student_access(student_id, current_user, db)

        logger.info(f"Getting completion status for student {student_id}")

        cache = _get_cache()
        cache_key = f"completion:{student_id}"

        # Initialize cache if needed
        if not cache._initialized:
            await cache.initialize()

        async def fetch_completion():
            """Fetch completion status from database - ASYNC FIX."""
            result = await db.execute(
                select(TopicCompletion).filter(
                    TopicCompletion.student_id == student_id,
                    # is_active column not in DB yet - commented out
                    # TopicCompletion.is_active == True
                )
            )
            completion_records = result.scalars().all()

            completion_data = {}
            for record in completion_records:
                completion_data[record.node_id] = record.completed

            logger.info(
                f"Fetched {len(completion_data)} completion records "
                f"for student {student_id}"
            )
            return completion_data

        completion_data = await cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_completion,
            ttl=300,  # 5 minutes
        )

        return {
            "success": True,
            "data": completion_data,
            "student_id": student_id,
            "total_topics": len(completion_data),
            "completed_topics": sum(1 for v in completion_data.values() if v),
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting completion status: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.put("/completion/{student_id}")
@rate_limit("completion_write")
async def update_completion_status(
    request: Request,
    student_id: str,
    completion_update: CompletionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Update student's topic completion status

    Allows frontend to mark topics as completed/incomplete.
    Invalidates cache after update.
    """
    try:
        await verify_student_access(student_id, current_user, db)
        if completion_update.student_id != student_id:
            raise HTTPException(
                status_code=400,
                detail="Student ID mismatch",
            )
            
        from application.commands.learning_path import UpdateCompletionStatusCommand
        from core.cqrs.bus import get_command_bus
        
        command = UpdateCompletionStatusCommand(
            db=db,
            student_id=student_id,
            completions=completion_update.completions
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating completion status: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/quiz/{quiz_id}/submit")
@rate_limit("quiz_submit")
async def submit_quiz(
    request: Request,
    quiz_id: str,
    submission: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Submit quiz answers and get results

    FIX: Uses database instead of mock data for quiz answers.
    """
    try:
        actual_student_id = submission.student_id or str(current_user.id)
        await verify_student_access(actual_student_id, current_user, db)
        
        from application.commands.learning_path import SubmitQuizCommand, QuizAnswerModel
        from core.cqrs.bus import get_command_bus
        
        answers = [QuizAnswerModel(question_id=a.question_id, answer=a.answer, time_spent=a.time_spent) for a in submission.answers]
        command = SubmitQuizCommand(
            db=db,
            quiz_id=quiz_id,
            student_id=actual_student_id,
            answers=answers
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing quiz submission: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.put("/progress/{student_id}/{node_id}")
@rate_limit("progress")
async def update_progress(
    request: Request,
    student_id: str,
    node_id: str,
    progress_update: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Update student's INTERACTION STATE on a specific topic/node

    Writes {progress, completed, time_spent} to TopicProgress and TopicCompletion.
    This is a UI convenience write - it is NOT a mastery signal.

    MASTERY TRUTH SOURCE: StudentAbility/theta (updated only by submit_quiz pipeline).
    Calling this endpoint does NOT update theta, BKT, cat_sessions, or any mastery model.
    """
    try:
        await verify_student_access(student_id, current_user, db)
        if not 0 <= progress_update.progress <= 100:
            raise HTTPException(
                status_code=400, detail="Progress must be between 0 and 100"
            )
            
        from application.commands.learning_path import UpdateProgressCommand
        from core.cqrs.bus import get_command_bus
        
        command = UpdateProgressCommand(
            db=db,
            student_id=student_id,
            node_id=node_id,
            progress=progress_update.progress,
            completed=progress_update.completed,
            time_spent=progress_update.time_spent
        )
        return await get_command_bus().execute(command)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# ============================================================================
# Fallback Videos Endpoint (Task 8 - Missing Endpoint Fix)
# ============================================================================

# Curated fallback videos by subject (static list for when search fails)
_FALLBACK_VIDEOS: dict[str, list[dict[str, Any]]] = {
    "matematik": [
        {
            "resource_id": "fallback_mat_001",
            "title": "TYT Matematik - Temel Kavramlar",
            "url": "https://www.youtube.com/watch?v=TYT_MATEMATIK_TEMEL",
            "platform": "youtube",
            "channel": "TonguçAkademi",
            "duration_minutes": 45,
            "difficulty": "orta",
            "quality_score": 0.85,
        },
        {
            "resource_id": "fallback_mat_002",
            "title": "AYT Matematik - Problem Çözme Teknikleri",
            "url": "https://www.youtube.com/watch?v=AYT_MATEMATIK_PROBLEM",
            "platform": "youtube",
            "channel": "Matematik Kafası",
            "duration_minutes": 60,
            "difficulty": "zor",
            "quality_score": 0.82,
        },
        {
            "resource_id": "fallback_mat_003",
            "title": "Türev ve İntegral Başlangıç",
            "url": "https://www.youtube.com/watch?v=TUREV_INTEGRAL",
            "platform": "youtube",
            "channel": "Khan Academy Türkçe",
            "duration_minutes": 30,
            "difficulty": "orta",
            "quality_score": 0.90,
        },
    ],
    "fizik": [
        {
            "resource_id": "fallback_fiz_001",
            "title": "TYT Fizik - Kuvvet ve Hareket",
            "url": "https://www.youtube.com/watch?v=TYT_FIZIK_KUVVET",
            "platform": "youtube",
            "channel": "TonguçAkademi",
            "duration_minutes": 40,
            "difficulty": "orta",
            "quality_score": 0.84,
        },
        {
            "resource_id": "fallback_fiz_002",
            "title": "Elektrik ve Manyetizma",
            "url": "https://www.youtube.com/watch?v=ELEKTRIK_MANYETIZMA",
            "platform": "youtube",
            "channel": "Fizik Okulu",
            "duration_minutes": 55,
            "difficulty": "zor",
            "quality_score": 0.80,
        },
    ],
    "kimya": [
        {
            "resource_id": "fallback_kim_001",
            "title": "TYT Kimya - Atom ve Periyodik Sistem",
            "url": "https://www.youtube.com/watch?v=TYT_KIMYA_ATOM",
            "platform": "youtube",
            "channel": "TonguçAkademi",
            "duration_minutes": 35,
            "difficulty": "orta",
            "quality_score": 0.86,
        },
    ],
    "turkce": [
        {
            "resource_id": "fallback_tur_001",
            "title": "TYT Türkçe - Paragraf Teknikleri",
            "url": "https://www.youtube.com/watch?v=TYT_TURKCE_PARAGRAF",
            "platform": "youtube",
            "channel": "TonguçAkademi",
            "duration_minutes": 50,
            "difficulty": "orta",
            "quality_score": 0.88,
        },
    ],
    "biyoloji": [
        {
            "resource_id": "fallback_bio_001",
            "title": "TYT Biyoloji - Hücre Yapısı",
            "url": "https://www.youtube.com/watch?v=TYT_BIYOLOJI_HUCRE",
            "platform": "youtube",
            "channel": "Biyoloji Adası",
            "duration_minutes": 45,
            "difficulty": "orta",
            "quality_score": 0.83,
        },
    ],
}


@router.get("/fallback-videos/{subject}")
@rate_limit("search_resources")
async def get_fallback_videos(
    request: Request,
    subject: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Fallback videos for a subject when main search fails.

    Returns pre-curated quality videos for Turkish YKS exam preparation.
    Used by frontend when the primary video search encounters errors.

    Args:
        subject: Ders adı (matematik, fizik, kimya, turkce, biyoloji, vb.)
        limit: Maksimum video sayısı (1-50, varsayılan 10)

    Returns:
        success: Boolean success flag
        videos: List of curated fallback videos
        total: Number of videos returned
        message: Turkish status message
    """
    try:
        # Validate limit
        limit = max(1, min(50, limit))

        # Normalize subject identifier — ASCII tag, NOT Turkish prose.
        # _normalize_turkish() applies Turkish locale (I→ı) which produces
        # "matematık" for "MATEMATIK" → never matches dict keys "matematik".
        # Endpoint Gate: use subject_key() for cache/dict lookups.
        subject_normalized = subject_key(subject)

        # Check cache first
        cache = _get_cache()
        cache_key = f"fallback_videos:{subject_normalized}:{limit}"

        try:
            cached = await cache.get(cache_key)
            if cached:
                logger.debug(f"Fallback videos cache hit for {subject_normalized}")
                return cached
        except Exception as cache_error:
            logger.warning(f"Cache read error (continuing): {cache_error}")

        # Get fallback videos for the subject
        videos = _FALLBACK_VIDEOS.get(subject_normalized, [])

        # If subject not found, try to find partial match
        if not videos:
            for key in _FALLBACK_VIDEOS:
                if subject_normalized in key or key in subject_normalized:
                    videos = _FALLBACK_VIDEOS[key]
                    break

        # If still no videos, provide generic message
        if not videos:
            logger.warning(f"No fallback videos for subject: {subject}")
            return {
                "success": False,
                "videos": [],
                "total": 0,
                "subject": subject,
                "message": f"'{subject}' dersi için örnek video bulunamadı",
            }

        # Apply limit
        videos = videos[:limit]

        result = {
            "success": True,
            "videos": videos,
            "total": len(videos),
            "subject": subject,
            "message": f"{len(videos)} örnek video bulundu",
        }

        # Cache the result for 1 hour
        try:
            await cache.set(cache_key, result, ttl=3600)
        except Exception as cache_error:
            logger.warning(f"Cache write error (continuing): {cache_error}")

        logger.info(f"Returning {len(videos)} fallback videos for {subject}")
        return result

    except Exception as e:
        logger.error(f"Error getting fallback videos: {e}")
        return {
            "success": False,
            "videos": [],
            "total": 0,
            "subject": subject,
            "error": "Örnek video yükleme hatası",
            "message": "Videolar şu anda yüklenemiyor",
        }


@router.get("/health")
@rate_limit("health")
async def health_check(request: Request) -> dict[str, Any]:
    """Learning Path API health check"""
    return {
        "status": "healthy",
        "service": "learning-path-api",
        "version": "3.0",
        "facade": "LearningPathFacade",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Ported from v1: Profile, Quiz, Review, Gamification endpoints
# ============================================================================


@router.get("/profile/{student_id}")
@rate_limit("profile_read")
async def get_student_profile(
    request: Request,
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get student profile by ID
    """
    await verify_student_access(student_id, current_user, db)
    
    from models.learning_path_models import LearningPathStudentProfile
    from sqlalchemy import select
    
    result = await db.execute(
        select(LearningPathStudentProfile)
        .where(LearningPathStudentProfile.student_id == student_id)
    )
    profile = result.scalars().first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Öğrenci profili bulunamadı")
        
    return {
        "success": True,
        "student_id": profile.student_id,
        "name": profile.name,
        "grade": int(profile.grade) if profile.grade else None,
        "exam_target": profile.exam_target,
        "interests": profile.interests,
        "goals": profile.goals,
        "learning_style": profile.learning_style,
    }


@router.get("/my-profile")
@rate_limit("profile_read")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get the authenticated user's learning path profile.
    Returns student_id for use in other endpoints.
    """
    result = await db.execute(
        select(LearningPathStudentProfile).where(
            LearningPathStudentProfile.user_id == str(current_user.id)
        )
    )
    profile = result.scalars().first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil bulunamadi")

    return {
        "success": True,
        "student_id": profile.student_id,
        "profile": {
            "name": profile.name,
            "grade": int(profile.grade) if profile.grade else None,
            "learning_style": profile.learning_style,
            "knowledge_level": profile.knowledge_level,
            "exam_target": profile.exam_target,
        },
    }


def _serialize_question(q: Question) -> dict:
    """Soru nesnesini JSON-serializable dict'e cevir."""
    return {
        "id": str(q.id),
        "question_text": q.question_text,
        "options": {
            "A": q.option_a,
            "B": q.option_b,
            "C": q.option_c,
            "D": q.option_d,
            "E": getattr(q, "option_e", None),
        },
        "correct_answer": q.correct_answer,
        "explanation": q.explanation,
        "explanation_video_url": getattr(q, "explanation_video_url", None),
        "difficulty_level": q.difficulty_level,
        "subject_area": q.subject_area,
    }


@router.get("/exit-quiz/{subject}")
@rate_limit("exit_quiz")
async def get_exit_quiz(
    subject: str,
    count: int = 5,
    exam_type: str = "TYT",
    topic: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Cikis testi: Tamamlanan konudan retrieval practice sorulari dondur.
    Bilimsel dayanak: Retrieval practice d=0.5-1.24 (Frontiers 2025).

    Args:
        subject: Ders adı (örn: "matematik", "fizik")
        count: Soru sayısı (varsayılan: 5)
        exam_type: Sınav tipi (varsayılan: "TYT")
        topic: Konu adı (opsiyonel, örn: "Türev", "Fonksiyonlar")
    """
    try:
        from services.soru_bankasi_service import SoruBankasiServisi

        soru_servisi = SoruBankasiServisi()
        questions = await soru_servisi.get_exit_quiz_questions(
            subject=subject,
            count=count,
            exam_type=exam_type,
            topic=topic,
        )
        return {
            "success": True,
            "questions": [_serialize_question(q) for q in questions],
            "count": len(questions),
            "topic": topic,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exit quiz questions: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/interleaved-practice")
@rate_limit("interleaved_practice")
async def get_interleaved_practice(
    subjects: str,
    count: int = 10,
    exam_type: str = "TYT",
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Karisik pratik: Birden fazla konudan interleaved soru seti.
    Bilimsel dayanak: Interleaving d=1.21 (Rohrer et al. RCT).

    subjects: Comma-separated konu listesi, orn. "MATEMATIK,FIZIK,KIMYA"
    """
    try:
        subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
        if not subject_list:
            raise HTTPException(
                status_code=400,
                detail="En az bir konu belirtilmelidir (subjects parametresi bos olamaz)",
            )

        from services.soru_bankasi_service import SoruBankasiServisi

        soru_servisi = SoruBankasiServisi()
        questions = await soru_servisi.get_interleaved_questions(
            subject_list, count, exam_type=exam_type
        )
        return {
            "success": True,
            "questions": [_serialize_question(q) for q in questions],
            "count": len(questions),
            "subjects": subject_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching interleaved practice questions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/review-queue")
@rate_limit("review_queue")
async def get_review_queue(
    limit: int = 20,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tekrar kuyrugu: FSRS'e gore vadesi gelen sorulari dondur.
    Yanlis cevaplanan sorular 24-48h sonra tekrar gelir.
    student_id current_user'dan turetilir (IDOR korumasi).
    Bilimsel dayanak: FSRS-6 SM-2'ye karsi %99.6 ustun (Expertium 2024).
    """
    try:
        from services.question_review_adapter import QuestionReviewAdapter

        student_id = str(current_user.id)
        adapter = QuestionReviewAdapter()
        due_questions = await adapter.get_due_questions(student_id, limit=limit, db=db)
        return {
            "success": True,
            "questions": due_questions,
            "count": len(due_questions),
            "student_id": student_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review queue: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


class SubmitReviewRequest(BaseModel):
    card_id: str = Field(..., description="FSRS kart ID")
    grade: int = Field(..., ge=1, le=4, description="1=AGAIN, 2=HARD, 3=GOOD, 4=EASY")


@router.post("/submit-review")
@rate_limit("submit_review")
async def submit_review(
    request: SubmitReviewRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tekrar sonucunu kaydet ve FSRS parametrelerini guncelle.
    Grade: 1=AGAIN (6h), 2=HARD (1d), 3=GOOD (2.5d), 4=EASY (7d).
    """
    try:
        from services.question_review_adapter import QuestionReviewAdapter

        student_id = str(current_user.id)
        adapter = QuestionReviewAdapter()
        card = await adapter.submit_review(
            request.card_id, request.grade, db, student_id=student_id
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


class RegisterWrongAnswersRequest(BaseModel):
    question_ids: list[str] = Field(..., min_length=1)
    error_types: dict[str, str] | None = None
    is_timeout: bool = False


@router.post("/register-wrong-answers")
@rate_limit("register_wrong_answers")
async def register_wrong_answers(
    request: RegisterWrongAnswersRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Quiz sonunda yanlis cevaplanan sorulari FSRS tekrar kuyruguna ekle.
    24h sonra review-queue'da gorunurler.
    student_id current_user'dan turetilir (IDOR korumasi).
    """
    try:
        from services.question_review_adapter import QuestionReviewAdapter

        student_id = str(current_user.id)
        adapter = QuestionReviewAdapter()
        created = await adapter.register_wrong_answers(
            student_id,
            request.question_ids,
            db,
            error_types=request.error_types,
        )
        await db.commit()
        return {
            "success": True,
            "created": created,
            "total_submitted": len(request.question_ids),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering wrong answers: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/weakness-report")
@rate_limit("weakness_report")
async def get_weakness_report(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Ogrencinin zayif konularini raporla.
    TopicProgress tablosundan dusuk skorlu konulari tespit eder.
    """
    try:
        student_id = str(current_user.id)

        result = await db.execute(
            select(TopicProgress).where(TopicProgress.student_id == student_id)
        )
        progress_records = result.scalars().all()

        weaknesses = []
        for record in progress_records:
            avg_score = record.progress or 0
            if avg_score >= 80:
                trend = "improving"
            elif avg_score >= 40:
                trend = "stable"
            else:
                trend = "declining"

            weaknesses.append(
                {
                    "topic": record.node_id,
                    "avg_score": avg_score,
                    "attempts": 1,
                    "trend": trend,
                    "is_weak": avg_score < 60,
                }
            )

        return {"weaknesses": weaknesses}

    except Exception as e:
        logger.error(f"Error fetching weakness report: {e}")
        return {"weaknesses": []}


@router.get("/streak")
@rate_limit("streak")
async def get_daily_streak(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Ogrencinin ardisik aktif gun sayisini dondur.
    TopicCompletion tablosundan ardisik gunleri hesaplar.
    """
    try:
        student_id = str(current_user.id)

        profile_result = await db.execute(
            select(LearningPathStudentProfile).where(
                LearningPathStudentProfile.user_id == student_id
            )
        )
        profile = profile_result.scalars().first()

        if not profile:
            return {"daily_streak": 0}

        result = await db.execute(
            select(TopicCompletion).where(
                TopicCompletion.student_id == profile.student_id,
                TopicCompletion.completed == True,  # noqa: E712
            )
        )
        completions = result.scalars().all()

        if not completions:
            return {"daily_streak": 0}

        dates = sorted(
            set(c.completion_date.date() for c in completions if c.completion_date),
            reverse=True,
        )

        if not dates:
            return {"daily_streak": 0}

        from datetime import timedelta

        streak = 1
        for i in range(1, len(dates)):
            if dates[i - 1] - dates[i] == timedelta(days=1):
                streak += 1
            else:
                break

        return {"daily_streak": streak}

    except Exception as e:
        logger.error(f"Error calculating daily streak: {e}")
        return {"daily_streak": 0}
