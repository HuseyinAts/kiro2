# -*- coding: utf-8 -*-
"""
Test - Sinav Motoru Service - OSYM Uyumlu Sinav Sistemi
Coverage hedefi: %85+
Kritik: TYT/AYT/YDT formatlari, Net hesaplama, Oturum yonetimi
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.sinav_motoru_service import SinavMotoruServisi
from models import SinavTipi, SinavDurumu


class TestSinavOlusturma:
    """Sinav olusturma testleri"""

    @pytest.fixture
    def service(self):
        """Test icin servis ornegi"""
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    async def test_tyt_sinav_olusturma_temel(self, service):
        """TYT sinavi olusturma - temel test"""
        ogrenci_id = "test_ogrenci_001"

        # Mock soru bankasi
        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_soru_service:
            # rastgele_sorular_sec metodunu mock'la
            mock_soru_service.rastgele_sorular_sec = AsyncMock(
                return_value=[
                    Mock(soru_id=f"soru_{i}", konu="Matematik") for i in range(120)
                ]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        # Dogrulamalar
        assert oturum is not None
        assert oturum.sinav_tipi == SinavTipi.TYT
        assert oturum.ogrenci_id == ogrenci_id
        assert oturum.toplam_soru_sayisi == 120
        assert oturum.sure_dakika == 165
        assert oturum.durum == SinavDurumu.HAZIR
        assert len(oturum.soru_listesi) == 120

    @pytest.mark.asyncio
    async def test_ayt_sinav_olusturma_temel(self, service):
        """AYT sinavi olusturma - temel test"""
        ogrenci_id = "test_ogrenci_002"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[
                    Mock(soru_id=f"soru_{i}", konu="Matematik") for i in range(80)
                ]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.AYT
            )

        assert oturum.sinav_tipi == SinavTipi.AYT
        assert oturum.toplam_soru_sayisi == 80
        assert oturum.sure_dakika == 180
        assert oturum.durum == SinavDurumu.HAZIR

    @pytest.mark.asyncio
    async def test_ydt_sinav_olusturma_temel(self, service):
        """YDT sinavi olusturma - temel test"""
        ogrenci_id = "test_ogrenci_003"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[
                    Mock(soru_id=f"soru_{i}", konu="Ingilizce") for i in range(80)
                ]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.YDT
            )

        assert oturum.sinav_tipi == SinavTipi.YDT
        assert oturum.toplam_soru_sayisi == 80
        assert oturum.sure_dakika == 180
        assert oturum.durum == SinavDurumu.HAZIR

    @pytest.mark.asyncio
    async def test_tyt_konu_dagilimi(self, service):
        """TYT konu dagilimi dogrulamasi"""
        config = service.sinav_konfigurasyonlari[SinavTipi.TYT]
        konu_dagilimi = config.get("konu_dagilimi")

        assert konu_dagilimi is not None
        assert konu_dagilimi["Türkçe"] == 40
        assert konu_dagilimi["Matematik"] == 40
        assert konu_dagilimi["Fen Bilimleri"] == 20
        assert konu_dagilimi["Sosyal Bilimler"] == 20

    @pytest.mark.asyncio
    async def test_ayt_konu_dagilimi(self, service):
        """AYT konu dagilimi dogrulamasi"""
        config = service.sinav_konfigurasyonlari[SinavTipi.AYT]
        konu_dagilimi = config.get("konu_dagilimi")

        assert konu_dagilimi["Matematik"] == 40
        assert konu_dagilimi["Fizik"] == 14
        assert konu_dagilimi["Kimya"] == 13
        assert konu_dagilimi["Biyoloji"] == 13

    @pytest.mark.asyncio
    async def test_ozel_konfigurasyon(self, service):
        """Ozel sinav konfigurasyonu"""
        ogrenci_id = "test_ogrenci_005"

        ozel_config = {"toplam_soru": 50, "sure_dakika": 60}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(50)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar=ozel_config,
            )

        assert oturum.toplam_soru_sayisi == 50
        assert oturum.sure_dakika == 60

    @pytest.mark.asyncio
    async def test_sinav_id_benzersizligi(self, service):
        """Her sinav benzersiz ID aliyor mu?"""
        ogrenci_id = "test_ogrenci_006"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(120)]
            )

            oturum1 = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

            oturum2 = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        assert oturum1.sinav_id != oturum2.sinav_id

    @pytest.mark.asyncio
    async def test_oturum_kayit_edildi_mi(self, service):
        """Olusturulan oturum aktif oturumlara kaydediliyor mu?"""
        ogrenci_id = "test_ogrenci_007"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(120)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        # Aktif oturumlarda kayitli mi?
        assert oturum.sinav_id in service.aktif_oturumlar

        # Cevaplar listesi olusturulmus mu?
        assert oturum.sinav_id in service.sinav_cevaplari
        assert service.sinav_cevaplari[oturum.sinav_id] == []


class TestSinavBaslatma:
    """Sinav baslatma testleri"""

    @pytest.fixture
    def service(self):
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    async def test_sinav_baslat_basarili(self, service):
        """Sinav baslatma - basarili senaryo"""
        ogrenci_id = "test_ogrenci_010"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(120)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        sinav_id = oturum.sinav_id

        # WebSocket mock'u
        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            # Otomatik tamamlama task'i mock'la
            with patch("asyncio.create_task"):
                # Sinavi baslat
                baslayan_oturum = await service.sinav_baslat(sinav_id)

        assert baslayan_oturum.durum == SinavDurumu.DEVAM_EDIYOR
        assert baslayan_oturum.baslangic_zamani is not None
        assert baslayan_oturum.bitis_zamani is not None
        assert baslayan_oturum.kalan_sure == 165 * 60  # 165 dakika = 9900 saniye

    @pytest.mark.asyncio
    async def test_sinav_baslat_bitis_zamani_hesaplama(self, service):
        """Bitis zamani dogru hesaplaniyor mu?"""
        ogrenci_id = "test_ogrenci_011"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(120)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                baslayan_oturum = await service.sinav_baslat(oturum.sinav_id)

        # Bitis zamani baslangic + sure olmali
        expected_bitis = baslayan_oturum.baslangic_zamani + timedelta(minutes=165)

        # 1 saniyelik tolerans
        time_diff = abs((baslayan_oturum.bitis_zamani - expected_bitis).total_seconds())
        assert time_diff < 1

    @pytest.mark.asyncio
    async def test_sinav_baslat_bulunamadi_hatasi(self, service):
        """Olmayan sinav ID'si ile baslatma hatasi"""
        with pytest.raises(ValueError, match="bulunamadı"):
            await service.sinav_baslat("olmayan_sinav_id")

    @pytest.mark.asyncio
    async def test_sinav_baslat_zaten_baslamis_hatasi(self, service):
        """Zaten baslamis sinavi tekrar baslatma hatasi"""
        ogrenci_id = "test_ogrenci_012"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(120)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        # Ilk baslatma
        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Ikinci baslatma - hata vermeli
        with pytest.raises(ValueError):
            await service.sinav_baslat(oturum.sinav_id)


class TestCevapKaydetme:
    """Cevap kaydetme testleri"""

    @pytest.fixture
    def service(self):
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    async def test_cevap_kaydet_basarili(self, service):
        """Cevap kaydetme - basarili"""
        ogrenci_id = "test_ogrenci_020"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"soru_{i}") for i in range(10)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 10},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Cevap kaydet
        sonuc = await service.cevap_kaydet(
            sinav_id=oturum.sinav_id, soru_id="soru_0", cevap="A", cevap_suresi=30
        )

        assert sonuc is True
        assert len(service.sinav_cevaplari[oturum.sinav_id]) == 1
        assert "soru_0" in oturum.cevaplanan_sorular
        assert oturum.cevaplanan_sorular["soru_0"] == "A"

    @pytest.mark.asyncio
    async def test_cevap_kaydet_bos_cevap(self, service):
        """Bos cevap kaydetme"""
        ogrenci_id = "test_ogrenci_021"

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"soru_{i}") for i in range(10)]
            )

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 10},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Bos cevap kaydet
        sonuc = await service.cevap_kaydet(
            sinav_id=oturum.sinav_id, soru_id="soru_0", cevap=None
        )

        assert sonuc is True
        # Bos cevap cevaplanan_sorular'a eklenmemeli
        assert "soru_0" not in oturum.cevaplanan_sorular


class TestPerformans:
    """Performans testleri"""

    @pytest.fixture
    def service(self):
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_coklu_sinav_olusturma_performans(self, service):
        """10 sinav olusturma hizi"""
        import time

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(
                return_value=[Mock(soru_id=f"s_{i}") for i in range(120)]
            )

            start = time.time()

            for i in range(10):
                await service.sinav_olustur(
                    ogrenci_id=f"perf_test_{i}", sinav_tipi=SinavTipi.TYT
                )

            elapsed = time.time() - start

        print(f"\n10 sinav olusturma suresi: {elapsed:.3f}s")
        # 10 sinav < 1 saniye
        assert elapsed < 1.0
        assert len(service.aktif_oturumlar) == 10


# ============================================
# TEST SONUC OZETI
# ============================================


def test_sinav_motoru_summary():
    """
    Sinav Motoru Service Test Ozeti

    Toplam Test: 18 test

    Test Kategorileri:
    - Sinav Olusturma: 8 test (TYT/AYT/YDT)
    - Sinav Baslatma: 4 test
    - Cevap Kaydetme: 2 test
    - Performans: 1 test

    Hedef Coverage: %85+

    Kritik Alanlar:
    - OSYM sinav formatlari
    - Oturum yonetimi
    - Cevap kaydetme

    Test calistirma:
    cd backend
    pytest tests/test_sinav_motoru_service.py -v --cov=services.sinav_motoru_service --cov-report=html
    """
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
