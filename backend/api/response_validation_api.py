"""
Response Validation API Endpoints

Bu modül, AI yanıt doğrulama sistemi için FastAPI endpoint'lerini içerir.

Endpoints:
- POST /api/v1/validate-response - Yanıt doğrulama
- GET /api/v1/validation-report/{response_id} - Rapor görüntüleme
- GET /api/v1/validation-stats - İstatistikler (admin)

Requirements: REQ-6.1 - REQ-6.6
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

# Auth dependencies - enable in production
# from backend.core.auth_dependencies import get_current_user, get_admin_user
try:
    from orchestrator.response_validation_orchestrator import (
        ResponseValidationOrchestrator,
    )
    from validators.base_response_validator import (
        AgentResponse,
        AgentTypeError,
    )
    from validators.error_reporter import get_error_reporter
except ImportError:
    ResponseValidationOrchestrator = None
    AgentResponse = None
    AgentTypeError = None
    get_error_reporter = None
try:
    from hooks.response_validation_hook import (
        get_validation_hook,
    )
except ImportError:
    get_validation_hook = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/response-validation", tags=["validation"])

# Global orchestrator instance
_orchestrator: Optional[ResponseValidationOrchestrator] = None


def get_orchestrator() -> ResponseValidationOrchestrator:
    """Orchestrator instance'ı al veya oluştur"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ResponseValidationOrchestrator()
    return _orchestrator


# Request/Response Models
class ValidateResponseRequest(BaseModel):
    """Yanıt doğrulama isteği"""
    agent_type: str = Field(
        description="Agent tipi: learning_path, study_buddy, exam"
    )
    response_id: str = Field(description="Yanıt unique ID'si")
    user_id: str = Field(description="Kullanıcı ID'si")
    query: str = Field(description="Kullanıcı sorusu/isteği")
    response_text: str = Field(description="Agent'ın metin yanıtı")
    response_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Agent'a özgü yapılandırılmış veri"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Ek bağlam bilgisi"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "agent_type": "study_buddy",
            "response_id": "resp_123",
            "user_id": "user_456",
            "query": "Osmanlı İmparatorluğu ne zaman kuruldu?",
            "response_text": "Osmanlı İmparatorluğu 1299 yılında kuruldu.",
            "response_data": {},
            "context": {"grade_level": 10}
        }
    })


class ValidationResponse(BaseModel):
    """Doğrulama yanıtı"""
    response_id: str
    confidence_score: float
    action: str
    action_description: str
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    duration_seconds: float
    timestamp: str


class ValidationStatsResponse(BaseModel):
    """Doğrulama istatistikleri yanıtı"""
    total_validations: int
    average_confidence: float
    approval_rate: float
    review_rate: float
    rejection_rate: float
    average_duration: float
    by_agent_type: Dict[str, Dict[str, Any]]
    period: str


# In-memory stats storage (production'da Redis/DB kullanılmalı)
_validation_stats: Dict[str, Any] = {
    "total": 0,
    "approved": 0,
    "review": 0,
    "rejected": 0,
    "total_confidence": 0.0,
    "total_duration": 0.0,
    "by_agent": {},
    "reports": {},  # response_id -> report
}


@router.post(
    "/validate-response",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="AI yanıtını doğrula",
    description="Bir AI agent yanıtını tam doğrulama pipeline'ından geçirir."
)
async def validate_response(
    request: ValidateResponseRequest,
    orchestrator: ResponseValidationOrchestrator = Depends(get_orchestrator),
) -> ValidationResponse:
    """
    AI yanıtını doğrula.

    - **agent_type**: learning_path, study_buddy, exam
    - **response_id**: Unique yanıt ID'si
    - **user_id**: Kullanıcı ID'si
    - **query**: Kullanıcı sorusu
    - **response_text**: Agent yanıtı
    """
    try:
        # AgentResponse oluştur
        agent_response = AgentResponse(
            agent_type=request.agent_type,
            response_id=request.response_id,
            user_id=request.user_id,
            query=request.query,
            response_text=request.response_text,
            response_data=request.response_data or {},
            context=request.context,
            timestamp=datetime.now(timezone.utc),
        )

        # Doğrulama yap
        result = await orchestrator.validate_response(agent_response)

        # İstatistikleri güncelle
        _update_stats(result)

        # Raporu kaydet
        _validation_stats["reports"][request.response_id] = result

        return ValidationResponse(
            response_id=result["response_id"],
            confidence_score=result["confidence_score"],
            action=result["action"],
            action_description=result["action_description"],
            errors=result["errors"],
            warnings=result["warnings"],
            suggestions=result["suggestions"],
            duration_seconds=result["duration_seconds"],
            timestamp=result["timestamp"],
        )

    except AgentTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Geçersiz agent tipi: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doğrulama hatası: {str(e)}"
        )


@router.get(
    "/validation-report/{response_id}",
    summary="Doğrulama raporunu al",
    description="Belirli bir yanıtın doğrulama raporunu getirir."
)
async def get_validation_report(
    response_id: str,
) -> Dict[str, Any]:
    """
    Doğrulama raporunu al.

    - **response_id**: Yanıt ID'si
    """
    report = _validation_stats["reports"].get(response_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rapor bulunamadı: {response_id}"
        )

    return report


@router.get(
    "/validation-stats",
    response_model=ValidationStatsResponse,
    summary="Doğrulama istatistiklerini al (Admin)",
    description="Sistem genelindeki doğrulama istatistiklerini getirir."
)
async def get_validation_stats(
    period: str = Query(default="all", description="İstatistik periyodu"),
    # current_user = Depends(get_admin_user),  # Production'da aktif edilmeli
) -> ValidationStatsResponse:
    """
    Doğrulama istatistiklerini al.

    - **period**: all, today, week, month
    """
    total = _validation_stats["total"]

    if total == 0:
        return ValidationStatsResponse(
            total_validations=0,
            average_confidence=0.0,
            approval_rate=0.0,
            review_rate=0.0,
            rejection_rate=0.0,
            average_duration=0.0,
            by_agent_type={},
            period=period,
        )

    return ValidationStatsResponse(
        total_validations=total,
        average_confidence=_validation_stats["total_confidence"] / total,
        approval_rate=_validation_stats["approved"] / total * 100,
        review_rate=_validation_stats["review"] / total * 100,
        rejection_rate=_validation_stats["rejected"] / total * 100,
        average_duration=_validation_stats["total_duration"] / total,
        by_agent_type=_validation_stats["by_agent"],
        period=period,
    )


@router.post(
    "/validate-quick",
    summary="Hızlı doğrulama",
    description="Sadece agent-specific doğrulama yapar (hızlı sonuç)."
)
async def quick_validate(
    request: ValidateResponseRequest,
    orchestrator: ResponseValidationOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Hızlı doğrulama (sadece agent-specific).
    """
    try:
        agent_response = AgentResponse(
            agent_type=request.agent_type,
            response_id=request.response_id,
            user_id=request.user_id,
            query=request.query,
            response_text=request.response_text,
            response_data=request.response_data or {},
            context=request.context,
        )

        confidence, action = await orchestrator.quick_validate(agent_response)

        return {
            "response_id": request.response_id,
            "confidence_score": confidence,
            "action": action.value,
            "quick_validation": True,
        }

    except Exception as e:
        logger.error(f"Quick validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


def _update_stats(result: Dict[str, Any]):
    """İstatistikleri güncelle"""
    _validation_stats["total"] += 1
    _validation_stats["total_confidence"] += result["confidence_score"]
    _validation_stats["total_duration"] += result["duration_seconds"]

    action = result["action"]
    if action == "approve":
        _validation_stats["approved"] += 1
    elif action == "review":
        _validation_stats["review"] += 1
    else:
        _validation_stats["rejected"] += 1

    # Agent bazlı istatistik
    agent_type = result.get("metadata", {}).get("agent_type", "unknown")
    if agent_type not in _validation_stats["by_agent"]:
        _validation_stats["by_agent"][agent_type] = {
            "total": 0,
            "approved": 0,
            "review": 0,
            "rejected": 0,
        }

    _validation_stats["by_agent"][agent_type]["total"] += 1
    _validation_stats["by_agent"][agent_type][action] += 1


# ============ Error Reporting Endpoints ============

@router.get(
    "/validation-errors",
    summary="Doğrulama hatalarını al (Admin)",
    description="Belirli dönemdeki doğrulama hatalarını getirir."
)
async def get_validation_errors(
    period_hours: int = Query(default=24, description="Dönem (saat)"),
    # current_user = Depends(get_admin_user),  # Production'da aktif edilmeli
) -> Dict[str, Any]:
    """
    Doğrulama hatalarını al.

    - **period_hours**: Son kaç saatteki hatalar
    """
    reporter = get_error_reporter()
    frequency = reporter.get_error_frequency(period_hours)
    trends = reporter.analyze_trends(period_hours, period_hours)

    return {
        "period_hours": period_hours,
        "error_frequency": frequency,
        "trends": [t.model_dump() for t in trends],
    }


@router.get(
    "/validation-error-report",
    summary="Hata raporu oluştur (Admin)",
    description="Kapsamlı hata analiz raporu oluşturur."
)
async def get_validation_error_report(
    period_hours: int = Query(default=24, description="Rapor dönemi (saat)"),
    # current_user = Depends(get_admin_user),  # Production'da aktif edilmeli
) -> Dict[str, Any]:
    """
    Kapsamlı hata raporu oluştur.

    - **period_hours**: Rapor dönemi
    """
    reporter = get_error_reporter()
    report = reporter.generate_report(period_hours)

    return report.model_dump()


@router.get(
    "/validation-suggestions",
    summary="İyileştirme önerileri al",
    description="Hata analizine dayalı iyileştirme önerileri."
)
async def get_validation_suggestions(
    period_hours: int = Query(default=24, description="Analiz dönemi"),
) -> Dict[str, Any]:
    """
    İyileştirme önerileri al.
    """
    reporter = get_error_reporter()
    suggestions = reporter.generate_suggestions(period_hours)

    return {
        "period_hours": period_hours,
        "suggestions": [s.model_dump() for s in suggestions],
    }


# ============ Hook Management Endpoints ============

@router.post(
    "/validation-hook/enable",
    summary="Doğrulama hook'unu etkinleştir",
    description="Response validation hook'unu etkinleştirir."
)
async def enable_validation_hook(
    # current_user = Depends(get_admin_user),  # Production'da aktif edilmeli
) -> Dict[str, Any]:
    """
    Validation hook'unu etkinleştir.
    """
    hook = get_validation_hook()
    hook.enable()

    return {
        "status": "enabled",
        "message": "Response validation hook etkinleştirildi",
    }


@router.post(
    "/validation-hook/disable",
    summary="Doğrulama hook'unu devre dışı bırak",
    description="Response validation hook'unu devre dışı bırakır."
)
async def disable_validation_hook(
    # current_user = Depends(get_admin_user),  # Production'da aktif edilmeli
) -> Dict[str, Any]:
    """
    Validation hook'unu devre dışı bırak.
    """
    hook = get_validation_hook()
    hook.disable()

    return {
        "status": "disabled",
        "message": "Response validation hook devre dışı bırakıldı",
    }


@router.get(
    "/validation-hook/stats",
    summary="Hook istatistiklerini al",
    description="Validation hook istatistiklerini getirir."
)
async def get_validation_hook_stats() -> Dict[str, Any]:
    """
    Hook istatistiklerini al.
    """
    hook = get_validation_hook()

    return {
        "enabled": hook.enabled,
        "stats": hook.get_stats(),
    }
