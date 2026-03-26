"""
Admin Panel Backend API'leri
Kullanıcı yönetimi, dashboard istatistikleri ve içerik yönetimi

CODE QUALITY FIX: Removed sensitive data exposure in error messages
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.enums import KullaniciRolu
from models.user import Kullanici, KullaniciOlustur
from services.admin_service import admin_servisi
from services.user_service import kullanici_servisi

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Panel"])
security = HTTPBearer()


async def admin_kullanici_getir(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Kullanici:
    """Admin kullanıcısını token'dan getir ve yetki kontrolü yap"""
    token = credentials.credentials
    kullanici = await kullanici_servisi.token_dogrula(token)

    if not kullanici:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
        )

    # Admin yetki kontrolü
    if kullanici.rol != KullaniciRolu.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli",
        )

    return kullanici


# ==================== KULLANICI YÖNETİMİ API'LERİ ====================


@router.get(
    "/users", response_model=List[Kullanici], summary="Tüm Kullanıcıları Listele"
)
async def kullanicilari_listele(
    rol: Optional[KullaniciRolu] = Query(None, description="Rol filtresi"),
    aktif: Optional[bool] = Query(None, description="Aktiflik durumu filtresi"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=50, description="Sayfa boyutu (max 50)"),
    _: Kullanici = Depends(admin_kullanici_getir),
) -> List[Kullanici]:
    """
    Tüm kullanıcıları listele (Admin yetkisi gerekli)

    - **rol**: Belirli role göre filtrele (ogrenci, ogretmen, veli, admin)
    - **aktif**: Aktif/pasif duruma göre filtrele
    - **sayfa**: Sayfa numarası (pagination)
    - **sayfa_boyutu**: Sayfa başına kullanıcı sayısı
    """
    try:
        kullanicilar = await admin_servisi.kullanicilari_listele(
            rol=rol, aktif=aktif, sayfa=sayfa, sayfa_boyutu=sayfa_boyutu
        )
        return kullanicilar
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Database connection error in kullanicilari_listele: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Veritabanı bağlantısı kurulamadı",
        )
    except Exception as e:
        # SECURITY FIX: Log full error, but don't expose to client
        logger.error(f"Error in kullanicilari_listele: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı listesi alınırken hata oluştu",
        )


@router.post("/users", response_model=Kullanici, summary="Yeni Kullanıcı Oluştur")
async def kullanici_olustur(
    kullanici_data: KullaniciOlustur, _: Kullanici = Depends(admin_kullanici_getir)
) -> Kullanici:
    """
    Yeni kullanıcı oluştur (Admin yetkisi gerekli)

    - **email**: Benzersiz e-posta adresi
    - **ad_soyad**: Kullanıcının adı ve soyadı
    - **sifre**: En az 6 karakter
    - **rol**: Kullanıcı rolü (ogrenci, ogretmen, veli, admin)
    """
    try:
        kullanici = await admin_servisi.kullanici_olustur(kullanici_data)
        return kullanici
    except ValueError as e:
        # ValueError is expected for validation errors - safe to show
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Database connection error in kullanici_olustur: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Veritabanı bağlantısı kurulamadı",
        )
    except Exception as e:
        # SECURITY FIX: Don't expose internal errors
        logger.error(f"Error in kullanici_olustur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı oluşturulurken hata oluştu",
        )


@router.get(
    "/users/{kullanici_id}", response_model=Kullanici, summary="Kullanıcı Detayı"
)
async def kullanici_detay(
    kullanici_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> Kullanici:
    """
    Belirli kullanıcının detay bilgilerini getir (Admin yetkisi gerekli)
    """
    kullanici = await admin_servisi.kullanici_getir(kullanici_id)

    if not kullanici:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı"
        )

    return kullanici


@router.put(
    "/users/{kullanici_id}", response_model=Kullanici, summary="Kullanıcı Güncelle"
)
async def kullanici_guncelle(
    kullanici_id: str,
    kullanici_data: Dict[str, Any],
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Kullanici:
    """
    Kullanıcı bilgilerini güncelle (Admin yetkisi gerekli)

    Güncellenebilir alanlar:
    - ad_soyad
    - telefon
    - aktif (hesap durumu)
    - rol (dikkatli kullanın!)
    """
    try:
        kullanici = await admin_servisi.kullanici_guncelle(kullanici_id, kullanici_data)
        return kullanici
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/users/{kullanici_id}", summary="Kullanıcı Sil")
async def kullanici_sil(
    kullanici_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Kullanıcıyı sil (Admin yetkisi gerekli)

    DİKKAT: Bu işlem geri alınamaz!
    """
    try:
        basarili = await admin_servisi.kullanici_sil(kullanici_id)

        if basarili:
            return {"success": True, "message": "Kullanıcı başarıyla silindi"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== DASHBOARD İSTATİSTİKLERİ ====================


@router.get("/dashboard/stats", summary="Admin Dashboard İstatistikleri")
async def dashboard_istatistikleri(
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Admin dashboard için genel sistem istatistikleri

    İçerik:
    - Toplam kullanıcı sayıları (rol bazında)
    - Aktif/pasif kullanıcı dağılımı
    - Son 30 gün kayıt trendi
    - Sistem performans metrikleri
    """
    try:
        istatistikler = await admin_servisi.dashboard_istatistikleri_getir()
        return {
            "success": True,
            "data": istatistikler,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK YÖNETİMİ - SORULAR ====================


@router.get("/content/questions", summary="Soru Bankası Listesi")
async def soru_bankasi_listesi(
    konu: Optional[str] = Query(None, description="Konu filtresi"),
    zorluk: Optional[str] = Query(None, description="Zorluk seviyesi filtresi"),
    sinav_tipi: Optional[str] = Query(None, description="Sınav türü filtresi"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=50, description="Sayfa boyutu (max 50)"),
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Soru bankasındaki soruları listele (Admin yetkisi gerekli)

    - **konu**: Matematik, Türkçe, Fen, Sosyal vb.
    - **zorluk**: Kolay, Orta, Zor
    - **sinav_tipi**: TYT, AYT, YDT
    """
    try:
        sorular = await admin_servisi.soru_bankasi_listesi(
            konu=konu,
            zorluk=zorluk,
            sinav_tipi=sinav_tipi,
            sayfa=sayfa,
            sayfa_boyutu=sayfa_boyutu,
        )
        return {
            "success": True,
            "data": sorular,
            "total_count": len(sorular),  # Gerçek implementasyonda toplam sayı
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/content/questions", summary="Yeni Soru Ekle")
async def soru_ekle(
    soru_data: Dict[str, Any], _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Soru bankasına yeni soru ekle (Admin yetkisi gerekli)

    Gerekli alanlar:
    - soru_metni: Soru metni
    - secenekler: A, B, C, D seçenekleri
    - dogru_cevap: Doğru seçenek
    - konu: Konu adı
    - zorluk_seviyesi: Kolay/Orta/Zor
    - sinav_tipi: TYT/AYT/YDT
    """
    try:
        soru = await admin_servisi.soru_ekle(soru_data)
        return {"success": True, "data": soru, "message": "Soru başarıyla eklendi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/content/questions/{soru_id}", summary="Soru Güncelle")
async def soru_guncelle(
    soru_id: str,
    soru_data: Dict[str, Any],
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Mevcut soruyu güncelle (Admin yetkisi gerekli)
    """
    try:
        soru = await admin_servisi.soru_guncelle(soru_id, soru_data)
        return {"success": True, "data": soru, "message": "Soru başarıyla güncellendi"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/content/questions/{soru_id}", summary="Soru Sil")
async def soru_sil(
    soru_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Soruyu sil (Admin yetkisi gerekli)
    """
    try:
        basarili = await admin_servisi.soru_sil(soru_id)

        if basarili:
            return {"success": True, "message": "Soru başarıyla silindi"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== İÇERİK YÖNETİMİ - EĞİTİM MATERYALLERİ ====================


@router.get("/content/educational", summary="Eğitim Materyalleri Listesi")
async def egitim_materyalleri_listesi(
    tur: Optional[str] = Query(None, description="Materyal türü (video, makale, pdf)"),
    konu: Optional[str] = Query(None, description="Konu filtresi"),
    onay_durumu: Optional[str] = Query(None, description="Onay durumu filtresi"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=50, description="Sayfa boyutu (max 50)"),
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Eğitim materyallerini listele (Admin yetkisi gerekli)

    - **tur**: video, makale, pdf, interaktif
    - **konu**: Matematik, Türkçe, Fen, Sosyal vb.
    - **onay_durumu**: beklemede, onaylandi, reddedildi
    """
    try:
        materyaller = await admin_servisi.egitim_materyalleri_listesi(
            tur=tur,
            konu=konu,
            onay_durumu=onay_durumu,
            sayfa=sayfa,
            sayfa_boyutu=sayfa_boyutu,
        )
        return {"success": True, "data": materyaller, "total_count": len(materyaller)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/content/educational", summary="Yeni Eğitim Materyali Ekle")
async def egitim_materyali_ekle(
    materyal_data: Dict[str, Any], _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Yeni eğitim materyali ekle (Admin yetkisi gerekli)

    Gerekli alanlar:
    - baslik: Materyal başlığı
    - aciklama: Kısa açıklama
    - tur: video/makale/pdf/interaktif
    - konu: İlgili konu
    - url: Materyal linki
    - zorluk_seviyesi: Kolay/Orta/Zor
    """
    try:
        materyal = await admin_servisi.egitim_materyali_ekle(materyal_data)
        return {
            "success": True,
            "data": materyal,
            "message": "Eğitim materyali başarıyla eklendi",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put("/content/educational/{materyal_id}", summary="Eğitim Materyali Güncelle")
async def egitim_materyali_guncelle(
    materyal_id: str,
    materyal_data: Dict[str, Any],
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Eğitim materyalini güncelle (Admin yetkisi gerekli)
    """
    try:
        materyal = await admin_servisi.egitim_materyali_guncelle(
            materyal_id, materyal_data
        )
        return {
            "success": True,
            "data": materyal,
            "message": "Eğitim materyali başarıyla güncellendi",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/content/educational/{materyal_id}", summary="Eğitim Materyali Sil")
async def egitim_materyali_sil(
    materyal_id: str, _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Eğitim materyalini sil (Admin yetkisi gerekli)
    """
    try:
        basarili = await admin_servisi.egitim_materyali_sil(materyal_id)

        if basarili:
            return {"success": True, "message": "Eğitim materyali başarıyla silindi"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Eğitim materyali bulunamadı",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.put(
    "/content/educational/{materyal_id}/approve", summary="Eğitim Materyali Onayla"
)
async def egitim_materyali_onayla(
    materyal_id: str,
    onay_data: Dict[str, Any],
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    Eğitim materyalini onayla veya reddet (Admin yetkisi gerekli)

    Body:
    - onay_durumu: "onaylandi" veya "reddedildi"
    - not: Onay/red notu (opsiyonel)
    """
    try:
        materyal = await admin_servisi.egitim_materyali_onay_durumu_guncelle(
            materyal_id, onay_data
        )
        return {
            "success": True,
            "data": materyal,
            "message": f"Materyal {onay_data.get('onay_durumu', 'güncellendi')}",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# ==================== TOPLU İŞLEMLER ====================


@router.post("/content/questions/bulk-upload", summary="Toplu Soru Yükleme")
async def toplu_soru_yukle(
    sorular_data: List[Dict[str, Any]], _: Kullanici = Depends(admin_kullanici_getir)
) -> Dict[str, Any]:
    """
    Toplu soru yükleme (Admin yetkisi gerekli)

    JSON array formatında birden fazla soru yükle
    """
    try:
        sonuc = await admin_servisi.toplu_soru_yukle(sorular_data)
        return {
            "success": True,
            "data": sonuc,
            "message": f"{sonuc['basarili_sayisi']} soru başarıyla yüklendi",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/content/search", summary="İçerik Arama")
async def icerik_ara(
    q: str = Query(..., min_length=2, description="Arama terimi"),
    tur: Optional[str] = Query(None, description="İçerik türü filtresi"),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    sayfa_boyutu: int = Query(20, ge=1, le=50, description="Sayfa boyutu (max 50)"),
    _: Kullanici = Depends(admin_kullanici_getir),
) -> Dict[str, Any]:
    """
    İçerik arama (sorular ve eğitim materyalleri)
    """
    try:
        sonuclar = await admin_servisi.icerik_ara(
            arama_terimi=q, tur=tur, sayfa=sayfa, sayfa_boyutu=sayfa_boyutu
        )
        return {"success": True, "data": sonuclar, "query": q}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
