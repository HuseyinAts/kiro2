"""
Claude Diary Plugin - API Endpoints

Gunluk tutma ve reflection sistemi API endpoint'leri.
Tum REQ-1 ile REQ-8 arasindaki endpoint'ler.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from core.database import get_db
from core.auth_dependencies import AuthenticationDependency
from core.service_dependencies import get_diary_service
from models.user import User
from services.diary_service import DiaryService
from services.goal_service import GoalService
from services.insight_service import InsightService
from services.reflection_service import ReflectionService
from services.learning_journal_service import LearningJournalService
from services.emotional_service import EmotionalService
from services.peer_comparison_service import PeerComparisonService
from services.export_service import ExportService
from models.diary import GoalStatus, ExportFormat
from api.schemas.diary import (
    # Diary schemas
    DiaryEntryCreate,
    DiaryEntryResponse,
    DiaryEntryUpdate,
    # Insight schemas
    InsightResponse,
    # Reflection schemas
    ReflectionCreate,
    ReflectionResponse,
    ReflectionPromptsResponse,
    # Learning schemas
    LearningEntryCreate,
    LearningEntryResponse,
    LearningReviewResponse,
    # Emotional schemas
    EmotionalStateCreate,
    EmotionalStateResponse,
    MoodTrendResponse,
    # Goal schemas
    GoalCreate,
    GoalResponse,
    GoalUpdate,
    GoalProgressUpdate,
    GoalRiskResponse,
    # Peer comparison schemas
    PeerComparisonResponse,
    # Export schemas
    ExportRequest,
    ExportResponse,
    ShareLinkCreate,
    ShareLinkResponse,
    # Common schemas
    SuccessResponse,
)


# Authentication dependency - kimlik dogrulama zorunlu
get_current_user = AuthenticationDependency(required=True)

router = APIRouter(prefix="/api/v1/diary", tags=["Diary"])


# =============================================================================
# Helper Functions
# =============================================================================


# =============================================================================
# REQ-1: Daily Summary Endpoints
# =============================================================================


@router.get("/summary/today", response_model=Optional[DiaryEntryResponse])
async def get_today_summary(
    current_user: User = Depends(get_current_user),
    service: DiaryService = Depends(get_diary_service),
) -> Optional[DiaryEntryResponse]:
    """
    Bugunun gunluk ozetini getir.

    Returns:
        DiaryEntryResponse veya null (kayit yoksa)
    """
    user_id = current_user.id
    entry = await service.get_today_summary(user_id)

    if entry:
        return DiaryEntryResponse(
            id=entry.id,
            user_id=entry.user_id,
            date=entry.date,
            success_count=entry.success_count,
            failure_count=entry.failure_count,
            total_tasks=entry.total_tasks,
            total_duration_minutes=entry.total_duration_minutes,
            highlights=entry.highlights or [],
            learnings=entry.learnings or [],
            challenges=entry.challenges or [],
            markdown_content=entry.markdown_content,
            file_path=entry.file_path,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            success_rate=entry.success_rate,
        )
    return None


@router.get("/summary", response_model=Optional[DiaryEntryResponse])
async def get_summary_by_date(
    entry_date: date = Query(..., description="Kayit tarihi (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[DiaryEntryResponse]:
    """
    Belirli bir tarihin gunluk ozetini getir.

    Args:
        entry_date: Kayit tarihi

    Returns:
        DiaryEntryResponse veya null
    """
    user_id = current_user.id
    service = DiaryService(db)
    entry = await service.get_summary(user_id, entry_date)

    if entry:
        return DiaryEntryResponse(
            id=entry.id,
            user_id=entry.user_id,
            date=entry.date,
            success_count=entry.success_count,
            failure_count=entry.failure_count,
            total_tasks=entry.total_tasks,
            total_duration_minutes=entry.total_duration_minutes,
            highlights=entry.highlights or [],
            learnings=entry.learnings or [],
            challenges=entry.challenges or [],
            markdown_content=entry.markdown_content,
            file_path=entry.file_path,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            success_rate=entry.success_rate,
        )
    return None


@router.get("/summaries", response_model=List[DiaryEntryResponse])
async def get_summaries(
    start_date: Optional[date] = Query(None, description="Baslangic tarihi"),
    end_date: Optional[date] = Query(None, description="Bitis tarihi"),
    limit: int = Query(30, ge=1, le=100, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[DiaryEntryResponse]:
    """
    Gunluk ozetleri listele.

    Args:
        start_date: Baslangic tarihi (opsiyonel)
        end_date: Bitis tarihi (opsiyonel)
        limit: Maksimum kayit sayisi

    Returns:
        List[DiaryEntryResponse]
    """
    user_id = current_user.id
    service = DiaryService(db)
    entries = await service.get_summaries(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return [
        DiaryEntryResponse(
            id=e.id,
            user_id=e.user_id,
            date=e.date,
            success_count=e.success_count,
            failure_count=e.failure_count,
            total_tasks=e.total_tasks,
            total_duration_minutes=e.total_duration_minutes,
            highlights=e.highlights or [],
            learnings=e.learnings or [],
            challenges=e.challenges or [],
            markdown_content=e.markdown_content,
            file_path=e.file_path,
            created_at=e.created_at,
            updated_at=e.updated_at,
            success_rate=e.success_rate,
        )
        for e in entries
    ]


@router.post("/summary", response_model=DiaryEntryResponse)
async def create_summary(
    request: DiaryEntryCreate,
    persist_file: bool = Query(True, description="Dosyaya kaydet"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiaryEntryResponse:
    """
    Manuel gunluk ozeti olustur.

    Args:
        request: DiaryEntryCreate - Kayit verisi
        persist_file: Markdown dosyasi olustur

    Returns:
        DiaryEntryResponse
    """
    user_id = current_user.id
    service = DiaryService(db)

    # Mevcut kayit kontrolu
    existing = await service.get_summary(user_id, request.date)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"{request.date} tarihi icin kayit zaten mevcut"
        )

    entry = await service.generate_summary(
        user_id=user_id,
        entry_date=request.date,
        tasks=request.tasks,
        persist_file=persist_file,
    )

    return DiaryEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        date=entry.date,
        success_count=entry.success_count,
        failure_count=entry.failure_count,
        total_tasks=entry.total_tasks,
        total_duration_minutes=entry.total_duration_minutes,
        highlights=entry.highlights or [],
        learnings=entry.learnings or [],
        challenges=entry.challenges or [],
        markdown_content=entry.markdown_content,
        file_path=entry.file_path,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        success_rate=entry.success_rate,
    )


@router.put("/summary/{entry_id}", response_model=DiaryEntryResponse)
async def update_summary(
    entry_id: UUID,
    request: DiaryEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiaryEntryResponse:
    """
    Gunluk ozetini guncelle.

    Args:
        entry_id: Kayit ID
        request: DiaryEntryUpdate - Guncelleme verisi

    Returns:
        DiaryEntryResponse
    """
    service = DiaryService(db)
    entry = await service.update_summary(
        entry_id=entry_id,
        highlights=request.highlights,
        learnings=request.learnings,
        challenges=request.challenges,
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Kayit bulunamadi")

    return DiaryEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        date=entry.date,
        success_count=entry.success_count,
        failure_count=entry.failure_count,
        total_tasks=entry.total_tasks,
        total_duration_minutes=entry.total_duration_minutes,
        highlights=entry.highlights or [],
        learnings=entry.learnings or [],
        challenges=entry.challenges or [],
        markdown_content=entry.markdown_content,
        file_path=entry.file_path,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        success_rate=entry.success_rate,
    )


@router.delete("/summary/{entry_id}", response_model=SuccessResponse)
async def delete_summary(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Gunluk ozetini sil.

    Args:
        entry_id: Kayit ID

    Returns:
        SuccessResponse
    """
    service = DiaryService(db)
    deleted = await service.delete_summary(entry_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Kayit bulunamadi")

    return SuccessResponse(success=True, message="Kayit silindi")


# =============================================================================
# REQ-6: Goal Tracking Endpoints
# =============================================================================


@router.get("/goals", response_model=List[GoalResponse])
async def get_goals(
    status: Optional[GoalStatus] = Query(None, description="Durum filtresi"),
    category: Optional[str] = Query(None, description="Kategori filtresi"),
    limit: int = Query(50, ge=1, le=100, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GoalResponse]:
    """
    Hedefleri listele.

    Args:
        status: Durum filtresi (active, completed, at_risk, cancelled)
        category: Kategori filtresi
        limit: Maksimum kayit sayisi

    Returns:
        List[GoalResponse]
    """
    user_id = current_user.id
    service = GoalService(db)
    goals = await service.get_goals(
        user_id=user_id,
        status=status,
        category=category,
        limit=limit,
    )

    return [_goal_to_response(g) for g in goals]


@router.get("/goals/active", response_model=List[GoalResponse])
async def get_active_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GoalResponse]:
    """
    Aktif hedefleri listele.

    Returns:
        List[GoalResponse]
    """
    user_id = current_user.id
    service = GoalService(db)
    goals = await service.get_active_goals(user_id)
    return [_goal_to_response(g) for g in goals]


@router.get("/goals/at-risk", response_model=List[GoalResponse])
async def get_at_risk_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GoalResponse]:
    """
    Risk altindaki hedefleri listele.

    Returns:
        List[GoalResponse]
    """
    user_id = current_user.id
    service = GoalService(db)
    goals = await service.get_at_risk_goals(user_id)
    return [_goal_to_response(g) for g in goals]


@router.get("/goals/statistics")
async def get_goal_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hedef istatistiklerini getir.

    Returns:
        Dict - Istatistikler
    """
    user_id = current_user.id
    service = GoalService(db)
    return await service.get_goal_statistics(user_id)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalResponse:
    """
    Belirli bir hedefi getir.

    Args:
        goal_id: Hedef ID

    Returns:
        GoalResponse
    """
    service = GoalService(db)
    goal = await service.get_goal(goal_id)

    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return _goal_to_response(goal)


@router.post("/goals", response_model=GoalResponse)
async def create_goal(
    request: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalResponse:
    """
    Yeni hedef olustur.

    Args:
        request: GoalCreate - Hedef verisi

    Returns:
        GoalResponse
    """
    user_id = current_user.id
    service = GoalService(db)

    # SMART validasyonu
    smart_result = service.validate_smart(request)
    if not smart_result["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "SMART kriterleri karsilanmiyor",
                "missing": smart_result["missing"],
                "warnings": smart_result["warnings"],
            }
        )

    goal = await service.create_goal(user_id, request)
    return _goal_to_response(goal)


@router.post("/goals/validate-smart")
async def validate_smart_criteria(
    request: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hedef icin SMART kriterlerini dogrula.

    Args:
        request: GoalCreate - Hedef verisi

    Returns:
        Dict - SMART validasyon sonucu
    """
    service = GoalService(db)
    return service.validate_smart(request)


@router.put("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    request: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalResponse:
    """
    Hedef guncelle.

    Args:
        goal_id: Hedef ID
        request: GoalUpdate - Guncelleme verisi

    Returns:
        GoalResponse
    """
    service = GoalService(db)
    goal = await service.update_goal(goal_id, request)

    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return _goal_to_response(goal)


@router.patch("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: UUID,
    request: GoalProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hedef ilerlemesini guncelle.

    Args:
        goal_id: Hedef ID
        request: GoalProgressUpdate - Ilerleme verisi

    Returns:
        Dict - Guncelleme sonucu (milestone celebrations dahil)
    """
    service = GoalService(db)
    result = await service.update_progress(goal_id, request)

    if not result:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return {
        "success": True,
        "goal": _goal_to_response(result["goal"]),
        "old_progress": result["old_progress"],
        "new_progress": result["new_progress"],
        "celebrations": result["celebrations"],
        "risk": {
            "is_at_risk": result["risk"].is_at_risk,
            "risk_level": result["risk"].risk_level,
            "risk_factors": result["risk"].risk_factors,
            "recommendations": result["risk"].recommendations,
        },
    }


@router.get("/goals/{goal_id}/risk", response_model=GoalRiskResponse)
async def get_goal_risk(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalRiskResponse:
    """
    Hedef risk analizini getir.

    Args:
        goal_id: Hedef ID

    Returns:
        GoalRiskResponse
    """
    service = GoalService(db)
    goal = await service.get_goal(goal_id)

    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return service.detect_risk(goal)


@router.post("/goals/{goal_id}/adjust", response_model=GoalResponse)
async def adjust_goal(
    goal_id: UUID,
    reason: str = Query(..., min_length=5, description="Ayarlama nedeni"),
    new_target_value: Optional[float] = Query(None, description="Yeni hedef degeri"),
    new_target_date: Optional[datetime] = Query(None, description="Yeni hedef tarihi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalResponse:
    """
    Hedefi ayarla (REQ-6.5).

    Args:
        goal_id: Hedef ID
        reason: Ayarlama nedeni
        new_target_value: Yeni hedef degeri (opsiyonel)
        new_target_date: Yeni hedef tarihi (opsiyonel)

    Returns:
        GoalResponse
    """
    service = GoalService(db)
    goal = await service.adjust_goal(
        goal_id=goal_id,
        reason=reason,
        new_target_value=new_target_value,
        new_target_date=new_target_date,
    )

    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return _goal_to_response(goal)


@router.post("/goals/{goal_id}/retrospective", response_model=GoalResponse)
async def create_goal_retrospective(
    goal_id: UUID,
    lessons_learned: List[str] = Query(default=[], description="Ogrenilen dersler"),
    success_factors: List[str] = Query(default=[], description="Basari faktorleri"),
    challenges_faced: List[str] = Query(default=[], description="Karsilasilan zorluklar"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalResponse:
    """
    Hedef retrospektifi olustur (REQ-6.6).

    Args:
        goal_id: Hedef ID
        lessons_learned: Ogrenilen dersler
        success_factors: Basari faktorleri
        challenges_faced: Karsilasilan zorluklar

    Returns:
        GoalResponse
    """
    service = GoalService(db)
    goal = await service.create_retrospective(
        goal_id=goal_id,
        lessons_learned=lessons_learned,
        success_factors=success_factors,
        challenges_faced=challenges_faced,
    )

    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return _goal_to_response(goal)


@router.delete("/goals/{goal_id}", response_model=SuccessResponse)
async def delete_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Hedef sil.

    Args:
        goal_id: Hedef ID

    Returns:
        SuccessResponse
    """
    service = GoalService(db)
    deleted = await service.delete_goal(goal_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Hedef bulunamadi")

    return SuccessResponse(success=True, message="Hedef silindi")


# =============================================================================
# Helper Functions
# =============================================================================


def _goal_to_response(goal) -> GoalResponse:
    """Goal model'ini GoalResponse'a donustur"""
    from api.schemas.diary import MilestoneResponse

    milestones = []
    for m in (goal.milestones or []):
        milestones.append(MilestoneResponse(
            percentage=m.get("percentage", 0),
            title=m.get("title", ""),
            achieved=m.get("achieved", False),
            achieved_at=m.get("achieved_at"),
        ))

    return GoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        title=goal.title,
        description=goal.description,
        progress=goal.progress,
        current_value=goal.current_value,
        target_value=goal.target_value,
        unit=goal.unit,
        status=goal.status,
        milestones=milestones,
        is_at_risk=goal.is_at_risk,
        risk_factors=goal.risk_factors or [],
        velocity=goal.velocity,
        predicted_completion=goal.predicted_completion,
        start_date=goal.start_date,
        target_date=goal.target_date,
        completed_at=goal.completed_at,
        category=goal.category,
        priority=goal.priority,
        days_remaining=goal.days_remaining if hasattr(goal, 'days_remaining') else 0,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


# =============================================================================
# REQ-2: Insight Extraction Endpoints
# =============================================================================


@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    category: Optional[str] = Query(None, description="Kategori filtresi"),
    min_confidence: float = Query(0.8, ge=0.0, le=1.0, description="Min guven skoru"),
    limit: int = Query(50, ge=1, le=100, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[InsightResponse]:
    """
    Kullanici insightlarini listele.

    Args:
        category: Kategori filtresi (technical, process, communication)
        min_confidence: Minimum guven skoru
        limit: Maksimum kayit sayisi

    Returns:
        List[InsightResponse]
    """
    user_id = current_user.id
    service = InsightService(db)
    insights = await service.get_insights(
        user_id=user_id,
        category=category,
        min_confidence=min_confidence,
        limit=limit,
    )
    return [_insight_to_response(i) for i in insights]


@router.post("/insights/analyze", response_model=List[InsightResponse])
async def analyze_entries_for_insights(
    start_date: Optional[date] = Query(None, description="Baslangic tarihi"),
    end_date: Optional[date] = Query(None, description="Bitis tarihi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[InsightResponse]:
    """
    Gunluk kayitlarini analiz edip yeni insightlar olustur.

    Args:
        start_date: Baslangic tarihi
        end_date: Bitis tarihi

    Returns:
        List[InsightResponse] - Yeni olusturulan insightlar
    """
    user_id = current_user.id
    service = InsightService(db)
    insights = await service.analyze_and_generate_insights(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    return [_insight_to_response(i) for i in insights]


@router.get("/insights/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InsightResponse:
    """
    Belirli bir insighti getir.

    Args:
        insight_id: Insight ID

    Returns:
        InsightResponse
    """
    service = InsightService(db)
    insight = await service.get_insight(insight_id)

    if not insight:
        raise HTTPException(status_code=404, detail="Insight bulunamadi")

    return _insight_to_response(insight)


@router.delete("/insights/{insight_id}", response_model=SuccessResponse)
async def delete_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Insight sil.

    Args:
        insight_id: Insight ID

    Returns:
        SuccessResponse
    """
    service = InsightService(db)
    deleted = await service.delete_insight(insight_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Insight bulunamadi")

    return SuccessResponse(success=True, message="Insight silindi")


def _insight_to_response(insight) -> InsightResponse:
    """Insight model'ini InsightResponse'a donustur"""
    return InsightResponse(
        id=insight.id,
        diary_entry_id=insight.diary_entry_id,
        user_id=insight.user_id,
        category=insight.category,
        pattern=insight.pattern,
        confidence=insight.confidence,
        evidence_count=insight.evidence_count,
        recommendation=insight.recommendation,
        priority=insight.priority,
        root_cause=insight.root_cause,
        correlation=insight.correlation,
        created_at=insight.created_at,
    )


# =============================================================================
# REQ-3: Reflection Prompts Endpoints
# =============================================================================


@router.get("/reflection/prompts", response_model=ReflectionPromptsResponse)
async def get_reflection_prompts(
    diary_entry_id: Optional[UUID] = Query(None, description="Gunluk kaydi ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReflectionPromptsResponse:
    """
    Yansitma sorularini getir.

    Args:
        diary_entry_id: Baglamsal sorular icin gunluk kaydi ID

    Returns:
        ReflectionPromptsResponse
    """
    user_id = current_user.id
    service = ReflectionService(db)

    prompts = await service.get_prompts(
        user_id=user_id,
        diary_entry_id=diary_entry_id,
    )

    return ReflectionPromptsResponse(
        prompts=prompts["prompts"],
        context_hints=prompts.get("context_hints"),
    )


@router.post("/reflection", response_model=ReflectionResponse)
async def create_reflection(
    request: ReflectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReflectionResponse:
    """
    Yeni yansitma olustur.

    Args:
        request: ReflectionCreate - Yansitma verisi

    Returns:
        ReflectionResponse
    """
    user_id = current_user.id
    service = ReflectionService(db)

    reflection = await service.create_reflection(user_id, request)
    return _reflection_to_response(reflection)


@router.get("/reflections", response_model=List[ReflectionResponse])
async def get_reflections(
    start_date: Optional[date] = Query(None, description="Baslangic tarihi"),
    end_date: Optional[date] = Query(None, description="Bitis tarihi"),
    depth: Optional[str] = Query(None, description="Derinlik filtresi"),
    limit: int = Query(30, ge=1, le=100, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReflectionResponse]:
    """
    Yansitmalari listele.

    Args:
        start_date: Baslangic tarihi
        end_date: Bitis tarihi
        depth: Derinlik filtresi (surface, moderate, deep)
        limit: Maksimum kayit sayisi

    Returns:
        List[ReflectionResponse]
    """
    user_id = current_user.id
    service = ReflectionService(db)

    reflections = await service.get_reflections(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        depth=depth,
        limit=limit,
    )

    return [_reflection_to_response(r) for r in reflections]


@router.get("/reflection/{reflection_id}", response_model=ReflectionResponse)
async def get_reflection(
    reflection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReflectionResponse:
    """
    Belirli bir yansitmayi getir.

    Args:
        reflection_id: Yansitma ID

    Returns:
        ReflectionResponse
    """
    service = ReflectionService(db)
    reflection = await service.get_reflection(reflection_id)

    if not reflection:
        raise HTTPException(status_code=404, detail="Yansitma bulunamadi")

    return _reflection_to_response(reflection)


def _reflection_to_response(reflection) -> ReflectionResponse:
    """Reflection model'ini ReflectionResponse'a donustur"""
    return ReflectionResponse(
        id=reflection.id,
        diary_entry_id=reflection.diary_entry_id,
        user_id=reflection.user_id,
        what_went_well=reflection.what_went_well,
        what_could_improve=reflection.what_could_improve,
        what_did_i_learn=reflection.what_did_i_learn,
        what_will_i_do_differently=reflection.what_will_i_do_differently,
        additional_notes=reflection.additional_notes,
        depth=reflection.depth,
        depth_score=reflection.depth_score,
        extracted_learnings=reflection.extracted_learnings or [],
        action_items=reflection.action_items or [],
        created_at=reflection.created_at,
        updated_at=reflection.updated_at,
    )


# =============================================================================
# REQ-4: Learning Journal Endpoints
# =============================================================================


@router.post("/learning", response_model=LearningEntryResponse)
async def create_learning_entry(
    request: LearningEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningEntryResponse:
    """
    Yeni ogrenme kaydi olustur.

    Args:
        request: LearningEntryCreate - Ogrenme verisi

    Returns:
        LearningEntryResponse
    """
    user_id = current_user.id
    service = LearningJournalService(db)

    entry = await service.create_entry(user_id, request)
    return _learning_to_response(entry)


@router.get("/learning", response_model=List[LearningEntryResponse])
async def get_learning_entries(
    domain: Optional[str] = Query(None, description="Alan filtresi"),
    tags: Optional[List[str]] = Query(None, description="Etiket filtresi"),
    limit: int = Query(50, ge=1, le=100, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[LearningEntryResponse]:
    """
    Ogrenme kayitlarini listele.

    Args:
        domain: Alan filtresi
        tags: Etiket filtresi
        limit: Maksimum kayit sayisi

    Returns:
        List[LearningEntryResponse]
    """
    user_id = current_user.id
    service = LearningJournalService(db)

    entries = await service.get_entries(
        user_id=user_id,
        domain=domain,
        tags=tags,
        limit=limit,
    )

    return [_learning_to_response(e) for e in entries]


@router.get("/learning/review", response_model=List[LearningEntryResponse])
async def get_due_reviews(
    limit: int = Query(10, ge=1, le=50, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[LearningEntryResponse]:
    """
    Tekrar edilmesi gereken ogrenme kayitlarini getir.

    Args:
        limit: Maksimum kayit sayisi

    Returns:
        List[LearningEntryResponse]
    """
    user_id = current_user.id
    service = LearningJournalService(db)

    entries = await service.get_due_reviews(user_id, limit=limit)
    return [_learning_to_response(e) for e in entries]


@router.post("/learning/{entry_id}/review", response_model=LearningReviewResponse)
async def record_review(
    entry_id: UUID,
    remembered: bool = Query(..., description="Hatirlandi mi?"),
    quality: int = Query(..., ge=1, le=5, description="Kalite (1-5)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningReviewResponse:
    """
    Ogrenme tekrari kaydet (FSRS benzeri).

    Args:
        entry_id: Kayit ID
        remembered: Hatirlandi mi?
        quality: Kalite degerlendirmesi (1-5)

    Returns:
        LearningReviewResponse
    """
    service = LearningJournalService(db)

    result = await service.record_review(
        entry_id=entry_id,
        remembered=remembered,
        quality=quality,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Ogrenme kaydi bulunamadi")

    return LearningReviewResponse(
        entry_id=result["entry_id"],
        next_review=result["next_review"],
        new_interval_days=result["new_interval_days"],
        retention_score=result["retention_score"],
        mastery_level=result["mastery_level"],
    )


@router.get("/learning/graph")
async def get_knowledge_graph(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Bilgi grafini getir.

    Returns:
        Dict - Nodes ve edges ile bilgi grafi
    """
    user_id = current_user.id
    service = LearningJournalService(db)

    graph = await service.get_knowledge_graph(user_id)
    return graph


@router.get("/learning/gaps")
async def get_knowledge_gaps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Bilgi bosluklerini tespit et.

    Returns:
        List[Dict] - Tespit edilen bosluklar
    """
    user_id = current_user.id
    service = LearningJournalService(db)

    gaps = await service.detect_gaps(user_id)
    return gaps


@router.get("/learning/{entry_id}", response_model=LearningEntryResponse)
async def get_learning_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearningEntryResponse:
    """
    Belirli bir ogrenme kaydini getir.

    Args:
        entry_id: Kayit ID

    Returns:
        LearningEntryResponse
    """
    service = LearningJournalService(db)
    entry = await service.get_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Ogrenme kaydi bulunamadi")

    return _learning_to_response(entry)


@router.post("/learning/{entry_id}/link")
async def link_concepts(
    entry_id: UUID,
    concepts: List[str] = Query(..., description="Ilgili kavramlar"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Ogrenme kaydina kavram baglantilari ekle.

    Args:
        entry_id: Kayit ID
        concepts: Baglanti kurulacak kavramlar

    Returns:
        SuccessResponse
    """
    service = LearningJournalService(db)

    result = await service.link_concepts(entry_id, concepts)

    if not result:
        raise HTTPException(status_code=404, detail="Ogrenme kaydi bulunamadi")

    return SuccessResponse(success=True, message=f"{len(concepts)} kavram baglandi")


def _learning_to_response(entry) -> LearningEntryResponse:
    """LearningEntry model'ini LearningEntryResponse'a donustur"""
    return LearningEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=entry.title,
        content=entry.content,
        summary=entry.summary,
        tags=entry.tags or [],
        domain=entry.domain,
        skill_type=entry.skill_type,
        related_concepts=entry.related_concepts or [],
        next_review=entry.next_review,
        review_count=entry.review_count,
        retention_score=entry.retention_score,
        mastery_level=entry.mastery_level,
        importance=entry.importance,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


# =============================================================================
# REQ-5: Emotional State Tracking Endpoints
# =============================================================================


@router.post("/emotional", response_model=EmotionalStateResponse)
async def track_emotional_state(
    request: EmotionalStateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmotionalStateResponse:
    """
    Duygusal durum kaydet.

    Args:
        request: EmotionalStateCreate - Duygusal durum verisi

    Returns:
        EmotionalStateResponse
    """
    user_id = current_user.id
    service = EmotionalService(db)

    state = await service.track_state(user_id, request)
    return _emotional_to_response(state)


@router.get("/emotional", response_model=List[EmotionalStateResponse])
async def get_emotional_states(
    start_date: Optional[date] = Query(None, description="Baslangic tarihi"),
    end_date: Optional[date] = Query(None, description="Bitis tarihi"),
    limit: int = Query(50, ge=1, le=100, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[EmotionalStateResponse]:
    """
    Duygusal durum kayitlarini listele.

    Args:
        start_date: Baslangic tarihi
        end_date: Bitis tarihi
        limit: Maksimum kayit sayisi

    Returns:
        List[EmotionalStateResponse]
    """
    user_id = current_user.id
    service = EmotionalService(db)

    states = await service.get_states(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return [_emotional_to_response(s) for s in states]


@router.get("/emotional/trend", response_model=MoodTrendResponse)
async def get_mood_trend(
    days: int = Query(30, ge=7, le=90, description="Kac gunluk trend"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MoodTrendResponse:
    """
    Ruh hali trendini getir.

    Args:
        days: Kac gunluk trend

    Returns:
        MoodTrendResponse
    """
    user_id = current_user.id
    service = EmotionalService(db)

    trend = await service.get_mood_trend(user_id, days=days)
    return MoodTrendResponse(
        period_start=trend["period_start"],
        period_end=trend["period_end"],
        data_points=trend["data_points"],
        average_confidence=trend["average_confidence"],
        flow_state_percentage=trend["flow_state_percentage"],
        frustration_events=trend["frustration_events"],
    )


@router.get("/emotional/chart")
async def get_mood_chart(
    days: int = Query(30, ge=7, le=90, description="Kac gunluk chart"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Ruh hali grafigini PNG olarak getir.

    Args:
        days: Kac gunluk grafik

    Returns:
        StreamingResponse (PNG)
    """
    user_id = current_user.id
    service = EmotionalService(db)

    chart_bytes = await service.generate_mood_chart(user_id, days=days)

    return StreamingResponse(
        io.BytesIO(chart_bytes),
        media_type="image/png",
        headers={"Content-Disposition": "inline; filename=mood_chart.png"},
    )


@router.get("/emotional/frustration-alerts")
async def get_frustration_alerts(
    threshold: float = Query(0.7, ge=0.5, le=1.0, description="Esik degeri"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Hayal kirikligi uyarilarini getir.

    Args:
        threshold: Esik degeri (0.5-1.0)

    Returns:
        List[Dict] - Uyari kayitlari
    """
    user_id = current_user.id
    service = EmotionalService(db)

    alerts = await service.get_frustration_alerts(user_id, threshold=threshold)
    return alerts


def _emotional_to_response(state) -> EmotionalStateResponse:
    """EmotionalState model'ini EmotionalStateResponse'a donustur"""
    return EmotionalStateResponse(
        id=state.id,
        user_id=state.user_id,
        timestamp=state.timestamp,
        confidence_level=state.confidence_level,
        frustration_score=state.frustration_score,
        retry_count=state.retry_count,
        error_count=state.error_count,
        flow_state=state.flow_state,
        productivity_score=state.productivity_score,
        tasks_completed=state.tasks_completed,
        task_type=state.task_type,
        trigger_factors=state.trigger_factors or {},
        self_awareness_score=state.self_awareness_score,
    )


# =============================================================================
# REQ-7: Peer Comparison Endpoints
# =============================================================================


@router.get("/peer-comparison", response_model=PeerComparisonResponse)
async def get_peer_comparison(
    days: int = Query(30, ge=7, le=90, description="Kac gunluk karsilastirma"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PeerComparisonResponse:
    """
    Akran karsilastirmasi yap (differential privacy ile).

    Args:
        days: Kac gunluk karsilastirma

    Returns:
        PeerComparisonResponse
    """
    user_id = current_user.id
    service = PeerComparisonService(db)

    comparison = await service.compare_performance(user_id, days=days)

    return PeerComparisonResponse(
        id=comparison.id,
        user_id=comparison.user_id,
        period_start=comparison.period_start,
        period_end=comparison.period_end,
        success_rate_percentile=comparison.success_rate_percentile,
        speed_percentile=comparison.speed_percentile,
        quality_percentile=comparison.quality_percentile,
        overall_percentile=comparison.overall_percentile,
        strengths=comparison.strengths or [],
        improvements=comparison.improvements or [],
        best_practices=comparison.best_practices or [],
        peer_group_size=comparison.peer_group_size,
        created_at=comparison.created_at,
    )


@router.get("/peer-comparison/history", response_model=List[PeerComparisonResponse])
async def get_peer_comparison_history(
    limit: int = Query(10, ge=1, le=50, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PeerComparisonResponse]:
    """
    Akran karsilastirma gecmisini getir.

    Args:
        limit: Maksimum kayit sayisi

    Returns:
        List[PeerComparisonResponse]
    """
    user_id = current_user.id
    service = PeerComparisonService(db)

    comparisons = await service.get_comparison_history(user_id, limit=limit)

    return [
        PeerComparisonResponse(
            id=c.id,
            user_id=c.user_id,
            period_start=c.period_start,
            period_end=c.period_end,
            success_rate_percentile=c.success_rate_percentile,
            speed_percentile=c.speed_percentile,
            quality_percentile=c.quality_percentile,
            overall_percentile=c.overall_percentile,
            strengths=c.strengths or [],
            improvements=c.improvements or [],
            best_practices=c.best_practices or [],
            peer_group_size=c.peer_group_size,
            created_at=c.created_at,
        )
        for c in comparisons
    ]


# =============================================================================
# REQ-8: Export and Sharing Endpoints
# =============================================================================


@router.post("/export", response_model=ExportResponse)
async def create_export(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    """
    Gunluk verilerini export et.

    Args:
        request: ExportRequest - Export parametreleri

    Returns:
        ExportResponse
    """
    user_id = current_user.id
    service = ExportService(db)

    export = await service.export(user_id, request)

    return ExportResponse(
        id=export.id,
        user_id=export.user_id,
        format=export.format,
        date_from=export.date_from,
        date_to=export.date_to,
        file_path=export.file_path,
        file_size=export.file_size,
        privacy_filter_applied=export.privacy_filter_applied,
        created_at=export.created_at,
    )


@router.get("/export/{export_id}/download")
async def download_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export dosyasini indir.

    Args:
        export_id: Export ID

    Returns:
        StreamingResponse
    """
    service = ExportService(db)

    export_data = await service.get_export(export_id)

    if not export_data:
        raise HTTPException(status_code=404, detail="Export bulunamadi")

    content = await service.get_export_content(export_id)

    if not content:
        raise HTTPException(status_code=404, detail="Export icerigi bulunamadi")

    # Format'a gore media type belirle
    format_type = export_data.format
    if format_type == ExportFormat.PDF:
        media_type = "application/pdf"
        filename = f"diary_export_{export_id}.pdf"
    elif format_type == ExportFormat.JSON:
        media_type = "application/json"
        filename = f"diary_export_{export_id}.json"
    else:
        media_type = "text/markdown"
        filename = f"diary_export_{export_id}.md"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/export/share", response_model=ShareLinkResponse)
async def create_share_link(
    request: ShareLinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """
    Paylasim linki olustur.

    Args:
        request: ShareLinkCreate - Paylasim parametreleri

    Returns:
        ShareLinkResponse
    """
    user_id = current_user.id
    service = ExportService(db)

    share = await service.create_share_link(
        user_id=user_id,
        export_id=request.export_id,
        expires_in_days=request.expires_in_days,
    )

    if not share:
        raise HTTPException(status_code=404, detail="Export bulunamadi")

    return ShareLinkResponse(
        export_id=share["export_id"],
        share_token=share["share_token"],
        share_url=share["share_url"],
        expires_at=share["expires_at"],
    )


@router.get("/export/shared/{share_token}")
async def get_shared_export(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Paylasilan exportu getir.

    Args:
        share_token: Paylasim tokeni

    Returns:
        StreamingResponse
    """
    service = ExportService(db)

    result = await service.get_shared_export(share_token)

    if not result:
        raise HTTPException(status_code=404, detail="Paylasim bulunamadi veya suresi dolmus")

    content = result["content"]
    export_data = result["export"]

    # Format'a gore media type belirle
    format_type = export_data.format
    if format_type == ExportFormat.PDF:
        media_type = "application/pdf"
    elif format_type == ExportFormat.JSON:
        media_type = "application/json"
    else:
        media_type = "text/markdown"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
    )


@router.get("/exports", response_model=List[ExportResponse])
async def get_exports(
    limit: int = Query(20, ge=1, le=50, description="Maksimum kayit sayisi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ExportResponse]:
    """
    Export gecmisini listele.

    Args:
        limit: Maksimum kayit sayisi

    Returns:
        List[ExportResponse]
    """
    user_id = current_user.id
    service = ExportService(db)

    exports = await service.get_exports(user_id, limit=limit)

    return [
        ExportResponse(
            id=e.id,
            user_id=e.user_id,
            format=e.format,
            date_from=e.date_from,
            date_to=e.date_to,
            file_path=e.file_path,
            file_size=e.file_size,
            privacy_filter_applied=e.privacy_filter_applied,
            created_at=e.created_at,
        )
        for e in exports
    ]


@router.post("/backup/encrypted")
async def create_encrypted_backup(
    password: str = Query(..., min_length=8, description="Sifreleme sifresi"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Sifrelenmis yedek olustur.

    Args:
        password: Sifreleme sifresi (min 8 karakter)

    Returns:
        Dict - Yedek bilgileri
    """
    user_id = current_user.id
    service = ExportService(db)

    backup = await service.create_encrypted_backup(user_id, password)

    return {
        "success": True,
        "backup_id": str(backup["backup_id"]),
        "file_size": backup["file_size"],
        "created_at": backup["created_at"].isoformat(),
        "encryption": "AES-256-GCM",
        "warning": "Sifreyi kaybederseniz yedege erisemezsiniz!",
    }
