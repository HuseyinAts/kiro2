"""
İçerik Yönetim API'leri
Soru bankası, eğitim materyalleri ve içerik onay/reddetme sistemi
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from core.dependencies import AuthenticatedUser, UserRole, get_current_user

# Mock implementations for testing
router = APIRouter(prefix="/api/v1/content-management", tags=["İçerik Yönetimi"])

_CONTENT_MGMT_STAFF = frozenset(
    {UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN}
)


async def admin_yetki_kontrolu(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Admin yetkisi kontrolü"""
    if current_user.role not in _CONTENT_MGMT_STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin veya öğretmen yetkisi gerekli",
        )
    return current_user


# ==================== SORU BANKASI CRUD API'LERİ ====================


@router.get("/questions", response_model=dict[str, Any])
async def soru_bankasi_listele(
    sinav_tipi: str | None = Query(None, description="Sınav türü (TYT, AYT, YDT)"),
    konu: str | None = Query(None, description="Konu filtresi"),
    zorluk_seviyesi: str | None = Query(None, description="Zorluk seviyesi"),
    onay_durumu: str | None = Query(
        None, description="Onay durumu (pending, approved, rejected)"
    ),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=100, description="Sayfa boyutu"),
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Soru bankasındaki soruları listele ve filtrele"""
    try:
        # Mock data
        mock_sorular = []
        for i in range(min(sayfa_boyutu, 5)):
            soru = {
                "id": f"soru-{i+1}",
                "soru_metni": f"Bu bir örnek soru metnidir - {i+1}",
                "sinav_tipi": sinav_tipi or "TYT",
                "konu": konu or "Matematik",
                "zorluk_seviyesi": zorluk_seviyesi or "medium",
                "onay_durumu": onay_durumu or "approved",
                "olusturma_tarihi": datetime.now().isoformat(),
                "aktif": True,
            }
            mock_sorular.append(soru)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "sorular": mock_sorular,
                    "toplam_sayfa": 1,
                    "mevcut_sayfa": sayfa,
                    "toplam_soru": len(mock_sorular),
                    "filtreler": {
                        "sinav_tipi": sinav_tipi,
                        "konu": konu,
                        "zorluk_seviyesi": zorluk_seviyesi,
                        "onay_durumu": onay_durumu,
                    },
                },
                "message": f"{len(mock_sorular)} soru başarıyla getirildi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/questions", response_model=dict[str, Any])
async def soru_ekle(
    soru_data: dict[str, Any], current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu)
):
    """Soru bankasına yeni soru ekle"""
    try:
        # Veri validasyonu
        required_fields = [
            "soru_metni",
            "secenekler",
            "dogru_cevap",
            "sinav_tipi",
            "konu",
            "zorluk_seviyesi",
        ]
        for field in required_fields:
            if field not in soru_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gerekli alan eksik: {field}",
                )

        # Mock response
        mock_soru = {
            "soru_id": "new-soru-123",
            "soru_metni": soru_data["soru_metni"],
            "sinav_tipi": soru_data["sinav_tipi"],
            "konu": soru_data["konu"],
            "zorluk_seviyesi": soru_data["zorluk_seviyesi"],
            "olusturma_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": mock_soru,
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


@router.get("/questions/{soru_id}", response_model=dict[str, Any])
async def soru_detay(
    soru_id: str, current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu)
):
    """Belirli bir sorunun detaylarını getir"""
    try:
        # Mock soru detayı
        soru_detay = {
            "id": soru_id,
            "soru_metni": "Bu bir örnek soru metnidir",
            "secenekler": {
                "A": "Seçenek A",
                "B": "Seçenek B",
                "C": "Seçenek C",
                "D": "Seçenek D",
            },
            "dogru_cevap": "A",
            "cozum_aciklamasi": "Bu sorunun çözüm açıklamasıdır",
            "sinav_tipi": "TYT",
            "konu": "Matematik",
            "zorluk_seviyesi": "medium",
            "olusturma_tarihi": datetime.now().isoformat(),
            "aktif": True,
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


@router.put("/questions/{soru_id}", response_model=dict[str, Any])
async def soru_guncelle(
    soru_id: str,
    soru_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Mevcut soruyu güncelle"""
    try:
        mock_response = {
            "soru_id": soru_id,
            "soru_metni": soru_data.get("soru_metni", "Güncellenmiş soru"),
            "guncelleme_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": mock_response,
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


@router.delete("/questions/{soru_id}", response_model=dict[str, Any])
async def soru_sil(
    soru_id: str, current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu)
):
    """Soruyu sil (soft delete)"""
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {"soru_id": soru_id},
                "message": "Soru başarıyla silindi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== EĞİTİM MATERYALİ CRUD API'LERİ ====================


@router.get("/educational", response_model=dict[str, Any])
async def egitim_materyalleri_listele(
    icerik_turu: str | None = Query(
        None, description="İçerik türü (video, article, interactive, quiz)"
    ),
    konu: str | None = Query(None, description="Konu filtresi"),
    platform: str | None = Query(
        None, description="Platform filtresi (youtube, khan_academy, eba_tv)"
    ),
    zorluk_seviyesi: str | None = Query(None, description="Zorluk seviyesi"),
    onay_durumu: str | None = Query(None, description="Onay durumu"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=100, description="Sayfa boyutu"),
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Eğitim materyallerini listele ve filtrele"""
    try:
        # Mock data
        mock_materyaller = []
        for i in range(min(sayfa_boyutu, 3)):
            materyal = {
                "id": f"materyal-{i+1}",
                "baslik": f"Eğitim Materyali {i+1}",
                "aciklama": f"Bu bir örnek eğitim materyalidir - {i+1}",
                "icerik_turu": icerik_turu or "video",
                "platform": platform or "youtube",
                "konu": konu or "Matematik",
                "zorluk_seviyesi": zorluk_seviyesi or "medium",
                "onay_durumu": onay_durumu or "approved",
                "olusturma_tarihi": datetime.now().isoformat(),
                "aktif": True,
            }
            mock_materyaller.append(materyal)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "materyaller": mock_materyaller,
                    "toplam_sayfa": 1,
                    "mevcut_sayfa": sayfa,
                    "toplam_materyal": len(mock_materyaller),
                },
                "message": f"{len(mock_materyaller)} materyal başarıyla getirildi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/educational", response_model=dict[str, Any])
async def egitim_materyali_ekle(
    materyal_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Yeni eğitim materyali ekle"""
    try:
        # Veri validasyonu
        required_fields = [
            "baslik",
            "icerik_turu",
            "platform",
            "url",
            "konu",
            "zorluk_seviyesi",
            "sinif_seviyesi",
        ]
        for field in required_fields:
            if field not in materyal_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gerekli alan eksik: {field}",
                )

        # Mock response
        mock_materyal = {
            "materyal_id": "new-materyal-123",
            "baslik": materyal_data["baslik"],
            "icerik_turu": materyal_data["icerik_turu"],
            "platform": materyal_data["platform"],
            "konu": materyal_data["konu"],
            "olusturma_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": mock_materyal,
                "message": "Eğitim materyali başarıyla eklendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/educational/{materyal_id}", response_model=dict[str, Any])
async def egitim_materyali_detay(
    materyal_id: str, current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu)
):
    """Belirli bir eğitim materyalinin detaylarını getir"""
    try:
        # Mock materyal detayı
        materyal_detay = {
            "id": materyal_id,
            "baslik": "Örnek Eğitim Materyali",
            "aciklama": "Bu bir örnek eğitim materyali açıklamasıdır",
            "icerik_turu": "video",
            "platform": "youtube",
            "url": "https://youtube.com/watch?v=example",
            "konu": "Matematik",
            "zorluk_seviyesi": "medium",
            "sinif_seviyesi": 12,
            "olusturma_tarihi": datetime.now().isoformat(),
            "aktif": True,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": materyal_detay,
                "message": "Eğitim materyali detayları başarıyla getirildi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/educational/{materyal_id}", response_model=dict[str, Any])
async def egitim_materyali_guncelle(
    materyal_id: str,
    materyal_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Mevcut eğitim materyalini güncelle"""
    try:
        mock_response = {
            "materyal_id": materyal_id,
            "baslik": materyal_data.get("baslik", "Güncellenmiş Materyal"),
            "guncelleme_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": mock_response,
                "message": "Eğitim materyali başarıyla güncellendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/educational/{materyal_id}", response_model=dict[str, Any])
async def egitim_materyali_sil(
    materyal_id: str, current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu)
):
    """Eğitim materyalini sil (soft delete)"""
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {"materyal_id": materyal_id},
                "message": "Eğitim materyali başarıyla silindi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK ONAY/REDDETME API'LERİ ====================


@router.put("/questions/{soru_id}/approve", response_model=dict[str, Any])
async def soru_onay_durumu_guncelle(
    soru_id: str,
    onay_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Soru onay durumunu güncelle"""
    try:
        if "onay_durumu" not in onay_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="onay_durumu alanı gerekli",
            )

        if onay_data["onay_durumu"] not in ["approved", "rejected", "pending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="onay_durumu 'approved', 'rejected' veya 'pending' olmalı",
            )

        mock_response = {
            "soru_id": soru_id,
            "onay_durumu": onay_data["onay_durumu"],
            "onaylayan": current_user.full_name,
            "onay_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": mock_response,
                "message": f"Soru {onay_data['onay_durumu']} durumuna güncellendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/educational/{materyal_id}/approve", response_model=dict[str, Any])
async def egitim_materyali_onay_durumu_guncelle(
    materyal_id: str,
    onay_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Eğitim materyali onay durumunu güncelle"""
    try:
        if "onay_durumu" not in onay_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="onay_durumu alanı gerekli",
            )

        mock_response = {
            "materyal_id": materyal_id,
            "onay_durumu": onay_data["onay_durumu"],
            "onaylayan": current_user.full_name,
            "onay_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": mock_response,
                "message": f"Eğitim materyali {onay_data['onay_durumu']} durumuna güncellendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== TOPLU İÇERİK YÜKLEME API'Sİ ====================


@router.post("/questions/bulk-upload", response_model=dict[str, Any])
async def toplu_soru_yukle(
    sorular_data: list[dict[str, Any]],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Toplu soru yükleme"""
    try:
        if not sorular_data or not isinstance(sorular_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçerli bir soru listesi gönderilmeli",
            )

        if len(sorular_data) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tek seferde en fazla 100 soru yüklenebilir",
            )

        # Mock response
        mock_result = {
            "toplam_soru": len(sorular_data),
            "basarili_yuklenen": len(sorular_data),
            "basarisiz_yuklenen": 0,
            "hatalar": [],
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": mock_result,
                "message": f"{len(sorular_data)} soru başarıyla yüklendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/educational/bulk-upload", response_model=dict[str, Any])
async def toplu_egitim_materyali_yukle(
    materyaller_data: list[dict[str, Any]],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Toplu eğitim materyali yükleme"""
    try:
        if not materyaller_data or not isinstance(materyaller_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçerli bir materyal listesi gönderilmeli",
            )

        if len(materyaller_data) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tek seferde en fazla 50 materyal yüklenebilir",
            )

        # Mock response
        mock_result = {
            "toplam_materyal": len(materyaller_data),
            "basarili_yuklenen": len(materyaller_data),
            "basarisiz_yuklenen": 0,
            "hatalar": [],
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": mock_result,
                "message": f"{len(materyaller_data)} materyal başarıyla yüklendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK KATEGORİLENDİRME API'LERİ ====================


@router.get("/categories", response_model=dict[str, Any])
async def icerik_kategorileri_getir(
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Mevcut içerik kategorilerini getir"""
    try:
        kategoriler = {
            "sinav_tipleri": ["TYT", "AYT", "YDT"],
            "konular": [
                "Matematik",
                "Türkçe",
                "Fen",
                "Sosyal",
                "Fizik",
                "Kimya",
                "Biyoloji",
                "İngilizce",
            ],
            "zorluk_seviyeleri": ["easy", "medium", "hard"],
            "icerik_turleri": ["video", "article", "interactive", "quiz", "pdf"],
            "platformlar": ["youtube", "khan_academy", "eba_tv", "custom"],
            "sinif_seviyeleri": [9, 10, 11, 12],
            "diller": ["tr", "en"],
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": kategoriler,
                "message": "İçerik kategorileri başarıyla getirildi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/categories", response_model=dict[str, Any])
async def icerik_kategorisi_ekle(
    kategori_data: dict[str, Any],
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Yeni içerik kategorisi ekle"""
    try:
        if "kategori_adi" not in kategori_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="kategori_adi alanı gerekli",
            )

        mock_kategori = {
            "kategori_id": "new-kategori-123",
            "kategori_adi": kategori_data["kategori_adi"],
            "olusturma_tarihi": datetime.now().isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": mock_kategori,
                "message": "İçerik kategorisi başarıyla eklendi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK ARAMA VE FİLTRELEME API'LERİ ====================


@router.get("/search", response_model=dict[str, Any])
async def icerik_ara(
    q: str = Query(..., min_length=2, description="Arama terimi"),
    icerik_turu: str | None = Query(
        None, description="İçerik türü (question, educational)"
    ),
    konu: str | None = Query(None, description="Konu filtresi"),
    zorluk_seviyesi: str | None = Query(
        None, description="Zorluk seviyesi filtresi"
    ),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=100, description="Sayfa boyutu"),
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """İçerik arama (sorular ve eğitim materyalleri)"""
    try:
        # Mock arama sonuçları
        mock_sonuclar = []
        for i in range(min(5, sayfa_boyutu)):
            sonuc = {
                "id": f"sonuc-{i+1}",
                "tip": icerik_turu or ("soru" if i % 2 == 0 else "egitim_materyali"),
                "baslik": f"'{q}' ile ilgili içerik {i+1}",
                "aciklama": f"Bu içerik '{q}' arama terimiyle eşleşiyor",
                "konu": konu or "Matematik",
                "zorluk_seviyesi": zorluk_seviyesi or "medium",
                "relevans_skoru": 0.9 - (i * 0.1),
            }
            mock_sonuclar.append(sonuc)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "arama_terimi": q,
                    "sonuclar": mock_sonuclar,
                    "toplam_sonuc": len(mock_sonuclar),
                    "mevcut_sayfa": sayfa,
                    "toplam_sayfa": 1,
                },
                "message": f"'{q}' için {len(mock_sonuclar)} sonuç bulundu",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/filter-options", response_model=dict[str, Any])
async def filtre_secenekleri_getir(
    current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu),
):
    """Filtreleme için mevcut seçenekleri getir"""
    try:
        filtre_secenekleri = {
            "konular": [
                "Matematik",
                "Türkçe",
                "Fen",
                "Sosyal",
                "Fizik",
                "Kimya",
                "Biyoloji",
                "İngilizce",
            ],
            "sinav_tipleri": ["TYT", "AYT", "YDT"],
            "zorluk_seviyeleri": ["easy", "medium", "hard"],
            "platformlar": ["youtube", "khan_academy", "eba_tv", "custom"],
            "icerik_turleri": ["video", "article", "interactive", "quiz"],
            "onay_durumlari": ["pending", "approved", "rejected"],
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": filtre_secenekleri,
                "message": "Filtre seçenekleri başarıyla getirildi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK İSTATİSTİKLERİ ====================


@router.get("/statistics", response_model=dict[str, Any])
async def icerik_istatistikleri(current_user: AuthenticatedUser = Depends(admin_yetki_kontrolu)):
    """İçerik yönetimi istatistikleri"""
    try:
        istatistikler = {
            "soru_istatistikleri": {
                "toplam_soru": 1250,
                "sinav_tipi_dagilimi": {"TYT": 500, "AYT": 600, "YDT": 150},
            },
            "materyal_istatistikleri": {
                "toplam_materyal": 450,
                "platform_dagilimi": {
                    "youtube": 200,
                    "khan_academy": 150,
                    "eba_tv": 100,
                },
            },
            "genel_istatistikler": {
                "toplam_icerik": 1700,
                "son_guncelleme": datetime.now().isoformat(),
            },
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": istatistikler,
                "message": "İçerik istatistikleri başarıyla getirildi",
            },
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
