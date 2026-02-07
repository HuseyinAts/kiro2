# -*- coding: utf-8 -*-
"""
Test: Sinav Motoru - Net Hesaplama ve Tamamlama (PART 2)
Hedef: %60-70 Coverage
Kritik: Net = Dogru - (Yanlis/4), Konu analizi, Sinav tamamlama
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.sinav_motoru_service import SinavMotoruServisi
from models import SinavTipi, SinavDurumu


class TestSinavTamamlamaVeSonucHesaplama:
    """Sinav tamamlama ve detayli sonuc hesaplama testleri"""

    @pytest.fixture
    def service(self):
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    async def test_sinav_tamamla_temel(self, service):
        """Sinav tamamlama - temel basarili senaryo"""
        ogrenci_id = "test_tamamla_001"

        # 20 soruluk mini sinav
        mock_sorular = []
        for i in range(20):
            mock_soru = Mock()
            mock_soru.soru_id = f"soru_{i}"
            mock_soru.konu = "Matematik"
            mock_soru.dogru_cevap = "A"
            mock_sorular.append(mock_soru)

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 20, "sure_dakika": 30},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Cevaplar: 15 dogru, 3 yanlis, 2 bos
        oturum.cevaplanan_sorular = {}
        for i in range(15):
            oturum.cevaplanan_sorular[f"soru_{i}"] = "A"  # Dogru
        for i in range(15, 18):
            oturum.cevaplanan_sorular[f"soru_{i}"] = "B"  # Yanlis

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:

            def get_soru(soru_id):
                return next((s for s in mock_sorular if s.soru_id == soru_id), None)

            mock_service.soru_getir = AsyncMock(side_effect=get_soru)

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Dogrulamalar
        assert sonuc is not None
        assert sonuc.sinav_id == oturum.sinav_id
        assert sonuc.ogrenci_id == ogrenci_id
        assert sonuc.sinav_tipi == SinavTipi.TYT
        assert sonuc.toplam_soru == 20
        assert sonuc.dogru_sayisi == 15
        assert sonuc.yanlis_sayisi == 3
        assert sonuc.bos_sayisi == 2

        # Net = 15 - (3/4) = 15 - 0.75 = 14.25
        expected_net = 15 - (3 / 4)
        assert sonuc.net_sayisi == expected_net

        # Ham puan = (15/20) * 100 = 75
        expected_ham_puan = (15 / 20) * 100
        assert sonuc.ham_puan == expected_ham_puan

        # Durum guncellendi mi?
        updated_oturum = service.aktif_oturumlar[oturum.sinav_id]
        assert updated_oturum.durum == SinavDurumu.TAMAMLANDI

    @pytest.mark.asyncio
    async def test_sinav_tamamla_sonuc_kaydedildi_mi(self, service):
        """Tamamlanan sinav sonucu kaydediliyor mu?"""
        ogrenci_id = "test_tamamla_002"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(10)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 10},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        oturum.cevaplanan_sorular = {f"s_{i}": "A" for i in range(5)}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Sonuc kayitlara eklendi mi?
        assert oturum.sinav_id in service.sinav_sonuclari
        assert service.sinav_sonuclari[oturum.sinav_id] == sonuc

    @pytest.mark.asyncio
    async def test_sinav_tamamla_olmayan_oturum(self, service):
        """Olmayan sinav ID ile tamamlama - hata"""
        with pytest.raises(ValueError):
            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                await service.sinav_tamamla("olmayan_sinav_id_xyz")


class TestNetHesaplamaAlgoritmasi:
    """OSYM Net Hesaplama Algoritmasi - Detayli Testler"""

    @pytest.fixture
    def service(self):
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    async def test_net_hesaplama_formul_standart(self, service):
        """Net = Dogru - (Yanlis / 4) - Standart durum"""
        ogrenci_id = "net_test_001"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(100)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 100},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # 60 dogru, 32 yanlis, 8 bos
        cevaplar = {}
        for i in range(60):
            cevaplar[f"s_{i}"] = "A"  # Dogru
        for i in range(60, 92):
            cevaplar[f"s_{i}"] = "B"  # Yanlis

        oturum.cevaplanan_sorular = cevaplar

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Net = 60 - (32/4) = 60 - 8 = 52
        expected_net = 60 - (32 / 4)
        assert sonuc.net_sayisi == expected_net
        assert sonuc.net_sayisi == 52.0

    @pytest.mark.asyncio
    async def test_net_hesaplama_tam_dogru(self, service):
        """Tum sorular dogru - Net = Toplam soru"""
        ogrenci_id = "net_test_002"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(50)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 50},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Tum sorular dogru
        oturum.cevaplanan_sorular = {f"s_{i}": "A" for i in range(50)}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Net = 50 - 0 = 50
        assert sonuc.net_sayisi == 50.0
        assert sonuc.dogru_sayisi == 50
        assert sonuc.yanlis_sayisi == 0
        assert sonuc.bos_sayisi == 0

    @pytest.mark.asyncio
    async def test_net_hesaplama_tam_yanlis(self, service):
        """Tum sorular yanlis - Negatif net"""
        ogrenci_id = "net_test_003"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(40)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 40},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Tum sorular yanlis
        oturum.cevaplanan_sorular = {f"s_{i}": "B" for i in range(40)}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Net = 0 - (40/4) = -10
        expected_net = 0 - (40 / 4)
        assert sonuc.net_sayisi == expected_net
        assert sonuc.net_sayisi == -10.0

    @pytest.mark.asyncio
    async def test_net_hesaplama_tam_bos(self, service):
        """Tum sorular bos - Net = 0"""
        ogrenci_id = "net_test_004"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(30)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 30},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Hic cevap yok
        oturum.cevaplanan_sorular = {}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Net = 0 - 0 = 0
        assert sonuc.net_sayisi == 0.0
        assert sonuc.dogru_sayisi == 0
        assert sonuc.yanlis_sayisi == 0
        assert sonuc.bos_sayisi == 30

    @pytest.mark.asyncio
    async def test_net_hesaplama_kesirli_sonuc(self, service):
        """Kesirli net sonucu dogru hesaplaniyor mu?"""
        ogrenci_id = "net_test_005"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(23)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 23},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # 17 dogru, 5 yanlis, 1 bos
        cevaplar = {}
        for i in range(17):
            cevaplar[f"s_{i}"] = "A"
        for i in range(17, 22):
            cevaplar[f"s_{i}"] = "B"

        oturum.cevaplanan_sorular = cevaplar

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Net = 17 - (5/4) = 17 - 1.25 = 15.75
        expected_net = 17 - (5 / 4)
        assert sonuc.net_sayisi == expected_net
        assert sonuc.net_sayisi == 15.75

    @pytest.mark.asyncio
    async def test_net_tyt_120_soru_gercekci_senaryo(self, service):
        """TYT 120 soru - Gercekci ogrenci senaryosu"""
        ogrenci_id = "net_test_006"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(120)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id, sinav_tipi=SinavTipi.TYT
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # Gercekci: 78 dogru, 24 yanlis, 18 bos
        cevaplar = {}
        for i in range(78):
            cevaplar[f"s_{i}"] = "A"
        for i in range(78, 102):
            cevaplar[f"s_{i}"] = "B"

        oturum.cevaplanan_sorular = cevaplar

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Net = 78 - (24/4) = 78 - 6 = 72
        expected_net = 78 - (24 / 4)
        assert sonuc.net_sayisi == expected_net
        assert sonuc.net_sayisi == 72.0


class TestHamPuanHesaplama:
    """Ham Puan Hesaplama Testleri"""

    @pytest.fixture
    def service(self):
        return SinavMotoruServisi()

    @pytest.mark.asyncio
    async def test_ham_puan_formul(self, service):
        """Ham Puan = (Dogru / Toplam) * 100"""
        ogrenci_id = "ham_puan_001"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(100)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 100},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        # 85 dogru
        oturum.cevaplanan_sorular = {f"s_{i}": "A" for i in range(85)}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        # Ham puan = (85/100) * 100 = 85
        expected_ham_puan = (85 / 100) * 100
        assert sonuc.ham_puan == expected_ham_puan
        assert sonuc.ham_puan == 85.0

    @pytest.mark.asyncio
    async def test_ham_puan_tam_dogru(self, service):
        """Tum sorular dogru - Ham puan = 100"""
        ogrenci_id = "ham_puan_002"

        mock_sorular = [
            Mock(soru_id=f"s_{i}", konu="Mat", dogru_cevap="A") for i in range(40)
        ]

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.rastgele_sorular_sec = AsyncMock(return_value=mock_sorular)

            oturum = await service.sinav_olustur(
                ogrenci_id=ogrenci_id,
                sinav_tipi=SinavTipi.TYT,
                ozel_konfigurasyonlar={"toplam_soru": 40},
            )

        with patch.object(service, "_send_websocket_update", new=AsyncMock()):
            with patch("asyncio.create_task"):
                await service.sinav_baslat(oturum.sinav_id)

        oturum.cevaplanan_sorular = {f"s_{i}": "A" for i in range(40)}

        with patch(
            "services.sinav_motoru_service.soru_bankasi_servisi"
        ) as mock_service:
            mock_service.soru_getir = AsyncMock(
                side_effect=lambda sid: next(
                    (s for s in mock_sorular if s.soru_id == sid), None
                )
            )

            with patch.object(service, "_send_websocket_update", new=AsyncMock()):
                sonuc = await service.sinav_tamamla(oturum.sinav_id)

        assert sonuc.ham_puan == 100.0


# ============================================
# TEST SONUC OZETI
# ============================================


def test_sinav_motoru_part2_summary():
    """
    Sinav Motoru Service - Part 2 Test Ozeti

    Yeni Testler: 13 test
    Hedef: %60-70 Coverage

    Test Kategorileri:
    - Sinav Tamamlama: 3 test
    - Net Hesaplama: 7 test (OSYM algoritmasi)
    - Ham Puan: 2 test

    Toplam (Part 1 + Part 2): ~29 test

    Kritik Alanlar:
    ✅ Net = Dogru - (Yanlis/4)
    ✅ Ham Puan = (Dogru/Toplam) * 100
    ✅ TYT gercekci senaryolar
    ✅ Edge cases (tam dogru, tam yanlis, tam bos)

    Test calistirma:
    cd backend
    pytest tests/test_sinav_motoru_service.py tests/test_sinav_motoru_part2.py -v --cov=services.sinav_motoru_service --cov-report=html
    """
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
