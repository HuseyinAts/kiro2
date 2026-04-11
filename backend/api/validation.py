"""
Content Validation API
Uzman içerik doğrulama ve onay API'leri
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.dependencies import (
    AuthenticatedUser,
    get_current_admin_user,
    get_current_user,
)
from core.expert_content_validation import (
    ContentType,
    ExpertRole,
    expert_validation_system,
)
from core.structured_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])


# ==================== REQUEST/RESPONSE MODELS ====================


class ContentSubmissionRequest(BaseModel):
    """İçerik gönderme talebi"""

    content_id: str
    content_type: str  # "question", "exam", "topic", etc.
    content_data: dict[str, Any]
    submitter_id: str
    submitter_name: str

    # Optional metadata
    grade_level: str | None = None
    subject: str | None = None
    topic: str | None = None
    learning_outcomes: list[str] | None = None
    exam_type: str | None = None
    difficulty_level: str | None = None
    priority: int = 5


class ExpertFeedbackSubmission(BaseModel):
    """Uzman geri bildirimi"""

    expert_id: str
    expert_name: str
    expert_role: str
    feedbacks: list[dict[str, Any]]


class ExpertRegistrationRequest(BaseModel):
    """Uzman kaydı talebi"""

    expert_id: str
    expert_roles: list[str]


class ValidationStatusResponse(BaseModel):
    """Doğrulama durumu yanıtı"""

    request_id: str
    status: str
    overall_score: float | None
    completion_percentage: int
    feedbacks_count: int
    required_experts: int
    completed_at: datetime | None


# ==================== ENDPOINTS ====================


@router.post("/submit")
async def submit_content_for_validation(
    submission: ContentSubmissionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    İçeriği uzman doğrulamasına gönder

    - Soru, sınav, konu gibi içeriklerin doğrulanması
    - MEB müfredat uyumluluğu kontrolü
    - ÖSYM standartları doğrulaması
    - Otomatik uzman ataması
    """

    # Content type'ı enum'a çevir
    try:
        content_type = ContentType(submission.content_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content_type: {submission.content_type}",
        )

    try:
        # Validation request oluştur
        request = await expert_validation_system.submit_content_for_validation(
            content_id=submission.content_id,
            content_type=content_type,
            content_data=submission.content_data,
            submitter_id=submission.submitter_id,
            submitter_name=submission.submitter_name,
            grade_level=submission.grade_level,
            subject=submission.subject,
            topic=submission.topic,
            learning_outcomes=submission.learning_outcomes or [],
            exam_type=submission.exam_type,
            difficulty_level=submission.difficulty_level,
            priority=submission.priority,
        )

        logger.info(
            "content_submitted_for_validation",
            request_id=request.request_id,
            content_id=submission.content_id,
            content_type=content_type.value,
            submitter_id=submission.submitter_id,
        )

        return {
            "success": True,
            "request_id": request.request_id,
            "status": request.status.value,
            "assigned_experts": len(request.assigned_experts),
            "review_deadline": request.review_deadline.isoformat()
            if request.review_deadline
            else None,
            "message": "İçerik başarıyla doğrulamaya gönderildi",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "content_submission_failed", error=str(e), content_id=submission.content_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/feedback/{request_id}")
async def submit_expert_feedback(
    request_id: str,
    feedback: ExpertFeedbackSubmission,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Uzman geri bildirimi gönder

    - Atanan uzmanlar tarafından geri bildirim
    - Kriter bazlı değerlendirme
    - Öneri ve düzeltme notları
    """

    try:
        # Expert role'ü enum'a çevir
        try:
            expert_role = ExpertRole(feedback.expert_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid expert_role: {feedback.expert_role}",
            )

        # Feedback gönder
        success = await expert_validation_system.submit_expert_feedback(
            request_id=request_id,
            expert_id=feedback.expert_id,
            expert_name=feedback.expert_name,
            expert_role=expert_role,
            feedbacks=feedback.feedbacks,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation request not found: {request_id}",
            )

        logger.info(
            "expert_feedback_submitted",
            request_id=request_id,
            expert_id=feedback.expert_id,
            feedback_count=len(feedback.feedbacks),
        )

        return {
            "success": True,
            "request_id": request_id,
            "message": "Uzman geri bildirimi başarıyla kaydedildi",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "expert_feedback_submission_failed", error=str(e), request_id=request_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/status/{request_id}")
async def get_validation_status(
    request_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ValidationStatusResponse:
    """
    Doğrulama durumunu getir

    - Mevcut durum bilgisi
    - Geri bildirim sayısı
    - Tamamlanma yüzdesi
    - Genel skor
    """

    try:
        request = expert_validation_system.get_validation_request(request_id)

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation request not found: {request_id}",
            )

        # Tamamlanma yüzdesi hesapla
        required_experts = len(request.required_expert_roles)
        feedbacks_count = len(request.feedbacks)
        completion_percentage = (
            int((feedbacks_count / required_experts) * 100)
            if required_experts > 0
            else 0
        )

        return ValidationStatusResponse(
            request_id=request.request_id,
            status=request.status.value,
            overall_score=request.overall_score,
            completion_percentage=completion_percentage,
            feedbacks_count=feedbacks_count,
            required_experts=required_experts,
            completed_at=request.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_validation_status_failed", error=str(e), request_id=request_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/request/{request_id}")
async def get_validation_request(
    request_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Tam doğrulama talebi bilgisini getir

    - İçerik detayları
    - Atanan uzmanlar
    - Tüm geri bildirimler
    - Revizyon notları
    """

    try:
        request = expert_validation_system.get_validation_request(request_id)

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation request not found: {request_id}",
            )

        return {
            "request_id": request.request_id,
            "content_id": request.content_id,
            "content_type": request.content_type.value,
            "status": request.status.value,
            "submitter": {"id": request.submitter_id, "name": request.submitter_name},
            "metadata": {
                "grade_level": request.grade_level,
                "subject": request.subject,
                "topic": request.topic,
                "exam_type": request.exam_type,
                "difficulty_level": request.difficulty_level,
            },
            "workflow": {
                "required_expert_roles": [
                    role.value for role in request.required_expert_roles
                ],
                "assigned_experts": request.assigned_experts,
                "feedbacks_count": len(request.feedbacks),
            },
            "timeline": {
                "submitted_at": request.submitted_at.isoformat(),
                "review_deadline": request.review_deadline.isoformat()
                if request.review_deadline
                else None,
                "completed_at": request.completed_at.isoformat()
                if request.completed_at
                else None,
            },
            "results": {
                "overall_score": request.overall_score,
                "final_decision": request.final_decision,
                "revision_notes": request.revision_notes,
            },
            "feedbacks": [
                {
                    "feedback_id": fb.feedback_id,
                    "expert_name": fb.expert_name,
                    "expert_role": fb.expert_role.value,
                    "passed": fb.passed,
                    "score": fb.score,
                    "comment": fb.comment,
                    "suggestions": fb.suggestions,
                    "created_at": fb.created_at.isoformat(),
                }
                for fb in request.feedbacks
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_validation_request_failed", error=str(e), request_id=request_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/compliance/{report_id}")
async def get_compliance_report(
    report_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Uyumluluk raporunu getir

    - MEB müfredat uyumluluğu
    - ÖSYM standartları uygunluğu
    - Pedagojik değerlendirme
    - Kalite metrikleri
    """

    try:
        report = expert_validation_system.get_compliance_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compliance report not found: {report_id}",
            )

        return {
            "report_id": report.report_id,
            "content_id": report.content_id,
            "content_type": report.content_type.value,
            "meb_compliance": {
                "level": report.meb_compliance.value,
                "score": report.meb_score,
                "standards_matched": report.meb_standards_matched,
                "issues": report.meb_issues,
            },
            "osym_compliance": {
                "level": report.osym_compliance.value,
                "score": report.osym_score,
                "standards_matched": report.osym_standards_matched,
                "issues": report.osym_issues,
            },
            "pedagogy": {
                "score": report.pedagogy_score,
                "notes": report.pedagogy_notes,
            },
            "quality": {"score": report.quality_score, "issues": report.quality_issues},
            "overall": {
                "compliance": report.overall_compliance.value,
                "score": report.overall_score,
                "recommendations": report.recommendations,
            },
            "generated_at": report.generated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_compliance_report_failed", error=str(e), report_id=report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/experts/register")
async def register_expert(
    request: ExpertRegistrationRequest,
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Uzman kaydı yap

    - Alan uzmanı (öğretmen) kaydı
    - Müfredat uzmanı kaydı
    - Kalite güvence uzmanı kaydı
    """

    try:
        # Rolleri enum'a çevir
        roles = []
        for role_str in request.expert_roles:
            try:
                role = ExpertRole(role_str)
                roles.append(role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid expert_role: {role_str}",
                )

        # Uzman kaydı yap
        await expert_validation_system.register_expert(
            expert_id=request.expert_id, expert_roles=roles
        )

        logger.info(
            "expert_registered",
            expert_id=request.expert_id,
            roles=[r.value for r in roles],
        )

        return {
            "success": True,
            "expert_id": request.expert_id,
            "roles": request.expert_roles,
            "message": "Uzman başarıyla kaydedildi",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "expert_registration_failed", error=str(e), expert_id=request.expert_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/experts/{expert_id}/pending")
async def get_pending_requests_for_expert(
    expert_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Uzman için bekleyen doğrulama taleplerini getir

    Returns:
        Bekleyen talep listesi
    """

    try:
        pending_requests = expert_validation_system.get_pending_requests_for_expert(
            expert_id
        )

        return {
            "expert_id": expert_id,
            "pending_count": len(pending_requests),
            "requests": [
                {
                    "request_id": req.request_id,
                    "content_id": req.content_id,
                    "content_type": req.content_type.value,
                    "subject": req.subject,
                    "topic": req.topic,
                    "priority": req.priority,
                    "submitted_at": req.submitted_at.isoformat(),
                    "review_deadline": req.review_deadline.isoformat()
                    if req.review_deadline
                    else None,
                }
                for req in pending_requests
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_pending_requests_failed", error=str(e), expert_id=expert_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== EXPORTS ====================

__all__ = ["router"]
