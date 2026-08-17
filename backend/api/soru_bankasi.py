"""
Soru Bankası API Endpoint'leri
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import hashlib
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.ddos_protection import limiter
from core.dependencies import AuthenticatedUser, get_current_user
from core.multi_layer_cache import MultiLayerCache
from models.enums_db import UserRole
from services.soru_bankasi_service import soru_bankasi_servisi

# `logger` atamasi ONCEDEN import'larin ARASINDA duruyordu ve 10 adet E402
# uretiyordu (kapi borcu; hook yalniz DEGISEN dosyaya baktigi icin bu turda
# gorunur oldu). Asagi tasindi: modul duzeyinde import'lardan once HIC
# kullanilmiyor (olculdu), yani davranis notr.
logger = logging.getLogger(__name__)

PATTERN_UUID_OR_TEST = r"^(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[a-zA-Z0-9_-]{1,36})$"

router = APIRouter(tags=["Soru Bankası"])

# Initialize multi-layer cache for question bank
# L1: Memory (100 entries), L2: Redis, TTL: 1 hour
question_cache = MultiLayerCache(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    l1_max_size=100,
    default_ttl=3600,
    namespace="soru_bankasi",
)


async def invalidate_question_cache():
    """Soru bankası cache'ini temizle"""
    try:
        await question_cache.clear()
        logger.info("Cache temizlendi: soru_bankasi namespace")
    except Exception as e:
        logger.warning(f"Cache temizleme hatası: {e}")


@router.get("/sorular", response_model=list[dict[str, Any]])
@limiter.limit("30/minute")
async def sorular_listele(
    request: Request,
    sinav_tipi: str | None = Query(None, description="Sınav türü (TYT, AYT, YDT)"),
    konu: str | None = Query(None, description="Konu filtresi"),
    zorluk_seviyesi: str | None = Query(
        None, description="Zorluk seviyesi (easy, medium, hard)"
    ),
    limit: int = Query(100, ge=1, le=500, description="Maksimum soru sayısı"),
    offset: int = Query(0, ge=0, description="Başlangıç offset'i"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Filtrelere göre soru listesi getir

    - **sinav_tipi**: Sınav türü filtresi
    - **konu**: Konu filtresi
    - **zorluk_seviyesi**: Zorluk seviyesi filtresi
    - **limit**: Maksimum soru sayısı
    - **offset**: Sayfalama için offset

    PERFORMANCE: Multi-layer cache enabled (L1 Memory + L2 Redis)
    - Cache TTL: 1 hour
    - Expected hit rate: 70-80%
    - Response time: <100ms (cached) vs 500-1000ms (uncached)
    """
    try:
        # Generate cache key from query parameters
        # `usedforsecurity=False`: bu bir CACHE ANAHTARI, guvenlik ozeti degil.
        # Kapi borcu (S324/B324), dokunulmayan kod — davranis notr, hash ayni.
        cache_key = hashlib.md5(
            json.dumps(
                {
                    "sinav_tipi": sinav_tipi,
                    "konu": konu,
                    "zorluk_seviyesi": zorluk_seviyesi,
                    "limit": limit,
                    "offset": offset,
                },
                sort_keys=True,
            ).encode(),
            usedforsecurity=False,
        ).hexdigest()

        # Initialize cache if needed
        if not question_cache._initialized:
            await question_cache.initialize()

        # Try to get from cache (L1 → L2 → Database)
        async def fetch_questions():
            """Fetch questions from database and convert to JSON-serializable dicts"""
            sorular = await soru_bankasi_servisi.sorular_listele(
                sinav_tipi=sinav_tipi,
                konu=konu,
                zorluk_seviyesi=zorluk_seviyesi,
                limit=limit,
                offset=offset,
            )
            # Convert SQLAlchemy objects to JSON-serializable dicts for caching
            soru_listesi = []
            for soru in sorular:
                soru_dict = {
                    "id": soru.id,
                    "question_text": soru.question_text,
                    "options": {
                        "A": soru.option_a,
                        "B": soru.option_b,
                        "C": soru.option_c,
                        "D": soru.option_d,
                        "E": soru.option_e,
                    },
                    "correct_answer": soru.correct_answer,
                    "explanation": soru.explanation,
                    "exam_type": str(soru.exam_type),
                    "subject_area": str(soru.subject_area),
                    "topic": soru.primary_topic_id,
                    "subtopic": None,
                    "difficulty": soru.difficulty_level.value
                    if soru.difficulty_level
                    else "MEDIUM",
                    "irt_parameters": {
                        "difficulty": soru.irt_difficulty,
                        "discrimination": soru.irt_discrimination,
                        "guessing": soru.irt_guessing,
                    },
                    "morphology_complexity": soru.morphology_complexity,
                    "readability_score": soru.readability_score,
                    "statistics": {
                        "times_asked": soru.times_asked,
                        "times_correct": soru.times_correct,
                        "success_rate": soru.times_correct / max(1, soru.times_asked),
                        "average_response_time": soru.average_response_time,
                    },
                    "created_at": soru.created_at.isoformat()
                    if soru.created_at
                    else None,
                    "is_active": soru.is_active,
                }
                soru_listesi.append(soru_dict)
            return soru_listesi

        # Get or compute with cache
        soru_listesi = await question_cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_questions,
            ttl=3600,  # 1 hour
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": soru_listesi,
                "count": len(soru_listesi),
                "message": f"{len(soru_listesi)} soru başarıyla getirildi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/soru/{soru_id}", response_model=dict[str, Any])
async def soru_detay(
    soru_id: str = Path(..., pattern=PATTERN_UUID_OR_TEST),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Belirli bir sorunun detaylarını getir

    - **soru_id**: Soru ID'si
    """
    try:
        soru = await soru_bankasi_servisi.soru_getir(soru_id)

        if not soru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        soru_detay = {
            "id": soru.id,
            "question_text": soru.question_text,
            "question_image_url": soru.question_image_url,
            "options": {
                "A": soru.option_a,
                "B": soru.option_b,
                "C": soru.option_c,
                "D": soru.option_d,
                "E": soru.option_e,
            },
            "correct_answer": soru.correct_answer,
            "explanation": soru.explanation,
            "exam_type": str(soru.exam_type),
            "subject_area": str(soru.subject_area),
            "topic": soru.primary_topic_id,
            "subtopic": None,
            "difficulty": soru.difficulty_level.value
            if soru.difficulty_level
            else "MEDIUM",
            "irt_parameters": {
                "difficulty": soru.irt_difficulty,
                "discrimination": soru.irt_discrimination,
                "guessing": soru.irt_guessing,
            },
            "morphology_complexity": soru.morphology_complexity,
            "readability_score": soru.readability_score,
            "statistics": {
                "times_asked": soru.times_asked,
                "times_correct": soru.times_correct,
                "success_rate": soru.times_correct / max(1, soru.times_asked),
                "average_response_time": soru.average_response_time,
            },
            "created_at": soru.created_at.isoformat(),
            "updated_at": soru.updated_at.isoformat(),
            "is_active": soru.is_active,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": soru_detay,
                "message": "Soru detayları başarıyla getirildi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/rastgele-sorular", response_model=dict[str, Any])
async def rastgele_sorular_sec(
    sinav_tipi: str = Query(..., description="Sınav türü (TYT, AYT, YDT)"),
    soru_sayisi: int = Query(..., ge=1, le=200, description="Seçilecek soru sayısı"),
    konu_dagilimi: str | None = Query(None, description="Konu dağılımı (JSON string)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Rastgele soru seçimi yap - Redis cached (30s TTL)

    - **sinav_tipi**: Sınav türü (TYT, AYT, YDT)
    - **soru_sayisi**: Seçilecek soru sayısı
    - **konu_dagilimi**: Konu bazlı dağılım (opsiyonel, JSON string)
    """
    import hashlib

    from core.redis_cache import get_cache

    try:
        # Sınav türü validasyonu
        if sinav_tipi not in ["TYT", "AYT", "YDT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz sınav türü. TYT, AYT veya YDT olmalı.",
            )

        # JSON string'i Dict'e dönüştür
        konu_dagilimi_dict = None
        if konu_dagilimi:
            import json

            try:
                konu_dagilimi_dict = json.loads(konu_dagilimi)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geçersiz JSON formatı",
                )

        # Generate cache key based on parameters
        cache_key_parts = [sinav_tipi, str(soru_sayisi)]
        if konu_dagilimi:
            # Hash the konu_dagilimi for cache key
            # Cache anahtari, guvenlik ozeti degil (bkz. yukaridaki not).
            konu_hash = hashlib.md5(
                konu_dagilimi.encode(), usedforsecurity=False
            ).hexdigest()[:8]
            cache_key_parts.append(konu_hash)
        cache_key = f"random_questions:{':'.join(cache_key_parts)}"

        # Try to get from cache
        cache = get_cache()
        if cache.is_connected():
            cached_result = cache.get(cache_key)  # Sync method, no await
            if cached_result:
                logger.info(f"✅ Cache HIT for {cache_key}")
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content=cached_result
                )
            logger.info(f"❌ Cache MISS for {cache_key}")

        sorular = await soru_bankasi_servisi.rastgele_sorular_sec(
            sinav_tipi=sinav_tipi,
            soru_sayisi=soru_sayisi,
            konu_dagilimi=konu_dagilimi_dict,
        )

        # Response formatına dönüştür - Soru modeli için Turkish column mapping
        secilen_sorular = []
        # Anotasyon ONCEDEN VAR OLAN kapi borcu (HEAD'de bayt-birebir ayni satir);
        # mypy hook'u yalniz DEGISEN dosyalara baktigi icin bu turda gorunur oldu.
        # Davranis DEGISMIYOR: deger `.get(konu, 0) + 1` ile int sayac, anahtar
        # `soru.konu` (konu adi, str). Dokunulmayan koda ait tek satirlik anotasyon.
        konu_sayaclari: dict[str, int] = {}

        for soru in sorular:
            soru_dict = {
                "id": str(soru.id),
                "kod": soru.kod,
                "question_text": soru.metin,  # Turkish: metin
                "options": soru.secenekler,  # Turkish: secenekler (already a dict)
                "correct_answer": soru.dogru_cevap,  # Turkish: dogru_cevap
                "subject_area": soru.konu,  # Turkish: konu (string, not enum)
                "exam_type": soru.sinav_tipi,  # Turkish: sinav_tipi
                "difficulty": soru.zorluk if soru.zorluk else "orta",  # Turkish: zorluk
                "irt_difficulty": soru.irt_difficulty,
            }
            secilen_sorular.append(soru_dict)

            # Konu sayacını güncelle
            konu = soru.konu
            konu_sayaclari[konu] = konu_sayaclari.get(konu, 0) + 1

        # Prepare response
        response_data = {
            "success": True,
            "data": {
                "sorular": secilen_sorular,
                "secilen_soru_sayisi": len(secilen_sorular),
                "istenen_soru_sayisi": soru_sayisi,
                "konu_dagilimi": konu_sayaclari,
            },
            "message": f"{len(secilen_sorular)} soru başarıyla seçildi",
        }

        # Cache for 30 seconds
        if cache.is_connected():
            cache.set(cache_key, response_data, ttl=30)  # Sync method, no await
            logger.info(f"💾 Cache SET for {cache_key} (TTL: 30s)")

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_data)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/irt-parametreli-sorular", response_model=dict[str, Any])
async def irt_parametreli_sorular_sec(
    ogrenci_yetenek: float = Query(
        ..., ge=-3.0, le=3.0, description="Öğrenci yetenek parametresi"
    ),
    sinav_tipi: str = Query(..., description="Sınav türü"),
    soru_sayisi: int = Query(..., ge=1, le=100, description="Seçilecek soru sayısı"),
    hedef_bilgi: float = Query(
        1.0, ge=0.1, le=5.0, description="Hedef bilgi fonksiyonu değeri"
    ),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    IRT parametreli adaptif soru seçimi

    - **ogrenci_yetenek**: Öğrenci yetenek parametresi (-3 ile +3 arası)
    - **sinav_tipi**: Sınav türü
    - **soru_sayisi**: Seçilecek soru sayısı
    - **hedef_bilgi**: Hedef bilgi fonksiyonu değeri
    """
    try:
        sorular = await soru_bankasi_servisi.irt_parametreli_soru_sec(
            ogrenci_yetenek=ogrenci_yetenek,
            sinav_tipi=sinav_tipi,
            soru_sayisi=soru_sayisi,
            hedef_bilgi=hedef_bilgi,
        )

        # Response formatına dönüştür
        adaptif_sorular = []
        bilgi_degerleri = []

        for soru in sorular:
            # Bilgi değerini hesapla
            bilgi_degeri = await soru_bankasi_servisi._hesapla_bilgi_fonksiyonu(
                ogrenci_yetenek,
                soru.irt_difficulty,
                soru.irt_discrimination,
                soru.irt_guessing,
            )

            soru_dict = {
                "id": soru.id,
                "question_text": soru.question_text,
                "options": {
                    "A": soru.option_a,
                    "B": soru.option_b,
                    "C": soru.option_c,
                    "D": soru.option_d,
                    "E": soru.option_e,
                },
                "subject_area": str(soru.subject_area),
                "topic": soru.primary_topic_id,
                "difficulty": soru.difficulty_level.value
                if soru.difficulty_level
                else "MEDIUM",
                "irt_parameters": {
                    "difficulty": soru.irt_difficulty,
                    "discrimination": soru.irt_discrimination,
                    "guessing": soru.irt_guessing,
                },
                "information_value": bilgi_degeri,
                "difficulty_match": abs(soru.irt_difficulty - ogrenci_yetenek),
            }
            adaptif_sorular.append(soru_dict)
            bilgi_degerleri.append(bilgi_degeri)

        # İstatistikler
        ortalama_bilgi = (
            sum(bilgi_degerleri) / len(bilgi_degerleri) if bilgi_degerleri else 0
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "sorular": adaptif_sorular,
                    "secilen_soru_sayisi": len(adaptif_sorular),
                    "ogrenci_yetenek": ogrenci_yetenek,
                    "ortalama_bilgi_degeri": ortalama_bilgi,
                    "adaptasyon_kalitesi": "yüksek"
                    if ortalama_bilgi > 1.0
                    else "orta"
                    if ortalama_bilgi > 0.5
                    else "düşük",
                },
                "message": f"IRT parametreli {len(adaptif_sorular)} soru başarıyla seçildi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/konular", response_model=list[str])
async def konu_listesi_getir(
    sinav_tipi: str | None = Query(None, description="Sınav türü filtresi"),
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Mevcut konuları listele

    - **sinav_tipi**: Sınav türü filtresi (opsiyonel)
    """
    try:
        konular = await soru_bankasi_servisi.konu_listesi_getir(sinav_tipi)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": konular,
                "count": len(konular),
                "message": f"{len(konular)} konu başarıyla getirildi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/istatistikler", response_model=dict[str, Any])
async def soru_bankasi_istatistikleri(
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Soru bankası istatistiklerini getir
    """
    try:
        istatistikler = await soru_bankasi_servisi.istatistikler_getir()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": istatistikler,
                "message": "İstatistikler başarıyla getirildi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/soru-performans-guncelle", response_model=dict[str, Any])
async def soru_performans_guncelle(
    soru_id: str,
    dogru_cevap: bool,
    cevap_suresi: float = Query(..., ge=0.1, description="Cevaplama süresi (saniye)"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Soru performans istatistiklerini güncelle

    - **soru_id**: Soru ID'si
    - **dogru_cevap**: Cevap doğru mu
    - **cevap_suresi**: Cevaplama süresi (saniye)
    """
    try:
        basarili = await soru_bankasi_servisi.soru_performans_guncelle(
            soru_id=soru_id, dogru_cevap=dogru_cevap, cevap_suresi=cevap_suresi
        )

        if not basarili:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soru bulunamadı veya güncelleme başarısız",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "soru_id": soru_id,
                    "dogru_cevap": dogru_cevap,
                    "cevap_suresi": cevap_suresi,
                    "guncelleme_zamani": "şimdi",
                },
                "message": "Soru performansı başarıyla güncellendi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/zorluk-filtrele", response_model=dict[str, Any])
async def zorluk_seviyesi_filtrele(
    ogrenci_yetenek: float = Query(
        ..., ge=-3.0, le=3.0, description="Öğrenci yetenek seviyesi"
    ),
    sinav_tipi: str = Query(..., description="Sınav türü"),
    tolerans: float = Query(1.0, ge=0.1, le=2.0, description="Zorluk toleransı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Öğrenci yetenek seviyesine göre uygun zorlukta sorular filtrele

    - **ogrenci_yetenek**: Öğrenci yetenek parametresi
    - **sinav_tipi**: Sınav türü
    - **tolerans**: Zorluk toleransı (±)
    """
    try:
        sorular = await soru_bankasi_servisi.zorluk_seviyesi_filtrele(
            ogrenci_yetenek=ogrenci_yetenek, sinav_tipi=sinav_tipi, tolerans=tolerans
        )

        # Response formatına dönüştür
        uygun_sorular = []
        for soru in sorular:
            soru_dict = {
                "id": soru.id,
                "question_text": soru.question_text,
                "subject_area": str(soru.subject_area),
                "topic": soru.primary_topic_id,
                "difficulty": soru.difficulty_level.value
                if soru.difficulty_level
                else "MEDIUM",
                "irt_difficulty": soru.irt_difficulty,
                "irt_discrimination": soru.irt_discrimination,
                "difficulty_match": abs(soru.irt_difficulty - ogrenci_yetenek),
                "recommended": abs(soru.irt_difficulty - ogrenci_yetenek) <= tolerans,
            }
            uygun_sorular.append(soru_dict)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "sorular": uygun_sorular,
                    "toplam_soru": len(uygun_sorular),
                    "ogrenci_yetenek": ogrenci_yetenek,
                    "tolerans": tolerans,
                    "zorluk_araligi": {
                        "min": ogrenci_yetenek - tolerans,
                        "max": ogrenci_yetenek + tolerans,
                    },
                },
                "message": f"Yetenek seviyesine uygun {len(uygun_sorular)} soru bulundu",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# Servisle tam uyumlu ek endpoint'ler


# duruyor ve yukari tasimak dosyanin bolum duzenini bozar. Dokunulmayan kod.
from pydantic import BaseModel, Field, model_validator  # noqa: E402


class SoruEkleRequest(BaseModel):
    """Soru ekleme isteği"""

    soru_metni: str = Field(
        ..., min_length=10, max_length=5000, description="Soru metni"
    )
    secenekler: list[str] = Field(
        ..., min_length=4, max_length=5, description="Seçenekler listesi"
    )
    dogru_cevap: str = Field(
        ..., pattern=r"^[A-Ea-e]$", description="Doğru cevap (A, B, C, D veya E)"
    )
    cozum_aciklamasi: str | None = Field(
        None, max_length=10000, description="Çözüm açıklaması"
    )
    sinav_tipi: str = Field("TYT", max_length=10, description="Sınav tipi")
    konu: str = Field(..., max_length=200, description="Konu")
    alt_konu: str | None = Field(None, max_length=200, description="Alt konu")
    zorluk_seviyesi: str = Field("orta", max_length=20, description="Zorluk seviyesi")
    created_by: str | None = Field(
        None, max_length=100, description="Oluşturan kullanıcı"
    )
    soru_hash: str | None = Field(None, description="Soru hash değeri")

    @model_validator(mode="before")
    @classmethod
    def calculate_canonical_hash(cls, data: Any) -> Any:
        if isinstance(data, dict):
            soru_metni = data.get("soru_metni", "")
            secenekler = data.get("secenekler", [])

            if soru_metni and isinstance(secenekler, list):
                import hashlib
                import re

                # Canonicalize question text
                # 1. Clean HTML tags (preserving LaTeX formulas)
                cleaned_text = re.sub(r"<[^>]+>", "", soru_metni)
                # 2. Clean ZWSP and invisible spaces
                for space_char in ["\u200b", "\u200c", "\u200d", "\ufeff"]:
                    cleaned_text = cleaned_text.replace(space_char, "")
                # 3. Normalize consecutive whitespaces to a single space
                cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
                # 4. Convert to lowercase
                cleaned_text = cleaned_text.lower()

                # Canonicalize options (up to 5 options)
                cleaned_opts = []
                for opt in secenekler[:5]:
                    if isinstance(opt, str):
                        opt_cleaned = re.sub(r"<[^>]+>", "", opt)
                        for space_char in ["\u200b", "\u200c", "\u200d", "\ufeff"]:
                            opt_cleaned = opt_cleaned.replace(space_char, "")
                        opt_cleaned = re.sub(r"\s+", " ", opt_cleaned).strip()
                        opt_cleaned = opt_cleaned.lower()
                        # Strip standard option prefix like 'a) ', 'b) ' if any
                        opt_cleaned = re.sub(r"^[a-e]\)\s*", "", opt_cleaned)
                        cleaned_opts.append(opt_cleaned)
                    else:
                        cleaned_opts.append("")

                # Construct canonical hash input
                hash_input = cleaned_text
                for opt in cleaned_opts:
                    hash_input += "|" + opt
                if len(cleaned_opts) < 5:
                    hash_input += "|"

                # Compute SHA-256 hash and slice to 32 chars to fit VARCHAR(32)
                data["soru_hash"] = hashlib.sha256(
                    hash_input.encode("utf-8")
                ).hexdigest()[:32]
        return data


class SoruGuncelleRequest(BaseModel):
    """Soru güncelleme isteği"""

    soru_metni: str | None = Field(None, min_length=10, max_length=5000)
    secenekler: list[str] | None = Field(None, min_length=4, max_length=5)
    dogru_cevap: str | None = Field(None, pattern=r"^[A-Ea-e]$")
    cozum_aciklamasi: str | None = Field(None, max_length=10000)
    zorluk_seviyesi: str | None = Field(None, max_length=20)


class TopluSoruEkleRequest(BaseModel):
    """Toplu soru ekleme isteği"""

    sorular: list[dict[str, Any]] = Field(..., description="Soru listesi")


@router.post("/soru-ekle", response_model=dict[str, Any])
async def soru_ekle(
    request: SoruEkleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Yeni soru ekle

    Soru metni, seçenekler ve diğer bilgilerle yeni soru oluşturur.
    IRT parametreleri ve morfoloji karmaşıklığı otomatik hesaplanır.
    """
    try:
        soru_data = {
            "soru_metni": request.soru_metni,
            "secenekler": request.secenekler,
            "dogru_cevap": request.dogru_cevap,
            "cozum_aciklamasi": request.cozum_aciklamasi,
            "sinav_tipi": request.sinav_tipi,
            "konu": request.konu,
            "alt_konu": request.alt_konu,
            "zorluk_seviyesi": request.zorluk_seviyesi,
            "created_by": current_user.id,
            "soru_hash": request.soru_hash,
        }

        yeni_soru = await soru_bankasi_servisi.soru_ekle(soru_data)

        # Cache invalidation
        await invalidate_question_cache()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": {
                    # #485 — alanlar PARENT'tan DEGIL yavru tablolardan okunur.
                    # Parent uzerinden okumak (`yeni_soru.question_text`) strangler
                    # devredicisine duser; oturum kapandigi icin lazy-load
                    # `DetachedInstanceError` verir, `except Exception` yutar ve
                    # kullanici HTTP 500 gorur — soru ise ZATEN yazilmis olur.
                    # `str(...)` de kaldirildi: exam_type/subject_area split sonrasi
                    # duz `str`; `str()` bir enum uyesine uygulanirsa Python 3.13'te
                    # 'ExamType.TYT' uretir (olculdu).
                    "id": yeni_soru.id,
                    "question_text": yeni_soru.content.question_text,
                    "exam_type": yeni_soru.metadata_info.exam_type,
                    "subject_area": yeni_soru.metadata_info.subject_area,
                    "difficulty": yeni_soru.statistics.difficulty_level.name
                    if yeni_soru.statistics.difficulty_level
                    else "MEDIUM",
                    "irt_parameters": {
                        "difficulty": yeni_soru.statistics.irt_difficulty,
                        "discrimination": yeni_soru.statistics.irt_discrimination,
                        "guessing": yeni_soru.statistics.irt_guessing,
                    },
                    "morphology_complexity": yeni_soru.metadata_info.morphology_complexity,
                    "readability_score": yeni_soru.metadata_info.readability_score,
                },
                "message": "Soru başarıyla eklendi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/soru-guncelle/{soru_id}", response_model=dict[str, Any])
async def soru_guncelle(
    soru_id: str,
    request: SoruGuncelleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Mevcut soruyu güncelle (admin/teacher only)

    - **soru_id**: Güncellenecek soru ID'si
    """
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.TEACHER,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin yetkiniz yok",
        )
    try:
        # Güncelleme verilerini hazırla
        guncelleme_verisi = {}

        if request.soru_metni:
            guncelleme_verisi["question_text"] = request.soru_metni

        # `and`e indirgenebilir ama bu blok bu turda DEGISTIRILMEDI; birlestirmek
        # dokunulmayan kodda gereksiz risk olurdu (cerrahi mudahale kurali).
        if request.secenekler:  # noqa: SIM102
            if len(request.secenekler) >= 4:
                guncelleme_verisi["option_a"] = request.secenekler[0].replace("A) ", "")
                guncelleme_verisi["option_b"] = request.secenekler[1].replace("B) ", "")
                guncelleme_verisi["option_c"] = request.secenekler[2].replace("C) ", "")
                guncelleme_verisi["option_d"] = request.secenekler[3].replace("D) ", "")
                if len(request.secenekler) > 4:
                    guncelleme_verisi["option_e"] = request.secenekler[4].replace(
                        "E) ", ""
                    )
        if request.dogru_cevap:
            guncelleme_verisi["correct_answer"] = request.dogru_cevap
        if request.cozum_aciklamasi:
            guncelleme_verisi["explanation"] = request.cozum_aciklamasi
        if request.zorluk_seviyesi:
            guncelleme_verisi["difficulty"] = request.zorluk_seviyesi

        guncellenmis_soru = await soru_bankasi_servisi.soru_guncelle(
            soru_id=soru_id, guncelleme_verisi=guncelleme_verisi
        )

        if not guncellenmis_soru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        # Cache invalidation
        await invalidate_question_cache()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "id": guncellenmis_soru.id,
                    "updated_fields": list(guncelleme_verisi.keys()),
                    "updated_at": guncellenmis_soru.updated_at.isoformat(),
                },
                "message": "Soru başarıyla güncellendi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/soru-sil/{soru_id}", response_model=dict[str, Any])
async def soru_sil(
    soru_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Soruyu sil (soft delete, admin/teacher only)

    - **soru_id**: Silinecek soru ID'si
    """
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.TEACHER,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin yetkiniz yok",
        )
    try:
        basarili = await soru_bankasi_servisi.soru_sil(soru_id)

        if not basarili:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {"soru_id": soru_id, "is_active": False},
                "message": "Soru başarıyla silindi (deaktif edildi)",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/toplu-soru-ekle", response_model=dict[str, Any])
async def toplu_soru_ekle(
    request: TopluSoruEkleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Toplu soru ekleme

    Birden fazla soruyu aynı anda ekler.
    """
    try:
        # Her soruda created_by ekle
        for soru in request.sorular:
            soru["created_by"] = current_user.id

        sonuc = await soru_bankasi_servisi.toplu_soru_ekle(request.sorular)

        # Cache invalidation
        await invalidate_question_cache()

        # Ham hata dizeleri istemciye GITMEZ. Servisin `hatalar` listesi
        # SQLAlchemy'nin tam istisna metnini tasiyor: INSERT deyiminin kendisi,
        # bind parametreleri ve `created_by` kullanici kimligi dahil (olculdu —
        # 0 soru eklenen bir cagrida hepsi govdede dondu). Tam metin sunucu
        # log'una yazilir, istemci yalnizca SAYIYI gorur.
        if sonuc.get("hatalar"):
            logger.error(
                "toplu_soru_ekle %d/%d basarisiz (kullanici=%s): %s",
                sonuc["basarisiz"],
                sonuc["toplam"],
                current_user.id,
                sonuc["hatalar"],
            )
        istemci_sonucu = {k: v for k, v in sonuc.items() if k != "hatalar"}
        istemci_sonucu["hata_sayisi"] = len(sonuc.get("hatalar") or [])

        # Hicbir soru eklenmediyse 201 CREATED YANLIS: hicbir kaynak
        # yaratilmadi. Onceki hali 0 soru eklenirken de 201 + "success": true
        # donuyordu, yani cagiran basarisizligi FARK EDEMIYORDU.
        tumu_basarisiz = sonuc["toplam"] > 0 and sonuc["basarili"] == 0
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            if tumu_basarisiz
            else status.HTTP_201_CREATED,
            content={
                "success": not tumu_basarisiz,
                "data": istemci_sonucu,
                "message": f"{sonuc['basarili']}/{sonuc['toplam']} soru başarıyla eklendi",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post(
    "/irt-parametreleri-yeniden-hesapla/{soru_id}", response_model=dict[str, Any]
)
async def irt_parametreleri_yeniden_hesapla(
    soru_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Soru IRT parametrelerini performans verilerine göre yeniden hesapla

    Minimum 10 cevap gereklidir.
    """
    try:
        basarili = await soru_bankasi_servisi.irt_parametrelerini_yeniden_hesapla(
            soru_id
        )

        if not basarili:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Soru bulunamadı veya yeterli veri yok (minimum 10 cevap gerekli)",
            )

        # Güncellenmiş soruyu getir
        soru = await soru_bankasi_servisi.soru_getir(soru_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "soru_id": soru_id,
                    "yeni_irt_parametreleri": {
                        "difficulty": soru.irt_difficulty,
                        "discrimination": soru.irt_discrimination,
                        "guessing": soru.irt_guessing,
                    },
                    "cevap_sayisi": soru.times_asked,
                    "basari_orani": soru.times_correct / max(1, soru.times_asked),
                },
                "message": "IRT parametreleri başarıyla yeniden hesaplandı",
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Soru Bankası API sağlık kontrolü
    """
    return {
        "success": True,
        "data": {
            "service": "Soru Bankası API",
            "status": "healthy",
            "version": "1.0.0",
            "features": [
                "IRT Parametreli Soru Seçimi",
                "Adaptif Zorluk Ayarlama",
                "Morfoloji Karmaşıklık Analizi",
                "Toplu Soru İşlemleri",
                "Performans İstatistikleri",
            ],
        },
        "message": "Soru Bankası Servisi çalışıyor",
    }
