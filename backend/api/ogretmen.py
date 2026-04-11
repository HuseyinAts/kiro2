"""
Öğretmen paneli API endpoint'leri
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.auth import mevcut_kullanici_getir
from models import Kullanici, KullaniciRolu
from services.ogretmen_service import ogretmen_servisi

router = APIRouter(
    prefix="/api/v1/ogretmen",
    tags=["Öğretmen Paneli (DEPRECATED)"],
    deprecated=True,  # In-memory backend — teacher_routes.py is DB-backed
)


class RaporParametreleri(BaseModel):
    """Rapor oluşturma parametreleri"""

    baslangic_tarihi: Optional[datetime] = Field(
        None, description="Rapor başlangıç tarihi"
    )
    bitis_tarihi: Optional[datetime] = Field(None, description="Rapor bitiş tarihi")
    sinav_tipi: Optional[str] = Field(None, description="Sınav türü filtresi")


class BildirimGonder(BaseModel):
    """Bildirim gönderme modeli"""

    baslik: str = Field(
        ..., min_length=1, max_length=200, description="Bildirim başlığı"
    )
    mesaj: str = Field(
        ..., min_length=1, max_length=1000, description="Bildirim mesajı"
    )
    tip: str = Field("bilgi", description="Bildirim tipi (bilgi, uyari, basari, hata)")


async def ogretmen_yetkisi_kontrol(
    mevcut_kullanici: Kullanici = Depends(mevcut_kullanici_getir),
) -> Kullanici:
    """Öğretmen yetkisi kontrolü"""
    if mevcut_kullanici.rol != KullaniciRolu.OGRETMEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için öğretmen yetkisi gerekli",
        )
    return mevcut_kullanici


@router.get("/dashboard", summary="Öğretmen Dashboard")
async def ogretmen_dashboard(ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol)):
    """
    Öğretmen dashboard verilerini getir

    - Genel istatistikler
    - Öğrenci listesi özeti
    - Son bildirimler
    - Performans özeti
    """
    try:
        # Öğretmen ID'sini kullanıcı ID'sinden al (basit implementasyon)
        ogretmen_id = ogretmen.kullanici_id

        dashboard_verisi = await ogretmen_servisi.ogretmen_dashboard_verisi(ogretmen_id)

        return {
            "success": True,
            "data": dashboard_verisi,
            "message": "Dashboard verisi başarıyla alındı",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard verisi alınamadı",
        )


@router.get("/ogrenciler", summary="Öğrenci Listesi")
async def ogrenci_listesi(
    ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol),
    sayfa: int = Query(1, ge=1, description="Sayfa numarası"),
    limit: int = Query(20, ge=1, le=100, description="Sayfa başına öğrenci sayısı"),
):
    """
    Öğretmenin sorumlu olduğu öğrenci listesini getir

    - Öğrenci temel bilgileri
    - Son performans verileri
    - Aktiflik durumu
    - Sayfalama desteği
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        # Tüm öğrenci listesini getir
        tum_ogrenciler = await ogretmen_servisi.ogrenci_listesi_getir(ogretmen_id)

        # Sayfalama uygula
        baslangic = (sayfa - 1) * limit
        bitis = baslangic + limit
        sayfalanmis_ogrenciler = tum_ogrenciler[baslangic:bitis]

        return {
            "success": True,
            "data": {
                "ogrenciler": sayfalanmis_ogrenciler,
                "sayfalama": {
                    "mevcut_sayfa": sayfa,
                    "sayfa_basina": limit,
                    "toplam_ogrenci": len(tum_ogrenciler),
                    "toplam_sayfa": (len(tum_ogrenciler) + limit - 1) // limit,
                },
            },
            "message": f"{len(sayfalanmis_ogrenciler)} öğrenci listelendi",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Öğrenci listesi alınamadı",
        )


@router.get("/ogrenci/{ogrenci_id}/performans", summary="Öğrenci Detay Performans")
async def ogrenci_performans_detay(
    ogrenci_id: str, ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol)
):
    """
    Belirli bir öğrencinin detaylı performans analizi

    - Sınav geçmişi
    - Konu bazlı performans
    - Net trendi
    - Zayıf/güçlü konular
    - Öneriler
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        performans_verisi = await ogretmen_servisi.ogrenci_detay_performans(
            ogretmen_id, ogrenci_id
        )

        return {
            "success": True,
            "data": performans_verisi,
            "message": "Öğrenci performans verisi başarıyla alındı",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Öğrenci performans verisi alınamadı",
        )


@router.post("/rapor/sinif", summary="Sınıf Raporu Oluştur")
async def sinif_raporu_olustur(
    rapor_parametreleri: RaporParametreleri,
    ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol),
):
    """
    Sınıf geneli için performans raporu oluştur

    - Sınıf istatistikleri
    - Konu bazlı performans
    - Karşılaştırmalı analiz
    - Öneriler
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        # Parametreleri dict'e çevir
        parametreler = rapor_parametreleri.dict()

        rapor = await ogretmen_servisi.sinif_raporu_olustur(ogretmen_id, parametreler)

        return {
            "success": True,
            "data": rapor,
            "message": "Sınıf raporu başarıyla oluşturuldu",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınıf raporu oluşturulamadı",
        )


@router.get("/raporlar", summary="Rapor Listesi")
async def rapor_listesi(
    ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol),
    limit: int = Query(10, ge=1, le=50, description="Maksimum rapor sayısı"),
):
    """
    Öğretmenin oluşturduğu raporları listele
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        # Öğretmenin raporlarını filtrele
        tum_raporlar = ogretmen_servisi.sinif_raporlari
        ogretmen_raporlari = [
            rapor
            for rapor in tum_raporlar.values()
            if rapor.get("ogretmen_id") == ogretmen_id
        ]

        # En yeni raporlar önce
        ogretmen_raporlari.sort(key=lambda x: x["olusturma_tarihi"], reverse=True)

        return {
            "success": True,
            "data": {
                "raporlar": ogretmen_raporlari[:limit],
                "toplam_rapor": len(ogretmen_raporlari),
            },
            "message": f"{len(ogretmen_raporlari[:limit])} rapor listelendi",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rapor listesi alınamadı",
        )


@router.get("/rapor/{rapor_id}", summary="Rapor Detayı")
async def rapor_detay(
    rapor_id: str, ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol)
):
    """
    Belirli bir raporun detaylarını getir
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        rapor = ogretmen_servisi.sinif_raporlari.get(rapor_id)

        if not rapor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Rapor bulunamadı"
            )

        # Yetki kontrolü
        if rapor.get("ogretmen_id") != ogretmen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu rapora erişim yetkiniz yok",
            )

        return {
            "success": True,
            "data": rapor,
            "message": "Rapor detayı başarıyla alındı",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rapor detayı alınamadı",
        )


@router.post("/bildirim", summary="Bildirim Gönder")
async def bildirim_gonder(
    bildirim: BildirimGonder, ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol)
):
    """
    Öğretmen bildirimi oluştur
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        basarili = await ogretmen_servisi.bildirim_gonder(ogretmen_id, bildirim.dict())

        if basarili:
            return {
                "success": True,
                "data": None,
                "message": "Bildirim başarıyla gönderildi",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Bildirim gönderilemedi"
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bildirim gönderme hatası",
        )


@router.get("/bildirimler", summary="Bildirimler")
async def bildirimler_getir(
    ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol),
    limit: int = Query(20, ge=1, le=100, description="Maksimum bildirim sayısı"),
):
    """
    Öğretmen bildirimlerini getir
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        bildirimler = await ogretmen_servisi.bildirimler_getir(ogretmen_id, limit)

        return {
            "success": True,
            "data": {
                "bildirimler": bildirimler,
                "toplam": len(bildirimler),
                "okunmamis": len([b for b in bildirimler if not b["okundu"]]),
            },
            "message": f"{len(bildirimler)} bildirim alındı",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bildirimler alınamadı",
        )


@router.put("/bildirim/{bildirim_id}/okundu", summary="Bildirimi Okundu İşaretle")
async def bildirim_okundu_isaretle(
    bildirim_id: str, ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol)
):
    """
    Bildirimi okundu olarak işaretle
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        basarili = await ogretmen_servisi.bildirim_okundu_isaretle(
            ogretmen_id, bildirim_id
        )

        if basarili:
            return {
                "success": True,
                "data": None,
                "message": "Bildirim okundu olarak işaretlendi",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bildirim bulunamadı"
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bildirim güncellenemedi",
        )


@router.get("/istatistikler", summary="Öğretmen İstatistikleri")
async def ogretmen_istatistikleri(
    ogretmen: Kullanici = Depends(ogretmen_yetkisi_kontrol),
    gun_sayisi: int = Query(
        30, ge=1, le=365, description="Son kaç günün istatistikleri"
    ),
):
    """
    Öğretmen için özet istatistikler

    - Son dönem performans trendi
    - Aktif öğrenci sayısı
    - Ortalama başarı oranı
    - Sınıf karşılaştırması
    """
    try:
        ogretmen_id = ogretmen.kullanici_id

        # Temel dashboard verisini al
        dashboard = await ogretmen_servisi.ogretmen_dashboard_verisi(ogretmen_id)

        # Ek istatistikler hesapla
        baslangic_tarihi = datetime.now() - timedelta(days=gun_sayisi)

        istatistikler = {
            "genel_ozet": dashboard["genel_istatistikler"],
            "donem_bilgisi": {
                "baslangic_tarihi": baslangic_tarihi,
                "gun_sayisi": gun_sayisi,
            },
            "ogrenci_aktivitesi": {
                "toplam_ogrenci": dashboard["genel_istatistikler"]["toplam_ogrenci"],
                "aktif_ogrenci": len(
                    [o for o in dashboard["ogrenci_listesi"] if o.get("aktif", True)]
                ),
            },
            "son_guncelleme": datetime.now(),
        }

        return {
            "success": True,
            "data": istatistikler,
            "message": "İstatistikler başarıyla alındı",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İstatistikler alınamadı",
        )
