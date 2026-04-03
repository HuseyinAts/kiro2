"""
Zone of Proximal Development + MEB Maarif API - DEVRİMSEL
Türk eğitim kültürüne uyarlanmış ZPD sistemi API endpoint'leri

DEVRİMSEL ÖZELLİKLER:
- Türk kültürü faktörleri entegrasyonu
- MEB Maarif değerleri uyum sistemi
- Grup vs bireysel öğrenme dengeleme
- Kültürel bağlam farkındalıklı ZPD hesaplama
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, UserRole, get_current_user
from models.zpd_maarif import (
    KulturelBaglamProfili,
    MaarifDegerleriProfili,
    ZPDHesaplamaParametreleri,
    ZPDSeviyesi,
)
from services.zpd_maarif_service import ZPDMaarifService

# Yeni devrimsel modeller

router = APIRouter(prefix="/api/v1/zpd-maarif", tags=["ZPD Maarif"])

# Servis instance'ı
zpd_service = ZPDMaarifService()


def _verify_student_access(current_user: AuthenticatedUser, ogrenci_id: str) -> None:
    """IDOR: student own data only, admin/teacher any."""
    if current_user.role in (UserRole.ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN):
        return
    if str(current_user.id) != ogrenci_id:
        raise HTTPException(
            status_code=403, detail="Bu ogrenci verisine erisim yetkiniz yok"
        )


class ZPDHesaplamaRequest(BaseModel):
    """ZPD hesaplama isteği"""

    ogrenci_id: str
    konu: str
    mevcut_seviye: float = Field(ge=0.0, le=10.0)
    kulturel_profil: KulturelBaglamProfili | None = None
    maarif_profili: MaarifDegerleriProfili | None = None
    parametreler: ZPDHesaplamaParametreleri | None = None


class ZPDOptimizasyonRequest(BaseModel):
    """ZPD optimizasyon isteği"""

    ogrenci_id: str
    konu: str
    performans_verileri: list[dict[str, Any]]


class ZPDResponse(BaseModel):
    """ZPD API yanıtı"""

    success: bool
    data: Any | None = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


# DEVRİMSEL YENİ REQUEST/RESPONSE MODELLERİ


class RevolutionaryZPDRequest(BaseModel):
    """DEVRİMSEL ZPD hesaplama isteği"""

    student_id: str
    subject: str
    current_level: float = Field(ge=0.0, le=10.0)
    behavioral_data: dict[str, Any]
    content_description: str = ""
    family_survey: dict[str, Any] | None = None


class RevolutionaryRecommendationRequest(BaseModel):
    """DEVRİMSEL öneri isteği"""

    student_id: str
    subject: str
    current_level: float = Field(ge=0.0, le=10.0)
    behavioral_data: dict[str, Any]
    learning_objective: str
    content_description: str = ""
    family_survey: dict[str, Any] | None = None


class CulturalAdaptationRequest(BaseModel):
    """Kültürel adaptasyon isteği"""

    student_id: str
    current_difficulty: float = Field(ge=0.0, le=10.0)
    student_performance: dict[str, float]
    behavioral_data: dict[str, Any]


class MaarifAlignmentRequest(BaseModel):
    """Maarif uyum analizi isteği"""

    subject: str = Field(..., min_length=2, max_length=100)
    content_description: str = Field(..., min_length=5, max_length=5000)


class LearningBalanceRequest(BaseModel):
    """Öğrenme dengesi analizi isteği"""

    student_id: str
    behavioral_data: dict[str, Any]


class CulturalPatternAnalysisRequest(BaseModel):
    """Kültürel kalıp analizi isteği"""

    student_id: str
    learning_sessions: list[dict[str, Any]]


@router.post("/hesapla", response_model=ZPDResponse)
async def hesapla_zpd(
    request: ZPDHesaplamaRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Türk eğitim kültürüne uyarlanmış ZPD aralığı hesapla

    Bu endpoint Vygotsky'nin ZPD teorisini MEB Maarif modeli ile birleştirerek
    Türk öğrenci psikolojisine özel optimal zorluk seviyesi belirler.

    **Devrimsel Özellikler:**
    - Türk kültürü faktörleri (grup çalışması, öğretmene saygı)
    - MEB Maarif değerleri entegrasyonu
    - Kültürel bağlam farkındalıklı hesaplama
    """
    # Ownership check — users can only calculate ZPD for themselves
    if request.ogrenci_id != str(current_user.id) and current_user.role.value not in (
        "admin",
        "teacher",
    ):
        raise HTTPException(
            status_code=403, detail="Bu ogrenci icin ZPD hesaplama yetkiniz yok"
        )

    try:
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=request.ogrenci_id,
            konu=request.konu,
            mevcut_seviye=request.mevcut_seviye,
            kulturel_profil=request.kulturel_profil,
            maarif_profili=request.maarif_profili,
            parametreler=request.parametreler,
        )

        return ZPDResponse(
            success=True,
            data=zpd_araligi.dict(),
            message=f"ZPD başarıyla hesaplandı. Optimal zorluk: {zpd_araligi.optimal_zorluk:.2f}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/optimize", response_model=ZPDResponse)
async def optimize_zpd(
    request: ZPDOptimizasyonRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Performans verilerine göre ZPD parametrelerini optimize et

    Bu endpoint geçmiş performans verilerini analiz ederek
    öğrenci için en uygun öğrenme stratejilerini önerir.
    """
    _verify_student_access(current_user, request.ogrenci_id)
    try:
        optimizasyon_sonucu = await zpd_service.optimize_zpd_parametreleri(
            ogrenci_id=request.ogrenci_id,
            konu=request.konu,
            performans_verileri=request.performans_verileri,
        )

        return ZPDResponse(
            success=True,
            data=optimizasyon_sonucu.dict(),
            message=f"ZPD optimizasyonu tamamlandı. Önerilen zorluk: {optimizasyon_sonucu.onerilen_zorluk_seviyesi:.2f}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/profil/kulturel/{ogrenci_id}", response_model=ZPDResponse)
async def get_kulturel_profil(
    ogrenci_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Öğrencinin kültürel bağlam profilini getir"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Varsayılan profil oluştur (gerçek uygulamada veritabanından gelir)
        kulturel_profil = await zpd_service._olustur_varsayilan_kulturel_profil(
            ogrenci_id
        )

        return ZPDResponse(
            success=True,
            data=kulturel_profil.dict(),
            message="Kültürel profil başarıyla getirildi",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/profil/maarif/{ogrenci_id}", response_model=ZPDResponse)
async def get_maarif_profili(
    ogrenci_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Öğrencinin MEB Maarif değerleri profilini getir"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Varsayılan profil oluştur (gerçek uygulamada veritabanından gelir)
        maarif_profili = await zpd_service._olustur_varsayilan_maarif_profili(
            ogrenci_id
        )

        return ZPDResponse(
            success=True,
            data=maarif_profili.dict(),
            message="MEB Maarif profili başarıyla getirildi",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.put("/profil/kulturel/{ogrenci_id}", response_model=ZPDResponse)
async def update_kulturel_profil(
    ogrenci_id: str,
    profil: KulturelBaglamProfili,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Öğrencinin kültürel bağlam profilini güncelle"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Profil güncelleme (gerçek uygulamada veritabanına kaydedilir)
        profil.ogrenci_id = ogrenci_id
        profil.guncelleme_tarihi = datetime.now()

        return ZPDResponse(
            success=True,
            data=profil.dict(),
            message="Kültürel profil başarıyla güncellendi",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.put("/profil/maarif/{ogrenci_id}", response_model=ZPDResponse)
async def update_maarif_profili(
    ogrenci_id: str,
    profil: MaarifDegerleriProfili,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Öğrencinin MEB Maarif değerleri profilini güncelle"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Profil güncelleme (gerçek uygulamada veritabanına kaydedilir)
        profil.ogrenci_id = ogrenci_id
        profil.guncelleme_tarihi = datetime.now()

        return ZPDResponse(
            success=True,
            data=profil.dict(),
            message="MEB Maarif profili başarıyla güncellendi",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/zorluk-seviyesi", response_model=ZPDResponse)
async def get_zorluk_seviyesi(
    ogrenci_id: str = Query(..., description="Öğrenci ID"),
    konu: str = Query(..., description="Konu adı"),
    hedef_zorluk: float = Query(
        ..., ge=0.0, le=10.0, description="Hedef zorluk seviyesi"
    ),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Hedef zorluğun ZPD içindeki seviyesini belirle"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Mevcut ZPD'yi al
        mevcut_zpd = await zpd_service._get_mevcut_zpd(ogrenci_id, konu)

        if mevcut_zpd is None:
            # ZPD yoksa hesapla
            zpd_araligi = await zpd_service.hesapla_turk_zpd(
                ogrenci_id=ogrenci_id,
                konu=konu,
                mevcut_seviye=5.0,  # Varsayılan orta seviye
            )
        else:
            zpd_araligi = mevcut_zpd

        # Zorluk seviyesini belirle
        zorluk_seviyesi = zpd_araligi.get_zorluk_seviyesi(hedef_zorluk)

        return ZPDResponse(
            success=True,
            data={
                "hedef_zorluk": hedef_zorluk,
                "zorluk_seviyesi": zorluk_seviyesi.value,
                "zpd_araligi": {
                    "alt_sinir": zpd_araligi.alt_sinir,
                    "ust_sinir": zpd_araligi.ust_sinir,
                    "optimal_zorluk": zpd_araligi.optimal_zorluk,
                },
                "oneri": await _get_zorluk_seviyesi_onerisi(zorluk_seviyesi),
            },
            message=f"Zorluk seviyesi belirlendi: {zorluk_seviyesi.value}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/gecmis/{ogrenci_id}", response_model=ZPDResponse)
async def get_zpd_gecmisi(
    ogrenci_id: str,
    konu: str | None = Query(None, description="Konu filtresi"),
    limit: int = Query(10, ge=1, le=50, description="Maksimum kayıt sayısı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Öğrencinin ZPD hesaplama geçmişini getir"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Geçmiş verilerini getir
        tum_gecmis = zpd_service.hesaplama_gecmisi

        # Öğrenci bazlı filtreleme
        ogrenci_gecmisi = []
        for anahtar, gecmis_listesi in tum_gecmis.items():
            if anahtar.startswith(ogrenci_id):
                for gecmis in gecmis_listesi:
                    if konu is None or gecmis.konu == konu:
                        ogrenci_gecmisi.append(gecmis)

        # Tarihe göre sırala ve sınırla
        ogrenci_gecmisi.sort(key=lambda x: x.hesaplama_tarihi, reverse=True)
        ogrenci_gecmisi = ogrenci_gecmisi[:limit]

        # Serialize et
        gecmis_data = [
            {
                "konu": g.konu,
                "hesaplama_tarihi": g.hesaplama_tarihi.isoformat(),
                "optimal_zorluk": g.zpd_araligi.optimal_zorluk,
                "hesaplama_guveni": g.zpd_araligi.hesaplama_guveni,
                "kulturel_uyum_guveni": g.zpd_araligi.kulturel_uyum_guveni,
            }
            for g in ogrenci_gecmisi
        ]

        return ZPDResponse(
            success=True,
            data={"gecmis": gecmis_data, "toplam_kayit": len(gecmis_data)},
            message=f"{len(gecmis_data)} ZPD geçmiş kaydı getirildi",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/istatistikler/{ogrenci_id}", response_model=ZPDResponse)
async def get_zpd_istatistikleri(
    ogrenci_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Öğrencinin ZPD istatistiklerini getir"""
    _verify_student_access(current_user, ogrenci_id)
    try:
        # Geçmiş verilerini analiz et
        tum_gecmis = zpd_service.hesaplama_gecmisi
        ogrenci_gecmisi = []

        for anahtar, gecmis_listesi in tum_gecmis.items():
            if anahtar.startswith(ogrenci_id):
                ogrenci_gecmisi.extend(gecmis_listesi)

        if not ogrenci_gecmisi:
            return ZPDResponse(
                success=True,
                data={
                    "toplam_hesaplama": 0,
                    "ortalama_optimal_zorluk": 0.0,
                    "ortalama_hesaplama_guveni": 0.0,
                    "konu_dagilimi": {},
                },
                message="Henüz ZPD hesaplama geçmişi bulunmuyor",
            )

        # İstatistikleri hesapla
        toplam_hesaplama = len(ogrenci_gecmisi)
        ortalama_optimal_zorluk = (
            sum(g.zpd_araligi.optimal_zorluk for g in ogrenci_gecmisi)
            / toplam_hesaplama
        )
        ortalama_hesaplama_guveni = (
            sum(g.zpd_araligi.hesaplama_guveni for g in ogrenci_gecmisi)
            / toplam_hesaplama
        )

        # Konu dağılımı
        konu_dagilimi = {}
        for gecmis in ogrenci_gecmisi:
            konu = gecmis.konu
            if konu not in konu_dagilimi:
                konu_dagilimi[konu] = 0
            konu_dagilimi[konu] += 1

        return ZPDResponse(
            success=True,
            data={
                "toplam_hesaplama": toplam_hesaplama,
                "ortalama_optimal_zorluk": round(ortalama_optimal_zorluk, 2),
                "ortalama_hesaplama_guveni": round(ortalama_hesaplama_guveni, 2),
                "konu_dagilimi": konu_dagilimi,
            },
            message="ZPD istatistikleri başarıyla hesaplandı",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


async def _get_zorluk_seviyesi_onerisi(zorluk_seviyesi: ZPDSeviyesi) -> str:
    """Zorluk seviyesine göre öneri metni döndür"""
    oneriler = {
        ZPDSeviyesi.COK_KOLAY: "Bu seviye çok kolay. Daha zorlu içeriklerle ilerleme sağlayabilirsiniz.",
        ZPDSeviyesi.KOLAY: "Bu seviye kolay. Mevcut bilgilerinizi pekiştirmek için uygun.",
        ZPDSeviyesi.OPTIMAL: "Bu seviye optimal! En verimli öğrenme için ideal zorluk seviyesi.",
        ZPDSeviyesi.ZOR: "Bu seviye zor ama başarılabilir. Öğretmen rehberliği önerilir.",
        ZPDSeviyesi.COK_ZOR: "Bu seviye çok zor. Önce daha basit konuları pekiştirin.",
    }
    return oneriler.get(zorluk_seviyesi, "Zorluk seviyesi değerlendirilemedi.")


# DEVRİMSEL YENİ ENDPOINT'LER


@router.post("/revolutionary/calculate", response_model=ZPDResponse)
async def calculate_revolutionary_zpd(
    request: RevolutionaryZPDRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: Türk kültürüne uyarlanmış ZPD hesaplama

    Bu endpoint Vygotsky ZPD + MEB Maarif + Türk kültürü entegrasyonu ile
    dünya çapında benzersiz bir öğrenme aralığı hesaplama sistemi sunar.

    **Devrimsel Özellikler:**
    - Türk öğrenci kültürü faktörleri (grup çalışması, öğretmene saygı)
    - MEB Maarif değerleri entegrasyonu
    - Kültürel bağlam farkındalıklı hesaplama
    - Grup vs bireysel öğrenme dengeleme
    """
    try:
        zpd_range = await zpd_service.calculate_revolutionary_zpd(
            student_id=request.student_id,
            subject=request.subject,
            current_level=request.current_level,
            behavioral_data=request.behavioral_data,
            content_description=request.content_description,
            family_survey=request.family_survey,
        )

        return ZPDResponse(
            success=True,
            data={
                "student_id": zpd_range.student_id,
                "subject": zpd_range.subject,
                "current_level": zpd_range.current_level,
                "lower_bound": zpd_range.lower_bound,
                "upper_bound": zpd_range.upper_bound,
                "optimal_challenge": zpd_range.optimal_challenge,
                "group_individual_balance": zpd_range.group_individual_balance,
                "cultural_context": {
                    "group_learning_preference": zpd_range.cultural_context.group_learning_preference,
                    "teacher_respect_level": zpd_range.cultural_context.teacher_respect_level,
                    "family_involvement": zpd_range.cultural_context.family_involvement,
                    "peer_competition": zpd_range.cultural_context.peer_competition,
                },
                "maarif_alignment": {
                    "overall_alignment": zpd_range.maarif_alignment.overall_alignment,
                    "national_values_alignment": zpd_range.maarif_alignment.national_values_alignment,
                    "universal_values_alignment": zpd_range.maarif_alignment.universal_values_alignment,
                    "root_values_alignment": zpd_range.maarif_alignment.root_values_alignment,
                    "aligned_values": [
                        v.value for v in zpd_range.maarif_alignment.aligned_values
                    ],
                },
                "calculated_at": zpd_range.calculated_at.isoformat(),
            },
            message=f"[ROCKET] DEVRİMSEL ZPD hesaplandı! Optimal zorluk: {zpd_range.optimal_challenge:.2f}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/revolutionary/recommend", response_model=ZPDResponse)
async def generate_revolutionary_recommendation(
    request: RevolutionaryRecommendationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: ZPD tabanlı kişiselleştirilmiş öğrenme önerisi

    Türk kültürü faktörleri ile optimize edilmiş öğrenme önerileri sunar.
    """
    try:
        recommendation = await zpd_service.generate_revolutionary_recommendation(
            student_id=request.student_id,
            subject=request.subject,
            current_level=request.current_level,
            behavioral_data=request.behavioral_data,
            learning_objective=request.learning_objective,
            content_description=request.content_description,
            family_survey=request.family_survey,
        )

        return ZPDResponse(
            success=True,
            data={
                "student_id": recommendation.student_id,
                "subject": recommendation.subject,
                "recommended_difficulty": recommendation.recommended_difficulty,
                "learning_mode": recommendation.learning_mode,
                "content_type": recommendation.content_type,
                "teacher_guidance_level": recommendation.teacher_guidance_level,
                "peer_support_level": recommendation.peer_support_level,
                "maarif_integration": [
                    v.value for v in recommendation.maarif_integration
                ],
                "reasoning": recommendation.reasoning,
                "confidence_score": recommendation.confidence_score,
            },
            message=f"[ROCKET] DEVRİMSEL öneri oluşturuldu! Mod: {recommendation.learning_mode}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/revolutionary/cultural-context", response_model=ZPDResponse)
async def detect_cultural_context(
    request: LearningBalanceRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: Türk öğrenci kültürel bağlam tespiti

    Öğrencinin Türk kültürü faktörlerini analiz eder.
    """
    try:
        cultural_context = await zpd_service.detect_cultural_context_revolutionary(
            student_id=request.student_id, behavioral_data=request.behavioral_data
        )

        return ZPDResponse(
            success=True,
            data={
                "student_id": cultural_context.student_id,
                "group_learning_preference": cultural_context.group_learning_preference,
                "teacher_respect_level": cultural_context.teacher_respect_level,
                "family_involvement": cultural_context.family_involvement,
                "peer_competition": cultural_context.peer_competition,
                "authority_acceptance": cultural_context.authority_acceptance,
                "collective_success": cultural_context.collective_success,
                "elder_wisdom_value": cultural_context.elder_wisdom_value,
                "social_harmony": cultural_context.social_harmony,
                "detected_at": cultural_context.detected_at.isoformat(),
            },
            message="[ROCKET] DEVRİMSEL kültürel bağlam tespit edildi!",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/revolutionary/adapt-difficulty", response_model=ZPDResponse)
async def adapt_difficulty_culturally(
    request: CulturalAdaptationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: Kültürel faktörlere göre zorluk adaptasyonu

    Türk öğrenci davranış kalıplarına göre zorluk seviyesini dinamik olarak ayarlar.
    """
    try:
        adapted_difficulty = (
            await zpd_service.adapt_difficulty_culturally_revolutionary(
                student_id=request.student_id,
                current_difficulty=request.current_difficulty,
                student_performance=request.student_performance,
                behavioral_data=request.behavioral_data,
            )
        )

        return ZPDResponse(
            success=True,
            data={
                "student_id": request.student_id,
                "original_difficulty": request.current_difficulty,
                "adapted_difficulty": adapted_difficulty,
                "adaptation_factor": adapted_difficulty / request.current_difficulty,
                "performance_factors": request.student_performance,
            },
            message=f"[ROCKET] DEVRİMSEL zorluk adaptasyonu: {request.current_difficulty:.2f} → {adapted_difficulty:.2f}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/revolutionary/maarif-alignment", response_model=ZPDResponse)
async def calculate_maarif_alignment(
    request: MaarifAlignmentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: MEB Maarif değerleri uyum analizi

    İçeriğin MEB Maarif değerleri ile uyumunu analiz eder.
    """
    try:
        alignment = await zpd_service.calculate_maarif_alignment_revolutionary(
            subject=request.subject, content_description=request.content_description
        )

        return ZPDResponse(
            success=True,
            data={
                "subject": alignment.subject,
                "national_values_alignment": alignment.national_values_alignment,
                "universal_values_alignment": alignment.universal_values_alignment,
                "root_values_alignment": alignment.root_values_alignment,
                "overall_alignment": alignment.overall_alignment,
                "aligned_values": [v.value for v in alignment.aligned_values],
            },
            message=f"[ROCKET] DEVRİMSEL Maarif uyumu: {alignment.overall_alignment:.2f}",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/revolutionary/learning-balance", response_model=ZPDResponse)
async def get_learning_balance(
    request: LearningBalanceRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: Grup vs bireysel öğrenme dengesi analizi

    Türk kültürü faktörleri ile optimize edilmiş öğrenme dengesi analizi.
    """
    try:
        balance_info = await zpd_service.get_revolutionary_learning_balance(
            student_id=request.student_id, behavioral_data=request.behavioral_data
        )

        return ZPDResponse(
            success=True,
            data=balance_info,
            message=f"[ROCKET] DEVRİMSEL öğrenme dengesi: {balance_info['recommended_mode']}",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/revolutionary/cultural-patterns", response_model=ZPDResponse)
async def monitor_cultural_patterns(
    request: CulturalPatternAnalysisRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    [ROCKET] DEVRİMSEL: Kültürel öğrenme kalıpları analizi

    Türk öğrenci davranış kalıplarının derinlemesine analizi.
    """
    try:
        patterns = await zpd_service.monitor_cultural_learning_patterns_revolutionary(
            student_id=request.student_id, learning_sessions=request.learning_sessions
        )

        return ZPDResponse(
            success=True,
            data=patterns,
            message="[ROCKET] DEVRİMSEL kültürel kalıp analizi tamamlandı",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/revolutionary/demo/{student_id}", response_model=ZPDResponse)
async def revolutionary_demo(
    student_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    [ROCKET] DEVRİMSEL DEMO: Tüm devrimsel özelliklerin demo gösterimi

    Bu endpoint tüm devrimsel özellikleri örnek verilerle gösterir.
    """
    _verify_student_access(current_user, student_id)
    try:
        # Örnek davranışsal veri
        sample_behavioral_data = {
            "group_study_sessions": 15,
            "individual_study_sessions": 8,
            "teacher_question_count": 12,
            "peer_interaction_count": 25,
            "help_seeking_frequency": 10,
            "video_watch_time": 120,
            "text_reading_time": 90,
            "interactive_engagement": 35,
            "quiz_completion_rate": 0.85,
            "hands_on_performance": 0.78,
            "visual_content_performance": 0.82,
            "auditory_content_performance": 0.75,
            "text_content_performance": 0.80,
            "note_taking_frequency": 8,
        }

        # Örnek aile anketi
        sample_family_survey = {
            "involvement_level": 0.8,
            "collective_focus": 0.7,
            "elder_respect": 0.9,
            "harmony_importance": 0.85,
        }

        # 1. Kültürel bağlam tespiti
        cultural_context = await zpd_service.detect_cultural_context_revolutionary(
            student_id=student_id,
            behavioral_data=sample_behavioral_data,
            family_survey=sample_family_survey,
        )

        # 2. ZPD hesaplama
        zpd_range = await zpd_service.calculate_revolutionary_zpd(
            student_id=student_id,
            subject="matematik",
            current_level=6.5,
            behavioral_data=sample_behavioral_data,
            content_description="Türk matematikçilerin katkıları ve geometri",
            family_survey=sample_family_survey,
        )

        # 3. Öneri oluşturma
        recommendation = await zpd_service.generate_revolutionary_recommendation(
            student_id=student_id,
            subject="matematik",
            current_level=6.5,
            behavioral_data=sample_behavioral_data,
            learning_objective="Geometri konusunda uzmanlaşma",
            content_description="Türk matematikçilerin katkıları ve geometri",
            family_survey=sample_family_survey,
        )

        # 4. Öğrenme dengesi
        balance_info = await zpd_service.get_revolutionary_learning_balance(
            student_id=student_id, behavioral_data=sample_behavioral_data
        )

        return ZPDResponse(
            success=True,
            data={
                "demo_title": "[ROCKET] DEVRİMSEL ZPD + MEB MAAİF SİSTEMİ DEMO",
                "student_id": student_id,
                "cultural_context": {
                    "group_learning_preference": cultural_context.group_learning_preference,
                    "teacher_respect_level": cultural_context.teacher_respect_level,
                    "family_involvement": cultural_context.family_involvement,
                    "social_harmony": cultural_context.social_harmony,
                },
                "zpd_calculation": {
                    "current_level": zpd_range.current_level,
                    "optimal_challenge": zpd_range.optimal_challenge,
                    "group_individual_balance": zpd_range.group_individual_balance,
                    "maarif_alignment": zpd_range.maarif_alignment.overall_alignment,
                },
                "recommendation": {
                    "learning_mode": recommendation.learning_mode,
                    "recommended_difficulty": recommendation.recommended_difficulty,
                    "content_type": recommendation.content_type,
                    "reasoning": recommendation.reasoning,
                    "confidence_score": recommendation.confidence_score,
                },
                "learning_balance": balance_info,
                "revolutionary_features": [
                    "[CHECK] Türk kültürü faktörleri entegrasyonu",
                    "[CHECK] MEB Maarif değerleri uyum sistemi",
                    "[CHECK] Grup vs bireysel öğrenme dengeleme",
                    "[CHECK] Kültürel bağlam farkındalıklı ZPD hesaplama",
                    "[CHECK] Gerçek zamanlı kültürel adaptasyon",
                ],
            },
            message="[ROCKET] DEVRİMSEL ZPD + MEB MAAİF sistemi başarıyla gösterildi!",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
