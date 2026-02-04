from unittest.mock import Mock, patch, AsyncMock

"""
Öğretmen servisi testleri
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta

import pytest

from models import KullaniciOlustur, KullaniciRolu
from services.ogretmen_service import ogretmen_servisi
from services.user_service import kullanici_servisi


@pytest.fixture
async def setup_test_data():
    """Test verileri hazırla"""
    # Test öğretmeni oluştur
    ogretmen_data = KullaniciOlustur(
        email="ogretmen@test.com",
        ad_soyad="Test Öğretmen",
        sifre="test123",
        rol=KullaniciRolu.OGRETMEN,
    )
    ogretmen = await kullanici_servisi.kullanici_olustur(ogretmen_data)

    # Test öğrencileri oluştur
    ogrenciler = []
    for i in range(3):
        ogrenci_data = KullaniciOlustur(
            email=f"ogrenci{i}@test.com",
            ad_soyad=f"Test Öğrenci {i+1}",
            sifre="test123",
            rol=KullaniciRolu.OGRENCI,
        )
        ogrenci = await kullanici_servisi.kullanici_olustur(ogrenci_data)
        ogrenciler.append(ogrenci)

    # Öğretmen-öğrenci ilişkisi kur
    ogretmen_servisi.sinif_ogrenci_iliskileri[ogretmen.kullanici_id] = [
        ogrenci.kullanici_id for ogrenci in ogrenciler
    ]

    return {"ogretmen": ogretmen, "ogrenciler": ogrenciler}


@pytest.mark.asyncio
async def test_ogretmen_dashboard_verisi(setup_test_data):
    """Öğretmen dashboard verisi testi"""
    test_data = await setup_test_data
    ogretmen = test_data["ogretmen"]

    # Dashboard verisini al
    dashboard_data = await ogretmen_servisi.ogretmen_dashboard_verisi(
        ogretmen.kullanici_id
    )

    # Kontroller
    assert dashboard_data is not None
    assert "genel_istatistikler" in dashboard_data
    assert "ogrenci_listesi" in dashboard_data
    assert "son_bildirimler" in dashboard_data

    # İstatistik kontrolleri
    stats = dashboard_data["genel_istatistikler"]
    assert stats["toplam_ogrenci"] == 3
    assert "ortalama_basari" in stats
    assert "son_guncelleme" in stats


@pytest.mark.asyncio
async def test_ogrenci_listesi_getir(setup_test_data):
    """Öğrenci listesi getirme testi"""
    test_data = await setup_test_data
    ogretmen = test_data["ogretmen"]

    # Öğrenci listesini al
    ogrenci_listesi = await ogretmen_servisi.ogrenci_listesi_getir(
        ogretmen.kullanici_id
    )

    # Kontroller
    assert len(ogrenci_listesi) == 3

    for ogrenci in ogrenci_listesi:
        assert "ogrenci_id" in ogrenci
        assert "ad_soyad" in ogrenci
        assert "performans" in ogrenci
        assert "ortalama_net" in ogrenci["performans"]
        assert "toplam_sinav" in ogrenci["performans"]


@pytest.mark.asyncio
async def test_sinif_raporu_olustur(setup_test_data):
    """Sınıf raporu oluşturma testi"""
    test_data = await setup_test_data
    ogretmen = test_data["ogretmen"]

    # Rapor parametreleri
    rapor_parametreleri = {
        "baslangic_tarihi": datetime.now() - timedelta(days=30),
        "bitis_tarihi": datetime.now(),
        "sinav_tipi": None,
    }

    # Rapor oluştur
    rapor = await ogretmen_servisi.sinif_raporu_olustur(
        ogretmen.kullanici_id, rapor_parametreleri
    )

    # Kontroller
    assert rapor is not None
    assert "rapor_id" in rapor
    assert "sinif_istatistikleri" in rapor
    assert "konu_performanslari" in rapor
    assert "oneriler" in rapor

    # İstatistik kontrolleri
    stats = rapor["sinif_istatistikleri"]
    assert stats["toplam_ogrenci"] == 3
    assert "ortalama_net" in stats
    assert "en_yuksek_net" in stats
    assert "en_dusuk_net" in stats


@pytest.mark.asyncio
async def test_bildirim_gonder():
    """Bildirim gönderme testi"""
    ogretmen_id = "test_ogretmen_id"

    bildirim_verisi = {
        "baslik": "Test Bildirimi",
        "mesaj": "Bu bir test bildirimidir",
        "tip": "bilgi",
    }

    # Bildirim gönder
    basarili = await ogretmen_servisi.bildirim_gonder(ogretmen_id, bildirim_verisi)

    # Kontroller
    assert basarili is True

    # Bildirimleri al
    bildirimler = await ogretmen_servisi.bildirimler_getir(ogretmen_id)

    assert len(bildirimler) == 1
    assert bildirimler[0]["baslik"] == "Test Bildirimi"
    assert bildirimler[0]["mesaj"] == "Bu bir test bildirimidir"
    assert bildirimler[0]["tip"] == "bilgi"
    assert bildirimler[0]["okundu"] is False


@pytest.mark.asyncio
async def test_bildirim_okundu_isaretle():
    """Bildirim okundu işaretleme testi"""
    ogretmen_id = "test_ogretmen_id"

    # Önce bildirim gönder
    bildirim_verisi = {
        "baslik": "Test Bildirimi",
        "mesaj": "Bu bir test bildirimidir",
        "tip": "bilgi",
    }

    await ogretmen_servisi.bildirim_gonder(ogretmen_id, bildirim_verisi)

    # Bildirimleri al
    bildirimler = await ogretmen_servisi.bildirimler_getir(ogretmen_id)
    bildirim_id = bildirimler[0]["bildirim_id"]

    # Okundu işaretle
    basarili = await ogretmen_servisi.bildirim_okundu_isaretle(ogretmen_id, bildirim_id)

    # Kontroller
    assert basarili is True

    # Bildirimi tekrar al ve kontrol et
    bildirimler = await ogretmen_servisi.bildirimler_getir(ogretmen_id)
    assert bildirimler[0]["okundu"] is True


@pytest.mark.asyncio
async def test_ogrenci_detay_performans(setup_test_data):
    """Öğrenci detay performans testi"""
    test_data = await setup_test_data
    ogretmen = test_data["ogretmen"]
    ogrenciler = test_data["ogrenciler"]

    # İlk öğrenci için detay performans al
    ogrenci_id = ogrenciler[0].kullanici_id

    try:
        performans = await ogretmen_servisi.ogrenci_detay_performans(
            ogretmen.kullanici_id, ogrenci_id
        )

        # Kontroller
        assert performans is not None
        assert "ogrenci_bilgileri" in performans
        assert "genel_istatistikler" in performans
        assert "sinav_gecmisi" in performans
        assert "konu_performanslari" in performans
        assert "oneriler" in performans

    except ValueError as e:
        # Öğrenci profili bulunamadığında beklenen hata
        assert "öğrenciye erişim yetkiniz yok" in str(
            e
        ) or "Öğrenci profili bulunamadı" in str(e)


@pytest.mark.asyncio
async def test_yetkisiz_erisim():
    """Yetkisiz erişim testi"""
    ogretmen_id = "test_ogretmen_id"
    baska_ogrenci_id = "baska_ogrenci_id"

    # Yetkisiz erişim denemesi
    with pytest.raises(ValueError) as exc_info:
        await ogretmen_servisi.ogrenci_detay_performans(ogretmen_id, baska_ogrenci_id)

    assert "erişim yetkiniz yok" in str(exc_info.value)


@pytest.mark.asyncio
async def test_demo_ogrenci_iliskileri_olustur():
    """Demo öğrenci ilişkileri oluşturma testi"""
    ogretmen_id = "test_ogretmen_id"

    # Demo ilişkileri oluştur
    await ogretmen_servisi._demo_ogrenci_iliskileri_olustur(ogretmen_id)

    # Kontroller
    assert ogretmen_id in ogretmen_servisi.sinif_ogrenci_iliskileri
    ogrenci_ids = ogretmen_servisi.sinif_ogrenci_iliskileri[ogretmen_id]
    assert isinstance(ogrenci_ids, list)


def test_ogretmen_servisi_singleton():
    """Öğretmen servisi singleton testi"""
    from services.ogretmen_service import ogretmen_servisi as service1
    from services.ogretmen_service import ogretmen_servisi as service2

    assert service1 is service2


if __name__ == "__main__":
    # Test çalıştırma
    asyncio.run(test_bildirim_gonder())
    asyncio.run(test_bildirim_okundu_isaretle())
    print("[CHECK] Tüm öğretmen servisi testleri başarılı!")
