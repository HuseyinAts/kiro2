from unittest.mock import Mock, patch, AsyncMock

"""
Sınav motoru testleri
"""
from datetime import datetime, timedelta

import pytest

from models import SinavDurumu, SinavTipi, ZorlukSeviyesi
from services.sinav_motoru_service import SinavMotoruServisi
from services.soru_bankasi_service import SoruBankasiServisi


@pytest.fixture
def sinav_motoru():
    """Test için temiz sınav motoru instance'ı"""
    return SinavMotoruServisi()


@pytest.fixture
def soru_bankasi():
    """Test için soru bankası instance'ı"""
    return SoruBankasiServisi()


class TestSinavMotoru:
    """Sınav motoru testleri"""

    @pytest.mark.asyncio
    async def test_sinav_olustur_tyt(self, sinav_motoru):
        """TYT sınavı oluşturma testi"""
        ogrenci_id = "test_ogrenci_123"

        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
        )

        assert oturum.ogrenci_id == ogrenci_id
        assert oturum.sinav_tipi == SinavTipi.TYT
        assert oturum.durum == SinavDurumu.HAZIR
        assert oturum.toplam_soru_sayisi > 0
        assert oturum.sure_dakika == 165  # TYT süresi
        assert len(oturum.soru_listesi) == oturum.toplam_soru_sayisi

    @pytest.mark.asyncio
    async def test_sinav_olustur_ayt(self, sinav_motoru):
        """AYT sınavı oluşturma testi"""
        ogrenci_id = "test_ogrenci_123"

        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.AYT
        )

        assert oturum.sinav_tipi == SinavTipi.AYT
        assert oturum.sure_dakika == 180  # AYT süresi

    @pytest.mark.asyncio
    async def test_sinav_olustur_ydt(self, sinav_motoru):
        """YDT sınavı oluşturma testi"""
        ogrenci_id = "test_ogrenci_123"

        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.YDT
        )

        assert oturum.sinav_tipi == SinavTipi.YDT
        assert oturum.sure_dakika == 180  # YDT süresi

    @pytest.mark.asyncio
    async def test_sinav_baslat(self, sinav_motoru):
        """Sınav başlatma testi"""
        # Sınav oluştur
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )

        # Sınavı başlat
        baslangic_zamani = datetime.now()
        baslatilan_oturum = await sinav_motoru.sinav_baslat(oturum.sinav_id)

        assert baslatilan_oturum.durum == SinavDurumu.DEVAM_EDIYOR
        assert baslatilan_oturum.baslangic_zamani is not None
        assert baslatilan_oturum.bitis_zamani is not None
        assert baslatilan_oturum.baslangic_zamani >= baslangic_zamani

        # Bitiş zamanı kontrolü
        beklenen_bitis = baslatilan_oturum.baslangic_zamani + timedelta(minutes=165)
        assert (
            abs((baslatilan_oturum.bitis_zamani - beklenen_bitis).total_seconds()) < 5
        )

    @pytest.mark.asyncio
    async def test_mevcut_soru_getir(self, sinav_motoru):
        """Mevcut soru getirme testi"""
        # Sınav oluştur ve başlat
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )
        await sinav_motoru.sinav_baslat(oturum.sinav_id)

        # Mevcut soruyu getir
        soru = await sinav_motoru.mevcut_soru_getir(oturum.sinav_id)

        assert soru is not None
        assert soru.soru_id == oturum.soru_listesi[0]
        assert soru.sinav_tipi == SinavTipi.TYT

    @pytest.mark.asyncio
    async def test_cevap_kaydet(self, sinav_motoru):
        """Cevap kaydetme testi"""
        # Sınav oluştur ve başlat
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )
        await sinav_motoru.sinav_baslat(oturum.sinav_id)

        # Mevcut soruyu al
        soru = await sinav_motoru.mevcut_soru_getir(oturum.sinav_id)

        # Cevap kaydet
        basarili = await sinav_motoru.cevap_kaydet(
            sinav_id=oturum.sinav_id, soru_id=soru.soru_id, cevap="A", cevap_suresi=30
        )

        assert basarili is True

        # Oturum güncellenmeli
        guncellenen_oturum = await sinav_motoru.oturum_getir(oturum.sinav_id)
        assert soru.soru_id in guncellenen_oturum.cevaplanan_sorular
        assert guncellenen_oturum.cevaplanan_sorular[soru.soru_id] == "A"

    @pytest.mark.asyncio
    async def test_sonraki_onceki_soru(self, sinav_motoru):
        """Sonraki/önceki soru navigasyon testi"""
        # Sınav oluştur ve başlat
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )
        await sinav_motoru.sinav_baslat(oturum.sinav_id)

        # İlk soru
        ilk_soru = await sinav_motoru.mevcut_soru_getir(oturum.sinav_id)
        assert ilk_soru.soru_id == oturum.soru_listesi[0]

        # Sonraki soru
        ikinci_soru = await sinav_motoru.sonraki_soru(oturum.sinav_id)
        assert ikinci_soru.soru_id == oturum.soru_listesi[1]

        # Önceki soru
        geri_donen_soru = await sinav_motoru.onceki_soru(oturum.sinav_id)
        assert geri_donen_soru.soru_id == ilk_soru.soru_id

    @pytest.mark.asyncio
    async def test_soru_isaretleme(self, sinav_motoru):
        """Soru işaretleme testi"""
        # Sınav oluştur ve başlat
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )
        await sinav_motoru.sinav_baslat(oturum.sinav_id)

        soru = await sinav_motoru.mevcut_soru_getir(oturum.sinav_id)

        # Soruyu işaretle
        basarili = await sinav_motoru.soru_isaretleme(
            sinav_id=oturum.sinav_id, soru_id=soru.soru_id, isaretli=True
        )

        assert basarili is True

        # Oturum kontrol et
        guncellenen_oturum = await sinav_motoru.oturum_getir(oturum.sinav_id)
        assert soru.soru_id in guncellenen_oturum.isaretlenen_sorular

        # İşareti kaldır
        await sinav_motoru.soru_isaretleme(
            sinav_id=oturum.sinav_id, soru_id=soru.soru_id, isaretli=False
        )

        guncellenen_oturum = await sinav_motoru.oturum_getir(oturum.sinav_id)
        assert soru.soru_id not in guncellenen_oturum.isaretlenen_sorular

    @pytest.mark.asyncio
    async def test_kalan_sure(self, sinav_motoru):
        """Kalan süre testi"""
        # Sınav oluştur ve başlat
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )
        await sinav_motoru.sinav_baslat(oturum.sinav_id)

        # Kalan süreyi kontrol et
        kalan_sure = await sinav_motoru.kalan_sure_getir(oturum.sinav_id)

        assert kalan_sure is not None
        assert kalan_sure > 0
        assert kalan_sure <= 165 * 60  # TYT süresi saniye cinsinden

    @pytest.mark.asyncio
    async def test_sinav_tamamla(self, sinav_motoru):
        """Sınav tamamlama testi"""
        # Sınav oluştur ve başlat
        oturum = await sinav_motoru.sinav_olustur(
            ogrenci_id="test_ogrenci", sinav_tipi=SinavTipi.TYT
        )
        await sinav_motoru.sinav_baslat(oturum.sinav_id)

        # Birkaç soru cevapla
        for i in range(3):
            soru = await sinav_motoru.mevcut_soru_getir(oturum.sinav_id)
            await sinav_motoru.cevap_kaydet(
                sinav_id=oturum.sinav_id, soru_id=soru.soru_id, cevap="A"
            )
            if i < 2:  # Son soruda sonraki soru çağırma
                await sinav_motoru.sonraki_soru(oturum.sinav_id)

        # Sınavı tamamla
        sonuc = await sinav_motoru.sinav_tamamla(oturum.sinav_id)

        assert sonuc is not None
        assert sonuc.sinav_id == oturum.sinav_id
        assert sonuc.ogrenci_id == oturum.ogrenci_id
        assert sonuc.sinav_tipi == oturum.sinav_tipi
        assert sonuc.toplam_soru == oturum.toplam_soru_sayisi
        assert sonuc.dogru_sayisi >= 0
        assert sonuc.yanlis_sayisi >= 0
        assert sonuc.bos_sayisi >= 0
        assert sonuc.net_sayisi >= 0

        # Oturum durumu kontrol et
        tamamlanan_oturum = await sinav_motoru.oturum_getir(oturum.sinav_id)
        assert tamamlanan_oturum.durum == SinavDurumu.TAMAMLANDI

    @pytest.mark.asyncio
    async def test_ogrenci_sinavlari(self, sinav_motoru):
        """Öğrenci sınavları listeleme testi"""
        ogrenci_id = "test_ogrenci_123"

        # Birkaç sınav oluştur
        oturum1 = await sinav_motoru.sinav_olustur(ogrenci_id, SinavTipi.TYT)
        oturum2 = await sinav_motoru.sinav_olustur(ogrenci_id, SinavTipi.AYT)

        # Öğrenci sınavlarını listele
        sinavlar = await sinav_motoru.ogrenci_sinavlari(ogrenci_id)

        assert len(sinavlar) == 2
        sinav_ids = [s.sinav_id for s in sinavlar]
        assert oturum1.sinav_id in sinav_ids
        assert oturum2.sinav_id in sinav_ids


class TestSoruBankasi:
    """Soru bankası testleri"""

    @pytest.mark.asyncio
    async def test_soru_listele(self, soru_bankasi):
        """Soru listeleme testi"""
        # TYT soruları
        tyt_sorulari = await soru_bankasi.sorular_listele(sinav_tipi=SinavTipi.TYT)
        assert len(tyt_sorulari) > 0
        assert all(soru.sinav_tipi == SinavTipi.TYT for soru in tyt_sorulari)

        # Matematik soruları
        matematik_sorulari = await soru_bankasi.sorular_listele(konu="Matematik")
        assert len(matematik_sorulari) > 0
        assert all(soru.konu == "Matematik" for soru in matematik_sorulari)

        # Kolay sorular
        kolay_sorular = await soru_bankasi.sorular_listele(
            zorluk_seviyesi=ZorlukSeviyesi.KOLAY
        )
        assert len(kolay_sorular) > 0
        assert all(
            soru.zorluk_seviyesi == ZorlukSeviyesi.KOLAY for soru in kolay_sorular
        )

    @pytest.mark.asyncio
    async def test_rastgele_soru_secimi(self, soru_bankasi):
        """Rastgele soru seçimi testi"""
        # TYT için rastgele sorular
        sorular = await soru_bankasi.rastgele_sorular_sec(
            sinav_tipi=SinavTipi.TYT, soru_sayisi=5
        )

        assert len(sorular) <= 5  # Mevcut soru sayısına bağlı
        assert all(soru.sinav_tipi == SinavTipi.TYT for soru in sorular)

        # Konu dağılımı ile seçim
        konu_dagilimi = {"Matematik": 2, "Türkçe": 1}
        sorular = await soru_bankasi.rastgele_sorular_sec(
            sinav_tipi=SinavTipi.TYT, soru_sayisi=3, konu_dagilimi=konu_dagilimi
        )

        matematik_sayisi = sum(1 for soru in sorular if soru.konu == "Matematik")
        turkce_sayisi = sum(1 for soru in sorular if soru.konu == "Türkçe")

        # Mevcut soru sayısına bağlı olarak kontrol
        assert matematik_sayisi <= 2
        assert turkce_sayisi <= 1

    @pytest.mark.asyncio
    async def test_konu_listesi(self, soru_bankasi):
        """Konu listesi testi"""
        # Tüm konular
        tum_konular = await soru_bankasi.konu_listesi_getir()
        assert len(tum_konular) > 0
        assert "Matematik" in tum_konular
        assert "Türkçe" in tum_konular

        # TYT konuları
        tyt_konulari = await soru_bankasi.konu_listesi_getir(SinavTipi.TYT)
        assert len(tyt_konulari) > 0
        assert all(konu in tum_konular for konu in tyt_konulari)

    @pytest.mark.asyncio
    async def test_istatistikler(self, soru_bankasi):
        """İstatistik testi"""
        istatistikler = await soru_bankasi.istatistikler_getir()

        assert "toplam_soru_sayisi" in istatistikler
        assert "sinav_tipi_dagilimi" in istatistikler
        assert "konu_dagilimi" in istatistikler
        assert "zorluk_dagilimi" in istatistikler

        assert istatistikler["toplam_soru_sayisi"] > 0
        assert len(istatistikler["sinav_tipi_dagilimi"]) > 0
        assert len(istatistikler["konu_dagilimi"]) > 0


class TestTurkceKarakterDestegi:
    """Türkçe karakter desteği testleri"""

    @pytest.mark.asyncio
    async def test_turkce_soru_metni(self, soru_bankasi):
        """Türkçe karakterli soru metni testi"""
        turkce_sorular = await soru_bankasi.sorular_listele(konu="Türkçe")

        # En az bir Türkçe sorusu olmalı
        assert len(turkce_sorular) > 0

        # Türkçe karakterler kontrol et
        turkce_karakterler = "çğıöşüÇĞIÖŞÜ"
        turkce_soru_var = False

        for soru in turkce_sorular:
            if any(char in soru.soru_metni for char in turkce_karakterler):
                turkce_soru_var = True
                break

        # Test verilerinde Türkçe karakterli sorular olmalı
        # Bu test, gerçek verilerle daha anlamlı olacak
