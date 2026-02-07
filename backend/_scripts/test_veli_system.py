"""
Veli takip sistemi testleri
"""
import asyncio

import pytest

from models import KullaniciOlustur, KullaniciRolu, OgrenciProfili, VeliProfili
from services.user_service import kullanici_servisi
from services.veli_service import VeliOnayTalebi, VeliRaporu, veli_servisi


class TestVeliSistemi:
    """Veli takip sistemi test sınıfı"""

    @pytest.fixture
    async def setup_test_data(self):
        """Test verileri hazırla"""
        # Veli kullanıcısı oluştur
        veli_data = KullaniciOlustur(
            email="veli@test.com",
            ad_soyad="Ahmet Yılmaz",
            sifre="123456",
            rol=KullaniciRolu.VELI,
            telefon="05551234567",
        )
        veli_kullanici = await kullanici_servisi.kullanici_olustur(veli_data)

        # Öğrenci kullanıcısı oluştur
        ogrenci_data = KullaniciOlustur(
            email="ogrenci@test.com",
            ad_soyad="Mehmet Yılmaz",
            sifre="123456",
            rol=KullaniciRolu.OGRENCI,
            telefon="05559876543",
        )
        ogrenci_kullanici = await kullanici_servisi.kullanici_olustur(ogrenci_data)

        # Veli profili oluştur
        veli_profil = VeliProfili(
            veli_id=veli_kullanici.kullanici_id,
            kullanici_id=veli_kullanici.kullanici_id,
            cocuk_ogrenci_ids=[ogrenci_kullanici.kullanici_id],
            email_bildirimleri=True,
            sms_bildirimleri=False,
        )
        await kullanici_servisi.veli_profili_olustur(veli_profil)

        # Öğrenci profili oluştur
        ogrenci_profil = OgrenciProfili(
            ogrenci_id=ogrenci_kullanici.kullanici_id,
            kullanici_id=ogrenci_kullanici.kullanici_id,
            sinif_seviyesi=11,
            okul_adi="Test Lisesi",
            hedef_sinav="TYT",
            veli_onay=True,
            veli_kullanici_id=veli_kullanici.kullanici_id,
        )
        await kullanici_servisi.ogrenci_profili_olustur(ogrenci_profil)

        return {
            "veli_id": veli_kullanici.kullanici_id,
            "ogrenci_id": ogrenci_kullanici.kullanici_id,
            "veli_kullanici": veli_kullanici,
            "ogrenci_kullanici": ogrenci_kullanici,
        }

    @pytest.mark.asyncio
    async def test_veli_cocuklarini_getir(self, setup_test_data):
        """Veli çocuk listesi testi"""
        test_data = await setup_test_data
        veli_id = test_data["veli_id"]

        # Çocuk listesini getir
        cocuklar = await veli_servisi.veli_cocuklarini_getir(veli_id)

        # Doğrulamalar
        assert len(cocuklar) == 1
        assert cocuklar[0]["ad_soyad"] == "Mehmet Yılmaz"
        assert cocuklar[0]["sinif_seviyesi"] == 11
        assert cocuklar[0]["okul_adi"] == "Test Lisesi"
        assert cocuklar[0]["veli_onay"] == True

    @pytest.mark.asyncio
    async def test_cocuk_performansini_getir(self, setup_test_data):
        """Çocuk performans verisi testi"""
        test_data = await setup_test_data
        veli_id = test_data["veli_id"]
        ogrenci_id = test_data["ogrenci_id"]

        # Performans verilerini getir
        performans = await veli_servisi.cocuk_performansini_getir(veli_id, ogrenci_id)

        # Doğrulamalar
        assert performans["ogrenci_id"] == ogrenci_id
        assert "son_30_gun" in performans
        assert "konu_performanslari" in performans
        assert "gelisim_trendi" in performans
        assert performans["son_30_gun"]["toplam_calisma_suresi"] > 0
        assert len(performans["konu_performanslari"]) > 0

    @pytest.mark.asyncio
    async def test_haftalik_rapor_olustur(self, setup_test_data):
        """Haftalık rapor oluşturma testi"""
        test_data = await setup_test_data
        veli_id = test_data["veli_id"]
        ogrenci_id = test_data["ogrenci_id"]

        # Haftalık rapor oluştur
        rapor = await veli_servisi.haftalik_rapor_olustur(veli_id, ogrenci_id)

        # Doğrulamalar
        assert isinstance(rapor, VeliRaporu)
        assert rapor.ogrenci_id == ogrenci_id
        assert rapor.ogrenci_ad_soyad == "Mehmet Yılmaz"
        assert rapor.toplam_calisma_suresi > 0
        assert rapor.ortalama_basari_orani > 0
        assert len(rapor.en_basarili_konular) > 0
        assert len(rapor.veli_onerileri) > 0

        # Rapor tarih aralığı kontrolü
        bitis_tarihi = rapor.bitis_tarihi
        baslangic_tarihi = rapor.baslangic_tarihi
        assert (bitis_tarihi - baslangic_tarihi).days == 7

    @pytest.mark.asyncio
    async def test_onay_talebi_olustur(self, setup_test_data):
        """Onay talebi oluşturma testi"""
        test_data = await setup_test_data
        ogrenci_id = test_data["ogrenci_id"]

        # Onay talebi oluştur
        talep = await veli_servisi.onay_talebi_olustur(
            ogrenci_id=ogrenci_id,
            talep_tipi="sinav_kayit",
            aciklama="YKS denemesi için kayıt olmak istiyorum",
        )

        # Doğrulamalar
        assert isinstance(talep, VeliOnayTalebi)
        assert talep.ogrenci_id == ogrenci_id
        assert talep.talep_tipi == "sinav_kayit"
        assert talep.durum == "beklemede"
        assert talep.talep_aciklamasi == "YKS denemesi için kayıt olmak istiyorum"

    @pytest.mark.asyncio
    async def test_onay_talebi_yanitla(self, setup_test_data):
        """Onay talebi yanıtlama testi"""
        test_data = await setup_test_data
        veli_id = test_data["veli_id"]
        ogrenci_id = test_data["ogrenci_id"]

        # Önce onay talebi oluştur
        talep = await veli_servisi.onay_talebi_olustur(
            ogrenci_id=ogrenci_id,
            talep_tipi="ek_ders",
            aciklama="Matematik ek dersi almak istiyorum",
        )

        # Onay talebi yanıtla (onayla)
        yanit = await veli_servisi.onay_talebi_yanitla(
            veli_id=veli_id,
            talep_id=talep.talep_id,
            onay=True,
            not_="Matematik notların düşük, ek ders alabilirsin",
        )

        # Doğrulamalar
        assert yanit.durum == "onaylandi"
        assert yanit.veli_notu == "Matematik notların düşük, ek ders alabilirsin"
        assert yanit.yanit_tarihi is not None

        # Reddetme testi
        talep2 = await veli_servisi.onay_talebi_olustur(
            ogrenci_id=ogrenci_id,
            talep_tipi="oyun_satın_alma",
            aciklama="Yeni oyun almak istiyorum",
        )

        yanit2 = await veli_servisi.onay_talebi_yanitla(
            veli_id=veli_id,
            talep_id=talep2.talep_id,
            onay=False,
            not_="Önce derslerine odaklan",
        )

        assert yanit2.durum == "reddedildi"
        assert yanit2.veli_notu == "Önce derslerine odaklan"

    @pytest.mark.asyncio
    async def test_veli_bildirimleri(self, setup_test_data):
        """Veli bildirim sistemi testi"""
        test_data = await setup_test_data
        veli_id = test_data["veli_id"]
        ogrenci_id = test_data["ogrenci_id"]

        # Onay talebi oluştur (bu bildirim gönderecek)
        await veli_servisi.onay_talebi_olustur(
            ogrenci_id=ogrenci_id,
            talep_tipi="sinav_kayit",
            aciklama="Test sınavı için kayıt",
        )

        # Bildirimleri getir
        bildirimler = await veli_servisi.veli_bildirimlerini_getir(veli_id)

        # Doğrulamalar
        assert len(bildirimler) > 0
        assert bildirimler[0].baslik == "Onay Talebi"
        assert bildirimler[0].tip == "uyari"
        assert not bildirimler[0].okundu

        # Bildirimi okundu işaretle
        bildirim_id = bildirimler[0].bildirim_id
        basarili = await veli_servisi.bildirim_okundu_isaretle(veli_id, bildirim_id)

        assert basarili == True

        # Güncellenmiş bildirimleri kontrol et
        guncel_bildirimler = await veli_servisi.veli_bildirimlerini_getir(veli_id)
        assert guncel_bildirimler[0].okundu == True

    @pytest.mark.asyncio
    async def test_yetki_kontrolu(self, setup_test_data):
        """Veli yetki kontrolü testi"""
        test_data = await setup_test_data

        # Başka bir veli oluştur
        baska_veli_data = KullaniciOlustur(
            email="baska_veli@test.com",
            ad_soyad="Ayşe Demir",
            sifre="123456",
            rol=KullaniciRolu.VELI,
        )
        baska_veli = await kullanici_servisi.kullanici_olustur(baska_veli_data)

        # Başka veli profili oluştur
        baska_veli_profil = VeliProfili(
            veli_id=baska_veli.kullanici_id,
            kullanici_id=baska_veli.kullanici_id,
            cocuk_ogrenci_ids=[],  # Boş çocuk listesi
            email_bildirimleri=True,
        )
        await kullanici_servisi.veli_profili_olustur(baska_veli_profil)

        # Yetkisiz erişim testi
        with pytest.raises(ValueError, match="Bu öğrenci üzerinde yetkiniz yok"):
            await veli_servisi.cocuk_performansini_getir(
                baska_veli.kullanici_id, test_data["ogrenci_id"]
            )

    @pytest.mark.asyncio
    async def test_performans_verisi_detaylari(self, setup_test_data):
        """Performans verisi detayları testi"""
        test_data = await setup_test_data
        veli_id = test_data["veli_id"]
        ogrenci_id = test_data["ogrenci_id"]

        # Performans verilerini getir
        performans = await veli_servisi.cocuk_performansini_getir(veli_id, ogrenci_id)

        # Detaylı doğrulamalar
        son_30_gun = performans["son_30_gun"]
        assert son_30_gun["toplam_calisma_suresi"] == 1800  # 30 saat
        assert son_30_gun["tamamlanan_sinav_sayisi"] == 12
        assert son_30_gun["ortalama_basari_orani"] == 76.3
        assert len(son_30_gun["en_aktif_gunler"]) == 3

        # Konu performansları
        konu_performanslari = performans["konu_performanslari"]
        assert "Matematik" in konu_performanslari
        assert "Türkçe" in konu_performanslari
        assert konu_performanslari["Matematik"]["basari_orani"] > 0
        assert konu_performanslari["Matematik"]["calisma_suresi"] > 0

        # Gelişim trendi
        gelisim_trendi = performans["gelisim_trendi"]
        assert "son_hafta" in gelisim_trendi
        assert "son_ay" in gelisim_trendi
        assert gelisim_trendi["genel_trend"] == "yukselme"

        # Zayıf ve güçlü konular
        assert len(performans["zayif_konular"]) > 0
        assert len(performans["guclu_konular"]) > 0
        assert len(performans["son_sinavlar"]) > 0


def test_veli_sistemi_sync():
    """Senkron test wrapper"""
    test_instance = TestVeliSistemi()

    async def run_tests():
        # Test verilerini hazırla
        setup_data = await test_instance.setup_test_data()

        # Testleri çalıştır
        await test_instance.test_veli_cocuklarini_getir(setup_data)
        await test_instance.test_cocuk_performansini_getir(setup_data)
        await test_instance.test_haftalik_rapor_olustur(setup_data)
        await test_instance.test_onay_talebi_olustur(setup_data)
        await test_instance.test_onay_talebi_yanitla(setup_data)
        await test_instance.test_veli_bildirimleri(setup_data)
        await test_instance.test_yetki_kontrolu(setup_data)
        await test_instance.test_performans_verisi_detaylari(setup_data)

        print("[CHECK] Tüm veli sistemi testleri başarıyla tamamlandı!")
        return True

    # Async testleri çalıştır
    return asyncio.run(run_tests())


if __name__ == "__main__":
    # Testleri çalıştır
    sonuc = test_veli_sistemi_sync()
    if sonuc:
        print("[PARTY] Veli takip sistemi başarıyla test edildi!")
    else:
        print("[X] Testlerde hata oluştu!")
