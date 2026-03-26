"""
Öğrenci Dashboard API endpoint'leri
SPRINT 2: Multi-layer cache integration (L1 Memory + L2 Redis)
"""
import os
from typing import List, Optional
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import mevcut_kullanici_getir
from core.dependencies import get_db
from core.multi_layer_cache import MultiLayerCache
from core.structured_logger import get_logger
from models.dashboard import (
    Bildirim,
    DashboardIstatistikleri,
    Hedef,
    PerformansVerisi,
    ProfilGuncelleme,
    SinavSonucu,
)
from models.user import Kullanici, OgrenciProfili
from services.student_dashboard_service import ogrenci_dashboard_servisi

router = APIRouter(prefix="/api/v1/student-dashboard", tags=["Öğrenci Dashboard"])
logger = get_logger("student_dashboard_api")

# SPRINT 2: Multi-layer cache for student dashboard
# L1: Memory (30 entries), L2: Redis, TTL: 5-10 minutes
# Performance improvement: ~1500ms → 10-50ms (15-150x faster on cache hit)
dashboard_cache = MultiLayerCache(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    l1_max_size=30,  # Dashboard data is highly personalized, smaller L1
    default_ttl=600,  # 10 minutes default
    namespace="student_dashboard",
)


@router.get(
    "/istatistikler",
    response_model=DashboardIstatistikleri,
    summary="Dashboard İstatistikleri",
)
async def dashboard_istatistikleri_getir(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrenci dashboard ana sayfası için istatistikleri getir

    - Tamamlanan ders/sınav sayıları
    - Ortalama performans
    - Çalışma süreleri ve hedefler
    - Seviye ve deneyim bilgileri

    **SPRINT 2**: Multi-layer cache (L1+L2) - 5 min TTL
    Expected: 1500ms → 50ms (30x faster)
    """
    try:
        # SPRINT 2: Multi-layer cache key
        cache_key = f"stats:{mevcut_kullanici.kullanici_id}"

        # Initialize cache if needed
        if not dashboard_cache._initialized:
            await dashboard_cache.initialize()

        # Get or compute with cache (L1 → L2 → Database)
        async def fetch_stats():
            """Fetch statistics from service"""
            return await ogrenci_dashboard_servisi.dashboard_istatistikleri_getir(
                mevcut_kullanici.kullanici_id, db
            )

        istatistikler = await dashboard_cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_stats,
            ttl=300  # 5 minutes - frequently updated stats
        )

        return istatistikler
    except Exception as e:
        logger.error(f"Dashboard istatistikleri hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/sinav-gecmisi", response_model=List[SinavSonucu], summary="Sınav Geçmişi")
async def sinav_gecmisi_getir(
    limit: int = Query(20, ge=1, le=100, description="Sonuç sayısı limiti"),
    offset: int = Query(0, ge=0, description="Sayfalama offset'i"),
    sinav_tipi: Optional[str] = Query(None, description="Sınav türü filtresi"),
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrencinin sınav geçmişini getir

    - Sayfalama desteği
    - Sınav türüne göre filtreleme
    - Detaylı performans bilgileri

    **SPRINT 2**: Multi-layer cache (L1+L2) - 10 min TTL
    Expected: 800ms → 30ms (25x faster)
    """
    try:
        # SPRINT 2: Cache key from query parameters
        cache_key = hashlib.md5(
            json.dumps({
                "user_id": mevcut_kullanici.kullanici_id,
                "limit": limit,
                "offset": offset,
                "sinav_tipi": sinav_tipi,
            }, sort_keys=True).encode()
        ).hexdigest()

        # Initialize cache if needed
        if not dashboard_cache._initialized:
            await dashboard_cache.initialize()

        # Get or compute with cache
        async def fetch_history():
            """Fetch exam history from service"""
            return await ogrenci_dashboard_servisi.sinav_gecmisi_getir(
                kullanici_id=mevcut_kullanici.kullanici_id,
                db=db,
                limit=limit,
                offset=offset,
                sinav_tipi=sinav_tipi,
            )

        sinav_gecmisi = await dashboard_cache.get_or_compute(
            key=f"history:{cache_key}",
            compute_fn=fetch_history,
            ttl=600  # 10 minutes - history data doesn't change frequently
        )

        return sinav_gecmisi
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/performans-trendi",
    response_model=List[PerformansVerisi],
    summary="Performans Trendi",
)
async def performans_trendi_getir(
    gun_sayisi: int = Query(30, ge=7, le=365, description="Kaç günlük veri"),
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrencinin performans trendini getir

    - Günlük performans verileri
    - Grafik görselleştirme için uygun format
    - Çalışma süresi ve puan trendleri

    **SPRINT 2**: Multi-layer cache (L1+L2) - 10 min TTL
    Expected: 1200ms → 40ms (30x faster)
    """
    try:
        # SPRINT 2: Multi-layer cache key
        cache_key = f"trend:{mevcut_kullanici.kullanici_id}:{gun_sayisi}"

        # Initialize cache if needed
        if not dashboard_cache._initialized:
            await dashboard_cache.initialize()

        # Get or compute with cache (L1 → L2 → Database)
        async def fetch_trend():
            """Fetch performance trend from service"""
            return await ogrenci_dashboard_servisi.performans_trendi_getir(
                kullanici_id=mevcut_kullanici.kullanici_id, db=db, gun_sayisi=gun_sayisi
            )

        performans_verisi = await dashboard_cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_trend,
            ttl=600  # 10 minutes - trend data updates gradually
        )

        return performans_verisi
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/hedefler", response_model=List[Hedef], summary="Öğrenci Hedefleri")
async def hedefler_getir(
    aktif_sadece: bool = Query(False, description="Sadece aktif hedefleri getir"),
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrencinin hedeflerini getir

    - Günlük, haftalık, aylık hedefler
    - İlerleme durumu
    - Hedef takip sistemi
    """
    try:
        hedefler = await ogrenci_dashboard_servisi.hedefler_getir(
            kullanici_id=mevcut_kullanici.kullanici_id, db=db, aktif_sadece=aktif_sadece
        )
        return hedefler
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/hedef-olustur", response_model=Hedef, summary="Yeni Hedef Oluştur")
async def hedef_olustur(
    hedef_data: Hedef,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Yeni öğrenci hedefi oluştur

    - Günlük/haftalık/aylık hedef türleri
    - Otomatik takip sistemi
    - İlerleme hesaplama
    """
    try:
        yeni_hedef = await ogrenci_dashboard_servisi.hedef_olustur(
            kullanici_id=mevcut_kullanici.kullanici_id, db=db, hedef_data=hedef_data
        )
        return yeni_hedef
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put(
    "/hedef-guncelle/{hedef_id}", response_model=Hedef, summary="Hedef Güncelle"
)
async def hedef_guncelle(
    hedef_id: str,
    hedef_data: Hedef,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Mevcut hedefi güncelle
    """
    try:
        guncellenen_hedef = await ogrenci_dashboard_servisi.hedef_guncelle(
            kullanici_id=mevcut_kullanici.kullanici_id,
            hedef_id=hedef_id,
            db=db,
            hedef_data=hedef_data,
        )
        return guncellenen_hedef
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/hedef-sil/{hedef_id}", summary="Hedef Sil")
async def hedef_sil(
    hedef_id: str,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Hedefi sil veya iptal et
    """
    try:
        basarili = await ogrenci_dashboard_servisi.hedef_sil(
            kullanici_id=mevcut_kullanici.kullanici_id, hedef_id=hedef_id, db=db
        )
        if basarili:
            return {"message": "Hedef başarıyla silindi"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Hedef bulunamadı"
            )
    except HTTPException:
        raise  # Re-raise HTTPException without wrapping
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/bildirimler", response_model=List[Bildirim], summary="Bildirimler")
async def bildirimler_getir(
    okunmamis_sadece: bool = Query(
        False, description="Sadece okunmamış bildirimleri getir"
    ),
    limit: int = Query(50, ge=1, le=100, description="Sonuç sayısı limiti"),
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrencinin bildirimlerini getir

    - Başarı, uyarı, bilgi bildirimleri
    - Okunma durumu takibi
    - Eylem URL'leri

    **SPRINT 2**: Multi-layer cache (L1+L2) - 2 min TTL
    Expected: 400ms → 15ms (25x faster)
    Short TTL for real-time notification updates
    """
    try:
        # SPRINT 2: Cache key from query parameters
        cache_key = hashlib.md5(
            json.dumps({
                "user_id": mevcut_kullanici.kullanici_id,
                "okunmamis_sadece": okunmamis_sadece,
                "limit": limit,
            }, sort_keys=True).encode()
        ).hexdigest()

        # Initialize cache if needed
        if not dashboard_cache._initialized:
            await dashboard_cache.initialize()

        # Get or compute with cache
        async def fetch_notifications():
            """Fetch notifications from service"""
            return await ogrenci_dashboard_servisi.bildirimler_getir(
                kullanici_id=mevcut_kullanici.kullanici_id,
                db=db,
                okunmamis_sadece=okunmamis_sadece,
                limit=limit,
            )

        bildirimler = await dashboard_cache.get_or_compute(
            key=f"notif:{cache_key}",
            compute_fn=fetch_notifications,
            ttl=120  # 2 minutes - notifications need frequent updates
        )

        return bildirimler
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put(
    "/bildirim-okundu/{bildirim_id}", summary="Bildirimi Okundu Olarak İşaretle"
)
async def bildirim_okundu_isaretle(
    bildirim_id: str,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Bildirimi okundu olarak işaretle
    """
    try:
        basarili = await ogrenci_dashboard_servisi.bildirim_okundu_isaretle(
            kullanici_id=mevcut_kullanici.kullanici_id, bildirim_id=bildirim_id, db=db
        )
        if basarili:
            return {"message": "Bildirim okundu olarak işaretlendi"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bildirim bulunamadı"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/profil", response_model=OgrenciProfili, summary="Öğrenci Profili")
async def ogrenci_profili_getir(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrencinin profil bilgilerini getir

    **SPRINT 2**: Multi-layer cache (L1+L2) - 30 min TTL
    Expected: 500ms → 20ms (25x faster)
    Profile data rarely changes, perfect for caching
    """
    try:
        # SPRINT 2: Cache key for profile
        cache_key = f"profile:{mevcut_kullanici.kullanici_id}"

        # Initialize cache if needed
        if not dashboard_cache._initialized:
            await dashboard_cache.initialize()

        # Get or compute with cache
        async def fetch_profile():
            """Fetch profile from service"""
            profil = await ogrenci_dashboard_servisi.ogrenci_profili_getir(
                mevcut_kullanici.kullanici_id, db
            )
            if not profil:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Öğrenci profili bulunamadı",
                )
            return profil

        profil = await dashboard_cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_profile,
            ttl=1800  # 30 minutes - profile data rarely changes
        )

        return profil
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put(
    "/profil-guncelle", response_model=OgrenciProfili, summary="Profil Güncelle"
)
async def profil_guncelle(
    profil_data: ProfilGuncelleme,
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Öğrenci profil bilgilerini güncelle

    - Kişisel bilgiler
    - Eğitim bilgileri
    - Hedefler ve tercihler

    **SPRINT 2**: Cache invalidation on profile update
    """
    try:
        guncellenen_profil = await ogrenci_dashboard_servisi.profil_guncelle(
            kullanici_id=mevcut_kullanici.kullanici_id, db=db, profil_data=profil_data
        )

        # SPRINT 2: Invalidate profile cache after update
        if dashboard_cache._initialized:
            cache_key = f"profile:{mevcut_kullanici.kullanici_id}"
            await dashboard_cache.delete(cache_key)
            logger.info(f"Profile cache invalidated for user {mevcut_kullanici.kullanici_id}")

        return guncellenen_profil
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/ozet", summary="Dashboard Özeti")
async def dashboard_ozeti(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
    db: AsyncSession = Depends(get_db),
):
    """
    Dashboard için özet bilgileri getir

    - Temel istatistikler
    - Son aktiviteler
    - Acil bildirimler
    - Günlük hedef durumu

    **SPRINT 2**: Multi-layer cache (L1+L2) - 3 min TTL
    Expected: 1800ms → 60ms (30x faster)
    Dashboard summary is highly accessed and combines multiple queries
    """
    try:
        # SPRINT 2: Cache key for dashboard summary
        cache_key = f"summary:{mevcut_kullanici.kullanici_id}"

        # Initialize cache if needed
        if not dashboard_cache._initialized:
            await dashboard_cache.initialize()

        # Get or compute with cache
        async def fetch_summary():
            """Fetch dashboard summary from service"""
            return await ogrenci_dashboard_servisi.dashboard_ozeti_getir(
                mevcut_kullanici.kullanici_id, db
            )

        ozet = await dashboard_cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_summary,
            ttl=180  # 3 minutes - balance between freshness and performance
        )

        return {
            "success": True,
            "data": ozet,
            "message": "Dashboard özeti başarıyla alındı",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
