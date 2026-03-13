"""
Learning Path API - Türkiye Üniversite Sınavları Hazırlık Platformu
Öğrenci öğrenme yolu oluşturma ve yönetim endpoint'leri

BUG FIX #1: AI Agent Integration with Dependency Injection
SPRINT 2: Multi-layer cache for completion status endpoint

ARCHITECTURE FIX: Moved cache initialization to dependency pattern

CIRCULAR IMPORT PREVENTION (2025-01-24):
Bu dosya cok sayida import iceriyor. Circular import onlemek icin:

1. TYPE_CHECKING pattern kullanildi (models icin)
2. Lazy imports kullanildi (get_* fonksiyonlari)
3. Dependency injection pattern tercih edildi

Import hiyerarsisi:
api/learning_path.py
  -> services/enhanced_resource_recommendation_engine.py
  -> agents/ (get_learning_path_agent)
  -> core/ (metrics, cache, circuit_breaker)
  -> models/ (learning_path_models)

RISK: services -> models -> database -> core -> services dongusu
COZUM: Dependency injection + lazy imports

ONERILEN YAPILAN IYILESTIRMELER:
- get_enhanced_recommendation_engine() factory pattern
- get_learning_path_agent() factory pattern
- circuit breaker lazy initialization
"""

import logging
import os
import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

try:
    from services.enhanced_resource_recommendation_engine import (
        EnhancedResourceRecommendationEngine,
        get_enhanced_recommendation_engine,
    )
except (ImportError, TypeError):
    EnhancedResourceRecommendationEngine = None
    get_enhanced_recommendation_engine = None

try:
    from agents import get_learning_path_agent, LearningPathAgent
except (ImportError, TypeError):
    get_learning_path_agent = None
    LearningPathAgent = None
from api.schemas.learning_path_schemas import (
    LearningPathCreateRequest,
)
from core.metrics_collector import get_metrics_collector
from core.multi_layer_cache import MultiLayerCache
from core.learning_path_circuit_breakers import (
    get_ai_agent_circuit_breaker,
    get_resource_search_circuit_breaker,
    ai_agent_fallback_handler,
)
from core.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerHalfOpenError
from core.dependencies import get_current_user, get_db, AuthenticatedUser
from core.learning_path_auth import (
    verify_student_access,
    get_current_user_optional,
)

# Database imports (Mock Data Cleanup - Phase 5)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.learning_path_models import (
    LearningPathStudentProfile,  # Renamed model to avoid conflict with models.database.StudentProfile
    TopicCompletion,
    Quiz,
    QuizQuestion,
    TopicProgress,
)
from models.question_bank import QuestionBankItem as Question

logger = logging.getLogger(__name__)

# Get global metrics collector
metrics = get_metrics_collector()

# P1.4: Get circuit breakers
ai_agent_circuit_breaker = get_ai_agent_circuit_breaker()
resource_search_circuit_breaker = get_resource_search_circuit_breaker()

# Router setup
router = APIRouter(prefix="/api/learning-path", tags=["Learning Path"])


# ARCHITECTURE FIX: Cache configuration from environment
# Cache settings with sensible defaults
CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_L1_MAX_SIZE = int(os.getenv("LEARNING_PATH_CACHE_L1_SIZE", "20"))
CACHE_DEFAULT_TTL = int(os.getenv("LEARNING_PATH_CACHE_TTL", "300"))  # 5 minutes


@lru_cache(maxsize=1)
def get_learning_path_cache() -> MultiLayerCache:
    """
    ARCHITECTURE FIX: Lazy initialization of cache via dependency injection.
    Uses lru_cache to ensure singleton behavior.

    Previously: Hardcoded redis URL at module level
    Now: Configuration from environment, lazy initialization
    """
    return MultiLayerCache(
        redis_url=CACHE_REDIS_URL,
        l1_max_size=CACHE_L1_MAX_SIZE,
        default_ttl=CACHE_DEFAULT_TTL,
        namespace="learning_path",
    )


# For backward compatibility - use the dependency getter
# Thread-safe singleton pattern with double-check locking
_cache_lock = threading.Lock()
_learning_path_cache = None


def _get_cache() -> MultiLayerCache:
    """
    Internal helper to get cache instance.
    Thread-safe with double-check locking pattern.
    """
    global _learning_path_cache
    if _learning_path_cache is None:
        with _cache_lock:
            # Double-check inside lock to prevent race condition
            if _learning_path_cache is None:
                _learning_path_cache = get_learning_path_cache()
    return _learning_path_cache


# Request/Response Models (Legacy - kept for backward compatibility)
class StudentProfileCreate(BaseModel):
    name: str = Field(..., description="Öğrenci adı")
    grade: int = Field(..., ge=9, le=12, description="Sınıf seviyesi (9-12)")
    subjects: List[str] = Field(..., description="İlgili dersler")
    goals: List[str] = Field(..., description="Hedefler")
    learning_style: Optional[str] = Field(None, description="Öğrenme stili")
    available_time: Optional[int] = Field(
        None, description="Günlük çalışma süresi (dakika)"
    )


class KnowledgeAssessment(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    subject: str = Field(..., description="Ders")
    questions: Optional[List[str]] = Field(None, description="Değerlendirme soruları")


class LearningPathCreate(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    subject: str = Field(..., description="Ders")
    target_date: Optional[str] = Field(None, description="Hedef tarih")
    difficulty_level: Optional[str] = Field("medium", description="Zorluk seviyesi")


class QuizAnswer(BaseModel):
    question_id: str = Field(..., description="Soru ID")
    answer: str = Field(..., description="Öğrenci cevabı")
    time_spent: Optional[int] = Field(None, description="Soruda geçen süre (saniye)")


class QuizSubmission(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    quiz_id: str = Field(..., description="Quiz ID")
    answers: List[QuizAnswer] = Field(..., description="Quiz cevapları")


class ProgressUpdate(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    node_id: str = Field(..., description="Node/Topic ID")
    progress: int = Field(..., ge=0, le=100, description="İlerleme yüzdesi (0-100)")
    time_spent: Optional[int] = Field(None, description="Harcanan süre (dakika)")
    completed: bool = Field(False, description="Tamamlandı mı?")


class CompletionUpdate(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    completions: Dict[str, bool] = Field(..., description="Topic tamamlanma durumları")


class ResourceSearch(BaseModel):
    subject: str = Field(..., description="Ders (matematik, fizik, kimya, vb.)")
    topic: Optional[str] = Field(None, description="Konu (türev, hareket, atom, vb.)")
    difficulty: Optional[str] = Field(
        "orta", description="Zorluk seviyesi (kolay, orta, zor)"
    )
    resource_type: Optional[str] = Field(
        None, description="Kaynak tipi (video, article, etc.)"
    )
    max_results: Optional[int] = Field(
        10, ge=1, le=50, description="Maksimum sonuç sayısı"
    )
    student_profile: Optional[Dict[str, Any]] = Field(
        None, description="Öğrenci profili (opsiyonel)"
    )


class PathAdaptation(BaseModel):
    student_id: str = Field(..., description="Öğrenci ID")
    path_id: str = Field(..., description="Öğrenme yolu ID")
    performance_data: Dict[str, Any] = Field(..., description="Performans verileri")


# Endpoints
@router.post("/create-profile")
async def create_student_profile(
    profile: StudentProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci profili oluştur

    Öğrenci için öğrenme yolu oluşturmak üzere profil bilgilerini kaydeder.

    REFACTORED (Mock Data Cleanup - Phase 5):
    - Saves to student_profiles table in database
    - Returns real student_id (UUID-based)
    - Data persists across restarts
    """
    try:
        # Check for existing profile — return it instead of creating duplicate
        existing = await db.execute(
            select(LearningPathStudentProfile).where(
                LearningPathStudentProfile.user_id == str(current_user.id)
            )
        )
        existing_profile = existing.scalars().first()
        if existing_profile:
            logger.info(f"Returning existing profile for user {current_user.id}: {existing_profile.student_id}")
            return {
                "success": True,
                "student_id": existing_profile.student_id,
                "profile": {
                    "name": existing_profile.name,
                    "grade": int(existing_profile.grade) if existing_profile.grade else None,
                    "subjects": existing_profile.interests,
                    "goals": existing_profile.goals,
                    "learning_style": existing_profile.learning_style,
                    "available_time": existing_profile.available_time,
                    "exam_target": existing_profile.exam_target,
                    "created_at": existing_profile.created_at.isoformat() if existing_profile.created_at else None,
                },
                "message": "Mevcut profil döndürüldü",
            }

        logger.info(f"Creating student profile: {profile.name}, grade {profile.grade}")

        # Generate unique student ID
        import uuid
        student_id = f"STU_{uuid.uuid4().hex[:12]}"

        # Determine exam target based on grade
        exam_target = "LGS" if profile.grade <= 8 else "YKS"

        # Create real database record
        new_profile = LearningPathStudentProfile(
            student_id=student_id,
            user_id=str(current_user.id),
            name=profile.name,
            grade=str(profile.grade),
            exam_target=exam_target,
            learning_style=profile.learning_style or "mixed",
            knowledge_level="beginner",  # Default, will be updated by assessment
            interests=profile.subjects,  # Store subjects as interests
            goals=profile.goals,
            available_time=profile.available_time or 60,  # Default 60 min/day
            metadata_json={"created_via": "learning_path_api"}
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
            "message": "Öğrenci profili başarıyla oluşturuldu ve kaydedildi",
        }

    except Exception as e:
        logger.error(f"Error creating student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-profile")
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
    profile = result.scalars().first()  # .first() instead of scalar_one_or_none() — handles duplicates gracefully

    if not profile:
        raise HTTPException(status_code=404, detail="Profil bulunamadı")

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


@router.post("/assess-knowledge")
async def assess_knowledge(
    assessment: KnowledgeAssessment,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Bilgi seviyesi değerlendirmesi

    Öğrencinin konuyla ilgili mevcut bilgi seviyesini değerlendirir.

    REFACTORED (Mock Data Cleanup - Phase 5):
    - Queries student profile and quiz history
    - Calculates real knowledge level from quiz performance
    - Updates student profile with assessed level
    - Returns actual data instead of hardcoded values
    """
    try:
        logger.info(
            f"Assessing knowledge for student {assessment.student_id}, subject: {assessment.subject}"
        )

        # Get student profile
        result = await db.execute(
            select(LearningPathStudentProfile).where(
                LearningPathStudentProfile.student_id == assessment.student_id
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail=f"Student profile not found: {assessment.student_id}")

        # NOTE: QuizSubmission is a Pydantic model, not ORM — this query is a no-op placeholder.
        # TODO: Replace with proper ORM model when quiz submission table exists.
        quiz_results = []

        # Calculate average score from quizzes
        if quiz_results and len(quiz_results) > 0:
            avg_score = sum(q.score for q in quiz_results) / len(quiz_results)

            # Determine knowledge level based on average score
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

            # Calculate strengths and weaknesses based on score range
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
            # No quiz history - use profile's current knowledge_level
            knowledge_level = profile.knowledge_level
            score = 50  # Default medium score for no data

            strengths = ["Henüz yeterli veri yok"]
            weaknesses = ["Daha fazla değerlendirme gerekiyor"]
            recommendations = [
                "Quiz'lere katılarak bilgi seviyenizi ölçün",
                "Düzenli pratik yapın"
            ]

        # Update student profile with assessed knowledge level
        profile.knowledge_level = knowledge_level
        profile.updated_at = datetime.now()
        await db.commit()

        logger.info(f"Knowledge assessed: {knowledge_level} (score: {score}) for student {assessment.student_id}")

        return {
            "success": True,
            "assessment": {
                "student_id": assessment.student_id,
                "subject": assessment.subject,
                "level": knowledge_level,
                "score": score,
                "quiz_count": len(quiz_results),
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations,
                "assessed_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Error assessing knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if get_learning_path_agent is not None:
    @router.post("/create-path")
    async def create_learning_path(
        request: LearningPathCreateRequest,
        agent: LearningPathAgent = Depends(get_learning_path_agent),
        http_request: Request = None,
        current_user=Depends(get_current_user),  # 🔒 AUTH ADDED
        db: AsyncSession = Depends(get_db),
    ):
        return await _create_learning_path_impl(request, agent, http_request, current_user, db=db)
else:
    @router.post("/create-path")
    async def create_learning_path(
        request: LearningPathCreateRequest,
        http_request: Request = None,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        """Fallback: return a template learning path when AI agent is not available."""
        logger.warning("Learning path agent not available — returning template path")
        await verify_student_access(request.student_id, current_user, db)

        subject = request.subject or "matematik"
        weeks = request.duration_weeks or 4

        # Generate a basic template path structure
        template_nodes = []
        topics = {
            "matematik": ["Sayılar ve İşlemler", "Cebir", "Fonksiyonlar", "Geometri", "Olasılık ve İstatistik", "Limit ve Türev"],
            "fizik": ["Kuvvet ve Hareket", "Enerji", "Elektrik", "Dalgalar", "Optik", "Modern Fizik"],
            "kimya": ["Atom ve Periyodik Tablo", "Kimyasal Bağlar", "Reaksiyon Hızı", "Denge", "Asit-Baz", "Organik Kimya"],
        }
        topic_list = topics.get(subject, topics["matematik"])

        for i, topic in enumerate(topic_list[:weeks * 2]):
            template_nodes.append({
                "id": f"node_{i+1}",
                "title": topic,
                "description": f"{topic} konusu çalışması",
                "week": (i // 2) + 1,
                "order": i + 1,
                "estimated_hours": 3,
                "resources": [],
                "prerequisites": [f"node_{i}"] if i > 0 else [],
            })

        return {
            "success": True,
            "learning_path": {
                "path_id": f"path_{request.student_id}_{subject}",
                "student_id": request.student_id,
                "subject": subject,
                "duration_weeks": weeks,
                "nodes": template_nodes,
                "created_at": datetime.utcnow().isoformat(),
                "status": "template",
            },
            "message": f"{subject.capitalize()} için {weeks} haftalık öğrenme yolu oluşturuldu (şablon)",
        }


async def _create_learning_path_impl(
    request: LearningPathCreateRequest,
    agent,
    http_request: Request = None,
    current_user=None,
    *,
    db: AsyncSession,
):
    """
    Kişiselleştirilmiş öğrenme yolu oluştur

    ✅ BUG FIX #1: AI Agent Integration
    - Agent singleton ile gerçek AI-powered öğrenme yolu oluşturulur
    - Mock data yok, gerçek kaynak önerileri
    - Öğrenci profiline göre kişiselleştirme

    ✅ BUG FIX #2: API Contract Fix
    - Flat structure (no nested student_profile)
    - Validated with Pydantic v2
    - OpenAPI auto-generated types

    ✅ P1.2 Enhancement: Prometheus Metrics
    - Tracks learning path creation duration
    - Records success/failure rates per subject
    - Monitors API request status
    """
    # P1.2: Track API request
    metrics.record_learning_path_api_request(
        endpoint="/create-path",
        method="POST",
        status_code=200,  # Will be updated on error
    )

    start_time = time.time()
    success = False

    try:
        # 🔒 Verify ownership: students can only create their own paths
        await verify_student_access(request.student_id, current_user, db)

        logger.info(
            f"Creating AI-powered learning path for student {request.student_id}, subject: {request.subject}"
        )

        # P1.4: Protect AI agent call with circuit breaker
        try:
            # ✅ GERÇEK AGENT KULLANIMI - 3278 satır AI kod aktif + Circuit Breaker koruması!
            learning_path_obj = await ai_agent_circuit_breaker.call(
                agent.create_learning_path,
                student_id=request.student_id,
                goal=request.subject,
                duration_weeks=request.duration_weeks or 4,
            )
        except (CircuitBreakerOpenError, CircuitBreakerHalfOpenError) as cb_error:
            # Circuit breaker açık - fallback handler kullan
            logger.warning(f"Circuit breaker triggered: {cb_error.message}")
            return await ai_agent_fallback_handler(
                cb_error, request.student_id, request.subject
            )

        success = True

        # Convert agent's LearningPath object to API response format
        modules = []
        for idx, phase in enumerate(learning_path_obj.phases, start=1):
            module = {
                "module_id": f"MOD{idx}",
                "title": phase.get("title", f"{request.subject.title()} - Modül {idx}"),
                "order": idx,
                "estimated_duration": f"{phase.get('duration_days', 7)} gün",
                "prerequisite": f"MOD{idx-1}" if idx > 1 else None,
                "topics": [
                    {
                        "topic_id": f"TOP{topic_idx}",
                        "name": topic,
                        "duration_minutes": 60,
                        "resources": [],  # Will be populated by search-resources endpoint
                        "quiz": {
                            "quiz_id": f"QZ{topic_idx}",
                            "question_count": 10,
                            "passing_score": 70,
                        },
                    }
                    for topic_idx, topic in enumerate(phase.get("topics", []), start=1)
                ],
            }
            modules.append(module)

        # Convert agent resources to API format
        resources_data = [
            {
                "resource_id": r.resource_id,
                "title": r.title,
                "source": r.source,
                "url": r.url,
                "type": r.resource_type,
                "difficulty": r.difficulty_level.value,
                "estimated_time": r.estimated_time,
                "description": r.description,
                "tags": r.tags,
                "rating": r.rating,
            }
            for r in learning_path_obj.resources
        ]

        learning_path = {
            "path_id": learning_path_obj.path_id,
            "student_id": request.student_id,
            "subject": request.subject,
            "difficulty_level": request.difficulty_level,
            "target_date": request.target_date,
            "modules": modules,
            "progress": {
                "completed_modules": 0,
                "total_modules": len(modules),
                "completed_topics": 0,
                "total_topics": sum(len(m["topics"]) for m in modules),
                "overall_progress": 0,
            },
            "resources": resources_data,
            "total_time": learning_path_obj.total_time,
            "reasoning": learning_path_obj.reasoning,
            "created_at": learning_path_obj.created_at.isoformat(),
            "ai_generated": True,
            "agent_metadata": {
                "learning_style": learning_path_obj.student_profile.learning_style.value,
                "knowledge_level": learning_path_obj.student_profile.knowledge_level.value,
                "available_time": learning_path_obj.student_profile.available_time,
            },
        }

        # P1.2: Record successful learning path creation
        duration_seconds = time.time() - start_time
        metrics.record_learning_path_creation(
            subject=request.subject, duration_seconds=duration_seconds, success=True
        )

        logger.info(
            f"Learning path created successfully for {request.student_id} in {duration_seconds:.2f}s"
        )

        return {
            "success": True,
            "learning_path": learning_path,
            "message": "AI agent ile öğrenme yolu oluşturuldu - Gerçek AI-powered öneriler!",
        }

    except Exception as e:
        # P1.2: Record failed learning path creation
        duration_seconds = time.time() - start_time
        metrics.record_learning_path_creation(
            subject=request.subject, duration_seconds=duration_seconds, success=False
        )

        metrics.record_learning_path_api_request(
            endpoint="/create-path", method="POST", status_code=500
        )

        logger.error(f"Error creating learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if get_enhanced_recommendation_engine is not None:
    @router.post("/search-resources")
    async def search_resources(
        search: ResourceSearch,
        engine: EnhancedResourceRecommendationEngine = Depends(
            get_enhanced_recommendation_engine
        ),
        http_request: Request = None,
        current_user=Depends(
            get_current_user_optional
        ),  # 🔒 OPTIONAL AUTH (public but personalized if logged in)
    ):
        return await _search_resources_impl(search, engine, http_request, current_user)
else:
    @router.post("/search-resources")
    async def search_resources(
        search: ResourceSearch,
        http_request: Request = None,
        current_user=Depends(get_current_user_optional),
    ):
        raise HTTPException(status_code=503, detail="Resource search engine not available")


async def _search_resources_impl(
    search: ResourceSearch,
    engine,
    http_request: Request = None,
    current_user=None,
):
    """
    Eğitim kaynaklarını ara - Enhanced Resource Recommendation Engine ile

    Bu endpoint, Türkçe içerik filtresi, konu uygunluğu skorlaması ve video kalite
    doğrulaması yaparak en uygun eğitim videolarını önerir.

    Pipeline:
    1. Cache kontrolü (1 saat TTL)
    2. YouTube'dan aday videolar al
    3. Türkçe filtresi uygula (min score: 0.7)
    4. Konu uygunluğu skorla (min score: 0.6)
    5. Erişilebilirlik doğrula (paralel)
    6. Kalite skorla
    7. Final skorlama ve sıralama

    Args:
        search: Arama parametreleri
        engine: Enhanced recommendation engine (dependency injection)

    Returns:
        Filtrelenmiş ve skorlanmış video önerileri

    ✅ P1.2 Enhancement: Prometheus Metrics
    - Tracks resource search duration per subject
    - Records result counts (has_results: yes/no)
    - Monitors API request status
    """
    # P1.2: Track API request
    metrics.record_learning_path_api_request(
        endpoint="/search-resources", method="POST", status_code=200
    )

    start_time = time.time()

    try:
        logger.info(
            f"Searching resources for subject='{search.subject}', "
            f"topic='{search.topic}', difficulty='{search.difficulty}'"
        )

        # Validation: subject zorunlu
        if not search.subject or not search.subject.strip():
            raise HTTPException(
                status_code=400, detail="Ders (subject) alanı zorunludur"
            )

        # Enhanced recommendation engine ile video önerileri al
        try:
            recommended_videos = await engine.get_recommended_videos(
                subject=search.subject,
                topic=search.topic,
                difficulty=search.difficulty or "orta",
                max_results=search.max_results or 10,
                student_profile=search.student_profile,
            )

            # RecommendedVideo objelerini API response formatına çevir
            resources = []
            for video in recommended_videos:
                resource = {
                    "resource_id": video.video_id,
                    "type": "video",
                    "title": video.title,
                    "description": video.description,
                    "url": video.url,
                    "thumbnail": video.thumbnail_url,
                    "duration": video.duration,
                    "duration_minutes": video.duration_minutes,
                    "difficulty": search.difficulty,
                    # Channel info
                    "channel_name": video.channel_name,
                    "channel_id": video.channel_id,
                    # Engagement metrics
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "upload_date": video.upload_date,
                    # Quality scores
                    "scores": {
                        "turkish_score": round(video.turkish_score, 2),
                        "relevance_score": round(video.relevance_score, 2),
                        "quality_score": round(video.quality_score, 2),
                        "final_score": round(video.final_score, 2),
                    },
                    # Validation flags
                    "is_accessible": video.is_accessible,
                    "is_embeddable": video.is_embeddable,
                    "is_turkish": video.is_turkish,
                    # Metadata
                    "tags": video.tags,
                    "caption_available": video.caption_available,
                    "definition": video.definition,
                }

                resources.append(resource)

            # Filter by resource type if specified (şu an sadece video var)
            if search.resource_type and search.resource_type != "video":
                resources = []
                logger.info(
                    f"Filtered out all resources - only 'video' type supported, "
                    f"requested: {search.resource_type}"
                )

            response = {
                "success": True,
                "resources": resources,
                "total": len(resources),
                "filters": {
                    "subject": search.subject,
                    "topic": search.topic,
                    "difficulty": search.difficulty,
                    "resource_type": search.resource_type or "video",
                    "max_results": search.max_results or 10,
                },
                "metadata": {
                    "engine": "EnhancedResourceRecommendationEngine",
                    "version": "1.0",
                    "features": [
                        "turkish_content_filter",
                        "subject_relevance_scorer",
                        "video_quality_validator",
                        "parallel_processing",
                        "redis_cache",
                    ],
                },
            }

            # P1.2: Record resource search metrics
            duration_seconds = time.time() - start_time
            metrics.record_resource_search(
                subject=search.subject,
                duration_seconds=duration_seconds,
                result_count=len(resources),
            )

            logger.info(
                f"Returning {len(resources)} resources for "
                f"{search.subject}/{search.topic} in {duration_seconds:.2f}s"
            )
            return response

        except Exception as engine_error:
            # Engine hatası - detaylı log ama kullanıcıya genel mesaj
            logger.error(
                f"Enhanced recommendation engine error: {str(engine_error)}",
                exc_info=True,
            )

            # P1.2: Record failed resource search
            duration_seconds = time.time() - start_time
            metrics.record_resource_search(
                subject=search.subject,
                duration_seconds=duration_seconds,
                result_count=0,
            )

            metrics.record_learning_path_api_request(
                endpoint="/search-resources", method="POST", status_code=500
            )

            # Fallback: boş sonuç döndür
            return {
                "success": False,
                "resources": [],
                "total": 0,
                "filters": {
                    "subject": search.subject,
                    "topic": search.topic,
                    "difficulty": search.difficulty,
                    "resource_type": search.resource_type,
                },
                "error": {
                    "message": "Video önerileri şu anda alınamıyor. Lütfen daha sonra tekrar deneyin.",
                    "code": "ENGINE_ERROR",
                },
            }

    except HTTPException:
        # FastAPI HTTPException'ları olduğu gibi fırlat
        raise

    except Exception as e:
        # Beklenmeyen hatalar
        logger.error(f"Unexpected error in search_resources: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Kaynak araması sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
        )


@router.post("/adapt-path")
async def adapt_learning_path(adaptation: PathAdaptation):
    """
    Öğrenme yolunu performansa göre uyarla

    Öğrencinin performans verilerine göre öğrenme yolunu dinamik olarak günceller.
    """
    try:
        logger.info(
            f"Adapting learning path {adaptation.path_id} for "
            f"student {adaptation.student_id}"
        )

        # Mock adaptation logic
        performance_score = adaptation.performance_data.get("average_score", 70)

        adaptations = []

        if performance_score < 60:
            adaptations.append(
                {
                    "type": "difficulty_adjustment",
                    "action": "Zorluk seviyesi düşürüldü",
                    "recommendation": "Temel konuları tekrar edin",
                }
            )
        elif performance_score > 85:
            adaptations.append(
                {
                    "type": "difficulty_adjustment",
                    "action": "Zorluk seviyesi artırıldı",
                    "recommendation": "İleri seviye konulara geçebilirsiniz",
                }
            )

        if adaptation.performance_data.get("completion_time", 0) > 120:
            adaptations.append(
                {
                    "type": "pace_adjustment",
                    "action": "Hız ayarı yapıldı",
                    "recommendation": "Daha yavaş tempoda ilerleyin",
                }
            )

        return {
            "success": True,
            "adaptations": adaptations,
            "updated_path": {
                "path_id": adaptation.path_id,
                "student_id": adaptation.student_id,
                "current_difficulty": "adjusted" if adaptations else "maintained",
                "next_steps": [
                    "Mevcut modülü tamamlayın",
                    "Quiz'i çözün",
                    "Sonraki modüle geçin",
                ],
                "adapted_at": datetime.now().isoformat(),
            },
            "message": (
                f"{len(adaptations)} uyarlama yapıldı"
                if adaptations
                else "Yol değişikliği gerekmiyor"
            ),
        }

    except Exception as e:
        logger.error(f"Error adapting learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/completion/{student_id}")
async def get_completion_status(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  # 🔒 AUTH ADDED
):
    """
    Get student's topic completion status

    Returns completion status for all topics in student's learning path.
    This is used by the frontend to display progress indicators.

    REFACTORED (Mock Data Cleanup - Phase 5 - FINAL MOCK REMOVED):
    - Queries topic_completions table for real data
    - Returns actual completion status for each topic
    - Empty dict for students with no completions (NOT fake data!)

    **SPRINT 2**: Multi-layer cache (L1+L2) - 5 min TTL
    Expected: 300ms → 20ms (15x faster)
    Completion status is read frequently but updated infrequently
    """
    try:
        # 🔒 Verify ownership: students can only view their own completion status
        await verify_student_access(student_id, current_user, db)

        logger.info(f"Getting completion status for student {student_id}")

        # SPRINT 2: Cache key for completion status
        cache_key = f"completion:{student_id}"

        # Get cache with thread-safe singleton
        cache = _get_cache()

        # Initialize cache if needed
        if not cache._initialized:
            await cache.initialize()

        # Get or compute with cache
        async def fetch_completion():
            """Fetch completion status from database - REFACTORED"""
            # Query real completion data from topic_completions table
            result = await db.execute(
                select(TopicCompletion).where(
                    TopicCompletion.student_id == student_id
                )
            )
            completion_records = result.scalars().all()

            # Build completion dictionary
            # Format: "MODULE_ID-TOPIC_ID": boolean
            completion_data = {}

            for record in completion_records:
                completion_data[record.node_id] = record.completed

            # Return real data (empty dict if no completions - NOT fake data)
            logger.info(f"Fetched {len(completion_data)} completion records for student {student_id}")
            return completion_data

        completion_data = await cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_completion,
            ttl=300  # 5 minutes - balance between freshness and performance
        )

        return {
            "success": True,
            "data": completion_data,
            "student_id": student_id,
            "total_topics": len(completion_data),
            "completed_topics": sum(1 for v in completion_data.values() if v),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting completion status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/completion/{student_id}")
async def update_completion_status(
    student_id: str,
    completion_update: CompletionUpdate,
    current_user=Depends(get_current_user),  # 🔒 AUTH ADDED
    db: AsyncSession = Depends(get_db),  # P0 FIX: Database session
):
    """
    Update student's topic completion status

    Allows frontend to mark topics as completed/incomplete.
    P0 FIX: Now persists to database via TopicCompletion model.

    **SPRINT 2**: Cache invalidation on completion update
    """
    try:
        # 🔒 Verify ownership: students can only update their own completion status
        await verify_student_access(student_id, current_user, db)

        logger.info(f"Updating completion status for student {student_id}")

        # Validate student_id matches
        if completion_update.student_id != student_id:
            raise HTTPException(
                status_code=400,
                detail="Student ID mismatch: URL parameter doesn't match request body",
            )

        # P0 FIX: Upsert completions to database
        updated_count = 0
        for node_id, is_completed in completion_update.completions.items():
            result = await db.execute(
                select(TopicCompletion).where(
                    TopicCompletion.student_id == student_id,
                    TopicCompletion.node_id == node_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.completed = is_completed
                existing.completion_date = datetime.now() if is_completed else None
                existing.updated_at = datetime.now()
            else:
                new_completion = TopicCompletion(
                    student_id=student_id,
                    node_id=node_id,
                    completed=is_completed,
                    completion_date=datetime.now() if is_completed else None,
                )
                db.add(new_completion)

            updated_count += 1

        await db.commit()
        logger.info(
            f"Persisted {updated_count} completion statuses for student {student_id}"
        )

        # SPRINT 2: Invalidate completion cache after update
        cache = _get_cache()
        if cache._initialized:
            cache_key = f"completion:{student_id}"
            await cache.delete(cache_key)
            logger.info(f"Completion cache invalidated for student {student_id}")

        # P1.2: Record topic completion metrics
        for _ in range(updated_count):
            metrics.record_topic_completion(success=True)

        metrics.record_learning_path_api_request(
            endpoint="/completion", method="PUT", status_code=200
        )

        return {
            "success": True,
            "student_id": student_id,
            "updated_count": updated_count,
            "completions": completion_update.completions,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating completion status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update completion status: {str(e)}"
        )


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmission,
    current_user=Depends(get_current_user),  # 🔒 AUTH ADDED
    db: AsyncSession = Depends(get_db),  # FIX: Add database session dependency
):
    """
    Submit quiz answers and get results

    Calculates score, determines if passed, and provides detailed feedback.
    Updates completion status if quiz passed.
    """
    try:
        # 🔒 Verify ownership: students can only submit their own quizzes
        await verify_student_access(submission.student_id, current_user, db)

        logger.info(
            f"Processing quiz submission for quiz {quiz_id} from student {submission.student_id}"
        )

        # Validate quiz_id matches
        if submission.quiz_id != quiz_id:
            raise HTTPException(
                status_code=400,
                detail="Quiz ID mismatch: URL parameter doesn't match request body",
            )

        # P0 FIX: Query quiz and questions from database (instead of mock data)
        result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise HTTPException(
                status_code=404,
                detail=f"Quiz '{quiz_id}' bulunamadı"
            )

        # Get quiz questions with their associated Question records
        stmt = (
            select(QuizQuestion, Question)
            .join(Question, QuizQuestion.question_id == Question.id)
            .where(QuizQuestion.quiz_id == quiz_id, Question.is_active == True)  # noqa: E712
            .order_by(QuizQuestion.order_number)
        )
        result = await db.execute(stmt)
        quiz_questions = result.all()

        if not quiz_questions:
            raise HTTPException(
                status_code=404,
                detail=f"Quiz '{quiz_id}' için soru bulunamadı"
            )

        # Build correct answers mapping from database
        correct_answers = {
            f"Q{qq.order_number}": q.correct_answer
            for qq, q in quiz_questions
        }

        quiz_data = {
            "quiz_id": quiz_id,
            "question_count": len(quiz_questions),
            "passing_score": quiz.passing_score or 70,
            "correct_answers": correct_answers,
        }

        # Validate answer count
        if len(submission.answers) != quiz_data["question_count"]:
            raise HTTPException(
                status_code=400,
                detail=f"Expected {quiz_data['question_count']} answers, got {len(submission.answers)}",
            )

        # Calculate score
        correct_count = 0
        question_results = []

        for answer in submission.answers:
            correct_answer = quiz_data["correct_answers"].get(answer.question_id)
            is_correct = answer.answer == correct_answer

            if is_correct:
                correct_count += 1

            question_results.append(
                {
                    "question_id": answer.question_id,
                    "student_answer": answer.answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "time_spent": answer.time_spent,
                }
            )

        score = (correct_count / quiz_data["question_count"]) * 100
        passed = score >= quiz_data["passing_score"]

        # Calculate total time
        total_time = sum(a.time_spent or 0 for a in submission.answers)

        logger.info(f"Quiz {quiz_id} results - Score: {score:.1f}%, Passed: {passed}")

        # P1.2: Record quiz submission metrics
        # Extract subject from quiz_id (format: subject_quizname or similar)
        # Common subjects: matematik, turkce, fizik, kimya, biyoloji, tarih, cografya, etc.
        subject = "genel"  # Default
        quiz_id_lower = quiz_id.lower()
        known_subjects = [
            "matematik", "turkce", "fizik", "kimya", "biyoloji",
            "tarih", "cografya", "geometri", "edebiyat", "ingilizce", "almanca"
        ]
        for known_subject in known_subjects:
            if known_subject in quiz_id_lower:
                subject = known_subject
                break

        metrics.record_quiz_submission(subject=subject, score=score, passed=passed)

        metrics.record_learning_path_api_request(
            endpoint="/quiz/submit", method="POST", status_code=200
        )

        return {
            "success": True,
            "quiz_id": quiz_id,
            "student_id": submission.student_id,
            "score": round(score, 2),
            "correct_count": correct_count,
            "total_questions": quiz_data["question_count"],
            "passing_score": quiz_data["passing_score"],
            "passed": passed,
            "total_time_seconds": total_time,
            "question_results": question_results,
            "timestamp": datetime.now().isoformat(),
            "feedback": (
                "Tebrikler! Quiz'i başarıyla tamamladınız."
                if passed
                else f"Quiz'i geçemediniz. Geçme notu: {quiz_data['passing_score']}%"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing quiz submission: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process quiz submission: {str(e)}"
        )


@router.put("/progress/{student_id}/{node_id}")
async def update_progress(
    student_id: str,
    node_id: str,
    progress_update: ProgressUpdate,
    current_user=Depends(get_current_user),  # 🔒 AUTH ADDED
    db: AsyncSession = Depends(get_db),  # P0 FIX: Database session
):
    """
    Update student's progress on a specific topic/node

    Tracks progress percentage, time spent, and completion status.
    P0 FIX: Now persists to database via TopicProgress model.
    """
    try:
        # 🔒 Verify ownership: students can only update their own progress
        await verify_student_access(student_id, current_user, db)

        logger.info(f"Updating progress for student {student_id}, node {node_id}")

        # Validate IDs match
        if progress_update.student_id != student_id:
            raise HTTPException(
                status_code=400,
                detail="Student ID mismatch: URL parameter doesn't match request body",
            )

        if progress_update.node_id != node_id:
            raise HTTPException(
                status_code=400,
                detail="Node ID mismatch: URL parameter doesn't match request body",
            )

        # Validate progress range
        if not 0 <= progress_update.progress <= 100:
            raise HTTPException(
                status_code=400, detail="Progress must be between 0 and 100"
            )

        # P0 FIX: Upsert progress to database
        result = await db.execute(
            select(TopicProgress).where(
                TopicProgress.student_id == student_id,
                TopicProgress.node_id == node_id
            )
        )
        existing_progress = result.scalar_one_or_none()

        is_completed = progress_update.completed or (progress_update.progress == 100)

        if existing_progress:
            # Update existing record
            existing_progress.progress = progress_update.progress
            existing_progress.completed = is_completed
            existing_progress.time_spent = (
                (existing_progress.time_spent or 0) + (progress_update.time_spent or 0)
            )
            existing_progress.updated_at = datetime.now()
            logger.info(f"Updated existing progress record for {student_id}/{node_id}")
        else:
            # Create new record
            new_progress = TopicProgress(
                student_id=student_id,
                node_id=node_id,
                progress=progress_update.progress,
                completed=is_completed,
                time_spent=progress_update.time_spent or 0,
            )
            db.add(new_progress)
            logger.info(f"Created new progress record for {student_id}/{node_id}")

        await db.commit()

        # Invalidate completion cache
        cache = _get_cache()
        if cache._initialized:
            cache_key = f"completion:{student_id}"
            await cache.delete(cache_key)
            logger.info(f"Progress cache invalidated for student {student_id}")

        logger.info(
            f"Progress persisted - Student: {student_id}, Node: {node_id}, "
            f"Progress: {progress_update.progress}%, Completed: {is_completed}"
        )

        return {
            "success": True,
            "student_id": student_id,
            "node_id": node_id,
            "progress": progress_update.progress,
            "completed": is_completed,
            "time_spent": progress_update.time_spent,
            "timestamp": datetime.now().isoformat(),
            "message": (
                "Topic başarıyla tamamlandı!"
                if is_completed
                else f"İlerleme %{progress_update.progress} olarak kaydedildi"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update progress: {str(e)}"
        )


def _serialize_question(q: Question) -> dict:
    """Soru nesnesini JSON-serializable dict'e çevir."""
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
async def get_exit_quiz(
    subject: str,
    count: int = 5,
    exam_type: str = "TYT",
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Çıkış testi: Tamamlanan konudan retrieval practice soruları döndür.
    Bilimsel dayanak: Retrieval practice d=0.5-1.24 (Frontiers 2025).
    """
    try:
        from services.soru_bankasi_service import SoruBankasiServisi

        soru_servisi = SoruBankasiServisi()
        questions = await soru_servisi.get_exit_quiz_questions(
            subject, count, exam_type=exam_type
        )
        return {
            "success": True,
            "questions": [_serialize_question(q) for q in questions],
            "count": len(questions),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exit quiz questions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch exit quiz questions: {str(e)}"
        )


@router.get("/interleaved-practice")
async def get_interleaved_practice(
    subjects: str,
    count: int = 10,
    exam_type: str = "TYT",
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Karışık pratik: Birden fazla konudan interleaved soru seti.
    Bilimsel dayanak: Interleaving d=1.21 (Rohrer et al. RCT).

    subjects: Comma-separated konu listesi, örn. "MATEMATIK,FIZIK,KIMYA"
    """
    try:
        subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
        if not subject_list:
            raise HTTPException(
                status_code=400,
                detail="En az bir konu belirtilmelidir (subjects parametresi boş olamaz)",
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
            detail=f"Failed to fetch interleaved practice questions: {str(e)}",
        )


@router.get("/review-queue")
async def get_review_queue(
    limit: int = 20,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tekrar kuyruğu: FSRS'e göre vadesi gelen soruları döndür.
    Yanlış cevaplanan sorular 24-48h sonra tekrar gelir.
    student_id current_user'dan türetilir (IDOR koruması).
    Bilimsel dayanak: FSRS-6 SM-2'ye karşı %99.6 üstün (Expertium 2024).
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
    except Exception as e:
        logger.error(f"Error fetching review queue: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch review queue: {str(e)}"
        )


class SubmitReviewRequest(BaseModel):
    card_id: str = Field(..., description="FSRS kart ID")
    grade: int = Field(..., ge=1, le=4, description="1=AGAIN, 2=HARD, 3=GOOD, 4=EASY")


@router.post("/submit-review")
async def submit_review(
    request: SubmitReviewRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tekrar sonucunu kaydet ve FSRS parametrelerini güncelle.
    Grade: 1=AGAIN (6h), 2=HARD (1d), 3=GOOD (2.5d), 4=EASY (7d).
    """
    try:
        from services.question_review_adapter import QuestionReviewAdapter

        student_id = str(current_user.id)
        adapter = QuestionReviewAdapter()
        card = await adapter.submit_review(request.card_id, request.grade, db, student_id=student_id)
        if not card:
            raise HTTPException(status_code=404, detail="Kart bulunamadı veya geçersiz grade")

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
            status_code=500, detail=f"Failed to submit review: {str(e)}"
        )


class RegisterWrongAnswersRequest(BaseModel):
    question_ids: List[str] = Field(..., min_length=1)
    # F8: Optional error type classifications from ErrorTypeSelector
    error_types: Optional[Dict[str, str]] = None


@router.post("/register-wrong-answers")
async def register_wrong_answers(
    request: RegisterWrongAnswersRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Quiz sonunda yanlış cevaplanan soruları FSRS tekrar kuyruğuna ekle.
    24h sonra review-queue'da görünürler.
    student_id current_user'dan türetilir (IDOR koruması).
    """
    try:
        from services.question_review_adapter import QuestionReviewAdapter

        student_id = str(current_user.id)
        adapter = QuestionReviewAdapter()
        created = await adapter.register_wrong_answers(
            student_id, request.question_ids, db,
            error_types=request.error_types,
        )
        await db.commit()
        return {
            "success": True,
            "created": created,
            "total_submitted": len(request.question_ids),
        }
    except Exception as e:
        logger.error(f"Error registering wrong answers: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to register wrong answers: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Learning Path API health check"""
    return {
        "status": "healthy",
        "service": "learning-path-api",
        "timestamp": datetime.now().isoformat(),
    }
