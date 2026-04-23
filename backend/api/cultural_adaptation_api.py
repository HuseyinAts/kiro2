"""
Kültürel Adaptasyon API Endpoint'leri

Bu modül, Türk kültürü faktörlerini dikkate alan adaptasyon sisteminin
API endpoint'lerini sağlar.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_user
from services.cultural_adaptation_service import CulturalAdaptationService

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/cultural-adaptation", tags=["Cultural Adaptation"])

# Servis instance'ı
cultural_service = CulturalAdaptationService()


class BehavioralUpdateRequest(BaseModel):
    """Davranış güncelleme isteği"""

    study_time_preference: str | None = Field(
        None, description="Çalışma zamanı tercihi"
    )
    group_study_sessions: int | None = Field(
        None, description="Grup çalışması sayısı"
    )
    individual_study_time: int | None = Field(
        None, description="Bireysel çalışma süresi (dakika)"
    )
    parent_account_activity: float | None = Field(
        None, ge=0.0, le=1.0, description="Veli hesap aktivitesi"
    )
    recommendation_compliance: float | None = Field(
        None, ge=0.0, le=1.0, description="Öneri uyumu"
    )
    leaderboard_engagement: float | None = Field(
        None, ge=0.0, le=1.0, description="Liderlik tablosu katılımı"
    )
    help_requests_sent: int | None = Field(
        None, description="Gönderilen yardım istekleri"
    )
    help_provided_to_peers: int | None = Field(
        None, description="Akranlara sağlanan yardım"
    )
    attention_span: int | None = Field(None, description="Dikkat süresi (dakika)")
    study_schedule_regularity: float | None = Field(
        None, ge=0.0, le=1.0, description="Çalışma programı düzenliliği"
    )


class CulturalAdaptationResponse(BaseModel):
    """Kültürel adaptasyon yanıtı"""

    success: bool
    data: dict[str, Any]
    message: str


@router.get("/student/{student_id}", response_model=CulturalAdaptationResponse)
async def get_student_cultural_adaptation(
    student_id: str,
    force_refresh: bool = Query(False, description="Cache'i yoksay ve yeniden hesapla"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci için kültürel adaptasyon bilgilerini getir

    Bu endpoint, belirtilen öğrenci için:
    - Mevcut kültürel dönem analizi
    - Kişiselleştirilmiş çalışma önerileri
    - Bölgesel ve yaş grubu adaptasyonları
    - Gerçek zamanlı kültürel bağlam analizi
    sağlar.
    """
    try:
        # Yetkilendirme kontrolü
        if (
            current_user.role.value not in ["admin", "teacher"]
            and current_user.id != student_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Bu öğrencinin kültürel adaptasyon bilgilerine erişim yetkiniz yok",
            )

        adaptation_data = await cultural_service.get_student_cultural_adaptation(
            student_id=student_id, force_refresh=force_refresh
        )

        return CulturalAdaptationResponse(
            success=True,
            data=adaptation_data,
            message="Kültürel adaptasyon bilgileri başarıyla getirildi",
        )

    except ValueError as e:
        logger.warning(f"Öğrenci bulunamadı: {student_id} - {e}")
        raise HTTPException(status_code=404, detail="Islem basarisiz. Lutfen tekrar deneyin.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kültürel adaptasyon getirme hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Kültürel adaptasyon bilgileri getirilirken bir hata oluştu",
        )


@router.put(
    "/student/{student_id}/behavioral-update", response_model=CulturalAdaptationResponse
)
async def update_student_behavioral_data(
    student_id: str,
    behavioral_update: BehavioralUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci davranış verilerini güncelle ve adaptasyonu yenile

    Bu endpoint, öğrenci davranış verilerini güncelleyerek:
    - Kültürel bağlam analizini yeniler
    - Adaptasyon önerilerini günceller
    - Kişiselleştirilmiş deneyimi optimize eder
    """
    try:
        # Yetkilendirme kontrolü
        if (
            current_user.role.value not in ["admin", "teacher"]
            and current_user.id != student_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Bu öğrencinin davranış verilerini güncelleme yetkiniz yok",
            )

        # Sadece None olmayan değerleri güncelle
        update_data = {
            key: value
            for key, value in behavioral_update.dict().items()
            if value is not None
        }

        if not update_data:
            raise HTTPException(
                status_code=400, detail="Güncellenecek davranış verisi bulunamadı"
            )

        updated_adaptation = await cultural_service.update_cultural_context(
            student_id=student_id, behavioral_update=update_data
        )

        return CulturalAdaptationResponse(
            success=True,
            data=updated_adaptation,
            message="Davranış verileri güncellendi ve kültürel adaptasyon yenilendi",
        )

    except ValueError as e:
        logger.warning(f"Davranış güncelleme hatası: {student_id} - {e}")
        raise HTTPException(status_code=400, detail="Islem basarisiz. Lutfen tekrar deneyin.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Davranış güncelleme hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Davranış verileri güncellenirken bir hata oluştu"
        )


@router.get("/cultural-period", response_model=CulturalAdaptationResponse)
async def get_current_cultural_period(
    date: str | None = Query(
        None, description="Kontrol edilecek tarih (YYYY-MM-DD formatında)"
    ),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Mevcut kültürel dönem bilgilerini getir

    Bu endpoint şu bilgileri sağlar:
    - Mevcut kültürel dönem (Ramazan, sınav dönemi, bayram vb.)
    - Dönem açıklaması ve özellikleri
    - Genel öneriler ve uyarılar
    """
    try:
        check_date = datetime.now()
        if date:
            try:
                check_date = datetime.fromisoformat(date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Geçersiz tarih formatı. YYYY-MM-DD formatını kullanın.",
                )

        period_info = await cultural_service.get_cultural_period_info(check_date)

        return CulturalAdaptationResponse(
            success=True,
            data=period_info,
            message="Kültürel dönem bilgileri başarıyla getirildi",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kültürel dönem bilgisi getirme hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Kültürel dönem bilgileri getirilirken bir hata oluştu",
        )


@router.get("/regional-culture/{region}", response_model=CulturalAdaptationResponse)
async def get_regional_culture_info(
    region: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Bölgesel kültür bilgilerini getir

    Desteklenen bölgeler:
    - marmara: Marmara Bölgesi
    - ege: Ege Bölgesi
    - akdeniz: Akdeniz Bölgesi
    - ic_anadolu: İç Anadolu Bölgesi
    - karadeniz: Karadeniz Bölgesi
    - dogu_anadolu: Doğu Anadolu Bölgesi
    - guneydogu_anadolu: Güneydoğu Anadolu Bölgesi
    """
    try:
        regional_info = await cultural_service.get_regional_culture_info(region)

        return CulturalAdaptationResponse(
            success=True,
            data=regional_info,
            message=f"{region} bölgesi kültür bilgileri başarıyla getirildi",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bölgesel kültür bilgisi getirme hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Bölgesel kültür bilgileri getirilirken bir hata oluştu",
        )


@router.get("/adaptation-summary", response_model=CulturalAdaptationResponse)
async def get_cultural_adaptation_summary(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Kültürel adaptasyon sistemi özeti

    Bu endpoint sistemin genel durumu hakkında bilgi sağlar:
    - Desteklenen kültürel dönemler
    - Bölgesel adaptasyon seçenekleri
    - Yaş grubu kategorileri
    - Sistem özellikleri
    """
    try:
        summary = {
            "system_info": {
                "name": "Türk Kültürü Adaptasyon Motoru",
                "version": "1.0.0",
                "description": "Türk öğrenci kültürüne uyarlanmış dinamik öğrenme deneyimi sağlar",
            },
            "supported_periods": [
                {"key": "normal", "name": "Normal Dönem"},
                {"key": "ramazan", "name": "Ramazan Ayı"},
                {"key": "kurban_bayrami", "name": "Kurban Bayramı"},
                {"key": "ramazan_bayrami", "name": "Ramazan Bayramı"},
                {"key": "sinav_donemi", "name": "Sınav Dönemi"},
                {"key": "yaz_tatili", "name": "Yaz Tatili"},
                {"key": "kis_tatili", "name": "Kış Tatili"},
                {"key": "milli_bayramlar", "name": "Milli Bayramlar"},
            ],
            "supported_regions": [
                {"key": "marmara", "name": "Marmara Bölgesi"},
                {"key": "ege", "name": "Ege Bölgesi"},
                {"key": "akdeniz", "name": "Akdeniz Bölgesi"},
                {"key": "ic_anadolu", "name": "İç Anadolu Bölgesi"},
                {"key": "karadeniz", "name": "Karadeniz Bölgesi"},
                {"key": "dogu_anadolu", "name": "Doğu Anadolu Bölgesi"},
                {"key": "guneydogu_anadolu", "name": "Güneydoğu Anadolu Bölgesi"},
            ],
            "age_groups": [
                {"key": "ilkokul", "name": "İlkokul (6-10 yaş)"},
                {"key": "ortaokul", "name": "Ortaokul (11-14 yaş)"},
                {"key": "lise", "name": "Lise (15-18 yaş)"},
                {"key": "universite", "name": "Üniversite (18+ yaş)"},
            ],
            "cultural_factors": [
                "Aile baskısı seviyesi",
                "Sosyal çevre etkisi",
                "Dini gözlem seviyesi",
                "Bölgesel eğitim kültürü",
                "Akran rekabeti yoğunluğu",
                "Otorite saygısı seviyesi",
                "Grup çalışması tercihi",
                "Bireysel başarı odağı",
            ],
            "features": [
                "Gerçek zamanlı kültürel dönem tespiti",
                "Bölgesel adaptasyon",
                "Yaş grubu özelleştirmesi",
                "Davranış tabanlı analiz",
                "Dinamik içerik ayarlama",
                "Kişiselleştirilmiş öneriler",
                "Kültürel bağlam farkındalığı",
            ],
        }

        return CulturalAdaptationResponse(
            success=True,
            data=summary,
            message="Kültürel adaptasyon sistemi özeti başarıyla getirildi",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sistem özeti getirme hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Sistem özeti getirilirken bir hata oluştu"
        )


@router.post("/test-adaptation", response_model=CulturalAdaptationResponse)
async def test_cultural_adaptation(
    test_data: dict[str, Any], current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Kültürel adaptasyon testi (sadece admin kullanıcılar için)

    Bu endpoint test amaçlı kültürel adaptasyon hesaplaması yapar.
    Gerçek öğrenci verisi kullanmadan sistem davranışını test etmek için kullanılır.
    """
    try:
        # Sadece admin kullanıcılar test edebilir
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=403,
                detail="Bu endpoint sadece admin kullanıcılar tarafından kullanılabilir",
            )

        # Test verilerini doğrula
        required_fields = ["student_id", "age", "region", "cultural_factors"]
        missing_fields = [field for field in required_fields if field not in test_data]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Eksik test verileri: {', '.join(missing_fields)}",
            )

        # Test adaptasyonu hesapla
        # Bu kısım gerçek implementasyonda test verilerini kullanarak adaptasyon hesaplayacak
        test_result = {
            "test_student_id": test_data["student_id"],
            "input_data": test_data,
            "adaptation_result": {
                "current_period": "normal",
                "adaptation_multiplier": 1.0,
                "recommended_study_hours": 4,
                "optimal_study_times": ["08:00-10:00", "19:00-21:00"],
                "content_difficulty_adjustment": 1.0,
                "social_learning_emphasis": 0.6,
                "individual_focus_emphasis": 0.4,
                "motivational_message_type": "balanced_motivation",
                "cultural_context_explanation": "Test verisi için örnek açıklama",
            },
            "test_timestamp": datetime.now().isoformat(),
        }

        return CulturalAdaptationResponse(
            success=True,
            data=test_result,
            message="Kültürel adaptasyon testi başarıyla tamamlandı",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kültürel adaptasyon test hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Kültürel adaptasyon testi sırasında bir hata oluştu",
        )
