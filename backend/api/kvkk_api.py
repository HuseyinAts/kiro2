"""
KVKK Compliance API Endpoints
Turkish GDPR Compliance REST API

Endpoints:
- POST /api/v1/kvkk/consent/grant - Rıza ver
- POST /api/v1/kvkk/consent/withdraw - Rızayı geri çek
- GET /api/v1/kvkk/consent/check - Rıza kontrolü
- POST /api/v1/kvkk/data-processing/log - Veri işleme kaydı
- POST /api/v1/kvkk/data-subject/request - Veri sahibi talebi
- GET /api/v1/kvkk/data-subject/request/{request_id} - Talep durumu
- POST /api/v1/kvkk/data-subject/request/{request_id}/process - Talebi işle
- POST /api/v1/kvkk/data-breach/report - Veri ihlali bildir
- GET /api/v1/kvkk/user/{user_id}/export - Kullanıcı verilerini dışa aktar
- POST /api/v1/kvkk/user/{user_id}/anonymize - Kullanıcı verilerini anonimleştir
- GET /api/v1/kvkk/compliance/report - Uyumluluk raporu
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.kvkk_compliance import (
    KVKKComplianceManager,
    get_kvkk_manager,
    ConsentRequest,
    ConsentResponse,
    DataProcessingLogRequest,
    DataSubjectRequestModel,
    DataBreachReport,
    DataProcessingPurpose,
    DataSubjectRight,
)
from core.dependencies import get_db, get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/v1/kvkk", tags=["KVKK Compliance"])


@router.post("/consent/grant", response_model=Dict[str, Any])
async def grant_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Rıza ver

    KVKK Madde 5: Açık rıza ile kişisel veri işleme

    Args:
        request: Rıza talebi
        db: Database session
        current_user: Mevcut kullanıcı

    Returns:
        Rıza yanıtı
    """
    try:
        # Kullanıcı kendi rızasını verebilir
        if request.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece kendi rızanızı verebilirsiniz",
            )

        manager = get_kvkk_manager(db)
        response = await manager.grant_consent(request)

        return {
            "success": True,
            "data": {
                "consent_id": response.consent_id,
                "status": response.status.value,
                "granted_at": response.granted_at.isoformat()
                if response.granted_at
                else None,
                "expires_at": response.expires_at.isoformat()
                if response.expires_at
                else None,
            },
            "message": "Rızanız başarıyla kaydedildi",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rıza kaydı sırasında hata: {str(e)}",
        )


@router.post("/consent/withdraw", response_model=Dict[str, Any])
async def withdraw_consent(
    consent_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Rızayı geri çek

    KVKK Madde 11: Veri sahibinin rızasını geri çekme hakkı

    Args:
        consent_id: Rıza ID
        db: Database session
        current_user: Mevcut kullanıcı

    Returns:
        İşlem sonucu
    """
    try:
        manager = get_kvkk_manager(db)
        result = await manager.withdraw_consent(current_user["id"], consent_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Rıza bulunamadı"
            )

        return {
            "success": True,
            "data": {"consent_id": consent_id},
            "message": "Rızanız başarıyla geri çekildi",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rıza geri çekme sırasında hata: {str(e)}",
        )


@router.get("/consent/check", response_model=Dict[str, Any])
async def check_consent(
    purpose: DataProcessingPurpose,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Rıza kontrolü

    Args:
        purpose: Veri işleme amacı
        db: Database session
        current_user: Mevcut kullanıcı

    Returns:
        Rıza durumu
    """
    try:
        manager = get_kvkk_manager(db)
        has_consent = await manager.check_consent(current_user["id"], purpose)

        return {
            "success": True,
            "data": {"has_consent": has_consent, "purpose": purpose.value},
            "message": "Rıza kontrolü tamamlandı",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rıza kontrolü sırasında hata: {str(e)}",
        )


@router.post("/data-processing/log", response_model=Dict[str, Any])
async def log_data_processing(
    request: DataProcessingLogRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_admin_user),
):
    """
    Veri işleme kaydı oluştur

    KVKK Madde 12: Veri sorumlusunun bildirimi

    Args:
        request: Veri işleme log talebi
        db: Database session
        current_user: Mevcut admin kullanıcı

    Returns:
        Log ID
    """
    try:
        manager = get_kvkk_manager(db)
        log_id = await manager.log_data_processing(request)

        return {
            "success": True,
            "data": {"log_id": log_id},
            "message": "Veri işleme kaydı oluşturuldu",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Veri işleme kaydı sırasında hata: {str(e)}",
        )


@router.post("/data-subject/request", response_model=Dict[str, Any])
async def create_data_subject_request(
    request: DataSubjectRequestModel,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Veri sahibi talebi oluştur

    KVKK Madde 11: Veri sahibinin hakları
    - Bilgi talep etme
    - Düzeltme
    - Silme
    - İşlemenin kısıtlanması
    - İtiraz
    - Veri taşınabilirliği

    Args:
        request: Veri sahibi talep modeli
        db: Database session
        current_user: Mevcut kullanıcı

    Returns:
        Talep ID
    """
    try:
        # Kullanıcı kendi talebi için başvurabilir
        if request.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece kendi taleplerinizi oluşturabilirsiniz",
            )

        manager = get_kvkk_manager(db)
        request_id = await manager.create_data_subject_request(request)

        return {
            "success": True,
            "data": {
                "request_id": request_id,
                "request_type": request.request_type.value,
                "deadline": "30 gün içinde yanıtlanacaktır",
            },
            "message": "Talebiniz başarıyla oluşturuldu. 30 gün içinde yanıtlanacaktır.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Talep oluşturma sırasında hata: {str(e)}",
        )


@router.post(
    "/data-subject/request/{request_id}/process", response_model=Dict[str, Any]
)
async def process_data_subject_request(
    request_id: str,
    response_text: str,
    request_status: str = "completed",
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_admin_user),
):
    """
    Veri sahibi talebini işle

    KVKK Madde 13: 30 gün içinde yanıt verme yükümlülüğü

    Args:
        request_id: Talep ID
        response_text: Yanıt metni
        request_status: Talep durumu (completed, rejected)
        db: Database session
        current_user: Mevcut admin kullanıcı

    Returns:
        İşlem sonucu
    """
    try:
        manager = get_kvkk_manager(db)
        result = await manager.process_data_subject_request(
            request_id, response_text, request_status
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Talep bulunamadı"
            )

        return {
            "success": True,
            "data": {"request_id": request_id, "status": request_status},
            "message": "Talep başarıyla işlendi",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Talep işleme sırasında hata: {str(e)}",
        )


@router.post("/data-breach/report", response_model=Dict[str, Any])
async def report_data_breach(
    report: DataBreachReport,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_admin_user),
):
    """
    Veri ihlali bildir

    KVKK Madde 12: Veri ihlali bildirimi
    - Kritik ihlallerde KVKK Kurulu'na 72 saat içinde bildirim
    - Etkilenen kullanıcılara bildirim

    Args:
        report: Veri ihlali raporu
        db: Database session
        current_user: Mevcut admin kullanıcı

    Returns:
        İhlal ID
    """
    try:
        manager = get_kvkk_manager(db)
        breach_id = await manager.report_data_breach(report)

        warning_message = ""
        if report.severity in ["high", "critical"]:
            warning_message = " UYARI: Kritik ihlal! KVKK Kurulu'na 72 saat içinde bildirim yapılmalıdır."

        return {
            "success": True,
            "data": {
                "breach_id": breach_id,
                "severity": report.severity,
                "affected_users": report.affected_users_count,
            },
            "message": f"Veri ihlali kaydedildi.{warning_message}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Veri ihlali bildirimi sırasında hata: {str(e)}",
        )


@router.get("/user/{user_id}/export", response_model=Dict[str, Any])
async def export_user_data(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Kullanıcı verilerini dışa aktar

    KVKK Madde 11: Veri taşınabilirliği hakkı

    Args:
        user_id: Kullanıcı ID
        db: Database session
        current_user: Mevcut kullanıcı

    Returns:
        Kullanıcı verileri
    """
    try:
        # Kullanıcı sadece kendi verilerini dışa aktarabilir
        if user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece kendi verilerinizi dışa aktarabilirsiniz",
            )

        manager = get_kvkk_manager(db)
        user_data = await manager.get_user_data_export(user_id)

        return {
            "success": True,
            "data": user_data,
            "message": "Verileriniz başarıyla dışa aktarıldı",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Veri dışa aktarma sırasında hata: {str(e)}",
        )


@router.post("/user/{user_id}/anonymize", response_model=Dict[str, Any])
async def anonymize_user_data(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Kullanıcı verilerini anonimleştir

    KVKK Madde 11: Silme hakkı (unutulma hakkı)

    Args:
        user_id: Kullanıcı ID
        db: Database session
        current_user: Mevcut kullanıcı

    Returns:
        İşlem sonucu
    """
    try:
        # Kullanıcı sadece kendi verilerini anonimleştirebilir
        if user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece kendi verilerinizi anonimleştirebilirsiniz",
            )

        manager = get_kvkk_manager(db)
        result = await manager.anonymize_user_data(user_id)

        return {
            "success": True,
            "data": {"user_id": user_id, "anonymized": result},
            "message": "Verileriniz başarıyla anonimleştirildi",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Veri anonimleştirme sırasında hata: {str(e)}",
        )


@router.get("/compliance/report", response_model=Dict[str, Any])
async def get_compliance_report(
    start_date: datetime = Query(..., description="Başlangıç tarihi"),
    end_date: datetime = Query(..., description="Bitiş tarihi"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_admin_user),
):
    """
    KVKK uyumluluk raporu

    Yöneticiler için detaylı uyumluluk raporu

    Args:
        start_date: Başlangıç tarihi
        end_date: Bitiş tarihi
        db: Database session
        current_user: Mevcut admin kullanıcı

    Returns:
        Uyumluluk raporu
    """
    try:
        manager = get_kvkk_manager(db)
        report = await manager.get_compliance_report(start_date, end_date)

        return {
            "success": True,
            "data": report,
            "message": "Uyumluluk raporu oluşturuldu",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rapor oluşturma sırasında hata: {str(e)}",
        )


# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def kvkk_health_check():
    """KVKK sistemi sağlık kontrolü"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "KVKK Compliance System",
            "version": "1.0.0",
        },
        "message": "KVKK sistemi çalışıyor",
    }
