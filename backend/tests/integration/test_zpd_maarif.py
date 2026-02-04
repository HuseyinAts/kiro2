from unittest.mock import Mock, patch, AsyncMock

"""
Zone of Proximal Development + MEB Maarif Sistemi Testleri
Türk eğitim kültürüne uyarlanmış ZPD sistemi için kapsamlı testler
"""

from datetime import datetime, timedelta

import pytest

from models.zpd_maarif import (
    KulturelBaglamProfili,
    MaarifDegerleriProfili,
    TurkZPDAraligi,
    ZPDHesaplamaParametreleri,
    ZPDOptimizasyonSonucu,
    ZPDSeviyesi,
)
from services.zpd_maarif_service import ZPDMaarifService


class TestZPDMaarifModels:
    """ZPD Maarif model testleri"""

    def test_kulturel_baglam_profili_olusturma(self):
        """Kültürel bağlam profili oluşturma testi"""
        profil = KulturelBaglamProfili(
            ogrenci_id="test_ogrenci_123",
            grup_calismasi_tercihi=0.8,
            ogretmene_saygi_seviyesi=0.9,
            aile_katilim_derecesi=0.7,
            akran_rekabet_egilimi=0.6,
            otorite_kabul_seviyesi=0.8,
            toplumsal_onay_ihtiyaci=0.7,
            basari_odaklilik=0.9,
            kolektif_kimlik_gucu=0.8,
            bolge="Marmara",
            sosyoekonomik_durum="orta",
            okul_turu="devlet",
        )

        assert profil.ogrenci_id == "test_ogrenci_123"
        assert profil.grup_calismasi_tercihi == 0.8
        assert profil.ogretmene_saygi_seviyesi == 0.9
        assert profil.bolge == "Marmara"
        assert isinstance(profil.olusturma_tarihi, datetime)

    def test_kulturel_profil_validasyon(self):
        """Kültürel profil validasyon testi"""
        # Geçersiz skor değeri
        with pytest.raises(ValueError):
            KulturelBaglamProfili(
                ogrenci_id="test", grup_calismasi_tercihi=1.5  # 1.0'dan büyük
            )

        with pytest.raises(ValueError):
            KulturelBaglamProfili(
                ogrenci_id="test", ogretmene_saygi_seviyesi=-0.1  # 0.0'dan küçük
            )

    def test_maarif_degerleri_profili_olusturma(self):
        """MEB Maarif değerleri profili oluşturma testi"""
        profil = MaarifDegerleriProfili(
            ogrenci_id="test_ogrenci_123",
            vatan_sevgisi=0.9,
            millet_bilinci=0.8,
            aile_birligi=0.95,
            adalet=0.85,
            dostluk=0.9,
            durustluk=0.8,
            sabir=0.7,
            saygi=0.95,
            sevgi=0.9,
        )

        assert profil.ogrenci_id == "test_ogrenci_123"
        assert profil.vatan_sevgisi == 0.9
        assert profil.get_milli_degerler_ortalamasi() > 0.8
        assert profil.get_evrensel_degerler_ortalamasi() > 0.8
        assert profil.get_kok_degerler_ortalamasi() > 0.8

    def test_turk_zpd_araligi_olusturma(self):
        """Türk ZPD aralığı oluşturma testi"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test_ogrenci_123",
            konu="matematik",
            mevcut_seviye=6.0,
            alt_sinir=5.5,
            ust_sinir=8.0,
            optimal_zorluk=7.2,
            kulturel_carpan=1.2,
            maarif_uyum_katsayisi=0.8,
            grup_calismasi_bonusu=0.2,
            ogretmen_rehberlik_faktoru=0.15,
            hesaplama_guveni=0.85,
            kulturel_uyum_guveni=0.8,
        )

        assert zpd.ogrenci_id == "test_ogrenci_123"
        assert zpd.konu == "matematik"
        assert zpd.mevcut_seviye == 6.0
        assert zpd.optimal_zorluk == 7.2
        assert zpd.is_gecerli()  # Yeni oluşturuldu, geçerli olmalı

    def test_zpd_zorluk_seviyesi_belirleme(self):
        """ZPD zorluk seviyesi belirleme testi"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="test",
            mevcut_seviye=6.0,
            alt_sinir=5.5,
            ust_sinir=8.0,
            optimal_zorluk=7.2,
        )

        # Çok kolay
        assert zpd.get_zorluk_seviyesi(5.0) == ZPDSeviyesi.COK_KOLAY

        # Kolay
        assert zpd.get_zorluk_seviyesi(5.8) == ZPDSeviyesi.KOLAY

        # Optimal
        assert zpd.get_zorluk_seviyesi(7.0) == ZPDSeviyesi.OPTIMAL

        # Zor
        assert zpd.get_zorluk_seviyesi(7.8) == ZPDSeviyesi.ZOR

        # Çok zor
        assert zpd.get_zorluk_seviyesi(9.0) == ZPDSeviyesi.COK_ZOR

    def test_zpd_gecerlilik_kontrolu(self):
        """ZPD geçerlilik kontrolü testi"""
        # Eski tarihli ZPD
        eski_zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="test",
            mevcut_seviye=6.0,
            alt_sinir=5.5,
            ust_sinir=8.0,
            optimal_zorluk=7.2,
            hesaplama_tarihi=datetime.now() - timedelta(days=10),
            gecerlilik_suresi_gun=7,
        )

        assert not eski_zpd.is_gecerli()  # 10 gün önce, 7 gün geçerli

        # Yeni ZPD
        yeni_zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="test",
            mevcut_seviye=6.0,
            alt_sinir=5.5,
            ust_sinir=8.0,
            optimal_zorluk=7.2,
            hesaplama_tarihi=datetime.now() - timedelta(days=3),
            gecerlilik_suresi_gun=7,
        )

        assert yeni_zpd.is_gecerli()  # 3 gün önce, 7 gün geçerli


class TestZPDMaarifService:
    """ZPD Maarif servis testleri"""

    @pytest.fixture
    def zpd_service(self):
        """ZPD servis fixture'ı"""
        return ZPDMaarifService()

    @pytest.fixture
    def sample_kulturel_profil(self):
        """Örnek kültürel profil fixture'ı"""
        return KulturelBaglamProfili(
            ogrenci_id="test_ogrenci_123",
            grup_calismasi_tercihi=0.8,
            ogretmene_saygi_seviyesi=0.9,
            aile_katilim_derecesi=0.7,
            akran_rekabet_egilimi=0.6,
            otorite_kabul_seviyesi=0.8,
            toplumsal_onay_ihtiyaci=0.7,
            basari_odaklilik=0.9,
            kolektif_kimlik_gucu=0.8,
        )

    @pytest.fixture
    def sample_maarif_profili(self):
        """Örnek MEB Maarif profili fixture'ı"""
        return MaarifDegerleriProfili(
            ogrenci_id="test_ogrenci_123",
            vatan_sevgisi=0.9,
            millet_bilinci=0.8,
            aile_birligi=0.95,
            adalet=0.85,
            dostluk=0.9,
            durustluk=0.8,
            sabir=0.7,
            saygi=0.95,
            sevgi=0.9,
        )

    @pytest.fixture
    def sample_performans_verileri(self):
        """Örnek performans verileri fixture'ı"""
        return [
            {
                "tarih": "2024-01-01",
                "basari_orani": 0.6,
                "zorluk_seviyesi": 6.0,
                "ogrenme_yontemi": "bireysel",
                "icerik_turu": "video",
            },
            {
                "tarih": "2024-01-02",
                "basari_orani": 0.7,
                "zorluk_seviyesi": 6.5,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "interaktif",
            },
            {
                "tarih": "2024-01-03",
                "basari_orani": 0.8,
                "zorluk_seviyesi": 7.0,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "video",
            },
        ]

    @pytest.mark.asyncio
    async def test_turk_zpd_hesaplama(
        self, zpd_service, sample_kulturel_profil, sample_maarif_profili
    ):
        """Türk ZPD hesaplama testi"""
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_ogrenci_123",
            konu="matematik",
            mevcut_seviye=6.0,
            kulturel_profil=sample_kulturel_profil,
            maarif_profili=sample_maarif_profili,
        )

        assert isinstance(zpd_araligi, TurkZPDAraligi)
        assert zpd_araligi.ogrenci_id == "test_ogrenci_123"
        assert zpd_araligi.konu == "matematik"
        assert zpd_araligi.mevcut_seviye == 6.0
        assert zpd_araligi.alt_sinir >= 0.0
        assert zpd_araligi.ust_sinir <= 10.0
        assert (
            zpd_araligi.alt_sinir < zpd_araligi.optimal_zorluk < zpd_araligi.ust_sinir
        )
        assert 0.0 <= zpd_araligi.hesaplama_guveni <= 1.0
        assert 0.0 <= zpd_araligi.kulturel_uyum_guveni <= 1.0

    @pytest.mark.asyncio
    async def test_varsayilan_profil_olusturma(self, zpd_service):
        """Varsayılan profil oluşturma testi"""
        # Varsayılan kültürel profil
        kulturel_profil = await zpd_service._olustur_varsayilan_kulturel_profil(
            "test_ogrenci"
        )
        assert isinstance(kulturel_profil, KulturelBaglamProfili)
        assert kulturel_profil.ogrenci_id == "test_ogrenci"
        assert 0.0 <= kulturel_profil.grup_calismasi_tercihi <= 1.0

        # Varsayılan MEB Maarif profili
        maarif_profili = await zpd_service._olustur_varsayilan_maarif_profili(
            "test_ogrenci"
        )
        assert isinstance(maarif_profili, MaarifDegerleriProfili)
        assert maarif_profili.ogrenci_id == "test_ogrenci"
        assert 0.0 <= maarif_profili.vatan_sevgisi <= 1.0

    @pytest.mark.asyncio
    async def test_kulturel_carpan_hesaplama(self, zpd_service, sample_kulturel_profil):
        """Kültürel çarpan hesaplama testi"""
        parametreler = ZPDHesaplamaParametreleri()

        carpan = await zpd_service._hesapla_kulturel_carpan(
            sample_kulturel_profil, parametreler
        )

        assert isinstance(carpan, float)
        assert 0.5 <= carpan <= 2.0  # Sınırlar içinde

        # Yüksek grup çalışması tercihi çarpanı artırmalı
        assert carpan > 1.0  # sample_kulturel_profil'de yüksek değerler var

    @pytest.mark.asyncio
    async def test_maarif_uyum_katsayisi_hesaplama(
        self, zpd_service, sample_maarif_profili
    ):
        """MEB Maarif uyum katsayısı hesaplama testi"""
        parametreler = ZPDHesaplamaParametreleri()

        # Matematik konusu
        matematik_uyum = await zpd_service._hesapla_maarif_uyum_katsayisi(
            sample_maarif_profili, "matematik", parametreler
        )

        # Tarih konusu
        tarih_uyum = await zpd_service._hesapla_maarif_uyum_katsayisi(
            sample_maarif_profili, "tarih", parametreler
        )

        assert isinstance(matematik_uyum, float)
        assert isinstance(tarih_uyum, float)
        assert 0.0 <= matematik_uyum <= 1.0
        assert 0.0 <= tarih_uyum <= 1.0

        # Tarih konusunda milli değerler daha önemli olmalı
        # Bu test profilde milli değerler yüksek olduğu için tarih uyumu daha yüksek olabilir

    @pytest.mark.asyncio
    async def test_grup_calismasi_bonusu(self, zpd_service, sample_kulturel_profil):
        """Grup çalışması bonusu hesaplama testi"""
        parametreler = ZPDHesaplamaParametreleri()

        bonus = await zpd_service._hesapla_grup_calismasi_bonusu(
            sample_kulturel_profil, parametreler
        )

        assert isinstance(bonus, float)
        assert 0.0 <= bonus <= 0.5

        # Yüksek grup çalışması tercihi (0.8) bonus vermeli
        assert bonus > 0.0

    @pytest.mark.asyncio
    async def test_ogretmen_rehberlik_faktoru(
        self, zpd_service, sample_kulturel_profil
    ):
        """Öğretmen rehberlik faktörü hesaplama testi"""
        parametreler = ZPDHesaplamaParametreleri()

        faktor = await zpd_service._hesapla_ogretmen_rehberlik_faktoru(
            sample_kulturel_profil, parametreler
        )

        assert isinstance(faktor, float)
        assert 0.0 <= faktor <= 0.3

        # Yüksek öğretmene saygı (0.9) faktör vermeli
        assert faktor > 0.0

    @pytest.mark.asyncio
    async def test_zpd_optimizasyonu(self, zpd_service, sample_performans_verileri):
        """ZPD optimizasyon testi"""
        optimizasyon_sonucu = await zpd_service.optimize_zpd_parametreleri(
            ogrenci_id="test_ogrenci_123",
            konu="matematik",
            performans_verileri=sample_performans_verileri,
        )

        assert isinstance(optimizasyon_sonucu, ZPDOptimizasyonSonucu)
        assert optimizasyon_sonucu.ogrenci_id == "test_ogrenci_123"
        assert optimizasyon_sonucu.konu == "matematik"
        assert 0.0 <= optimizasyon_sonucu.onerilen_zorluk_seviyesi <= 10.0
        assert isinstance(optimizasyon_sonucu.grup_calismasi_onerisi, bool)
        assert isinstance(optimizasyon_sonucu.ogretmen_rehberlik_ihtiyaci, bool)
        assert len(optimizasyon_sonucu.icerik_turu_onerileri) <= 3
        assert len(optimizasyon_sonucu.motivasyon_stratejileri) <= 5
        assert 0.0 <= optimizasyon_sonucu.oneri_guveni <= 1.0
        assert 0.0 <= optimizasyon_sonucu.beklenen_basari_artisi <= 1.0

    @pytest.mark.asyncio
    async def test_basari_trendi_analizi(self, zpd_service, sample_performans_verileri):
        """Başarı trendi analizi testi"""
        trend = await zpd_service._analiz_et_basari_trendi(sample_performans_verileri)

        assert isinstance(trend, float)
        assert -0.5 <= trend <= 0.5

        # Örnek verilerde başarı artışı var (0.6 -> 0.8)
        assert trend > 0.0

    @pytest.mark.asyncio
    async def test_zorluk_uyumu_analizi(self, zpd_service, sample_performans_verileri):
        """Zorluk uyumu analizi testi"""
        uyum = await zpd_service._analiz_et_zorluk_uyumu(sample_performans_verileri)

        assert isinstance(uyum, float)
        assert 0.0 <= uyum <= 1.0

    @pytest.mark.asyncio
    async def test_ogrenme_hizi_hesaplama(
        self, zpd_service, sample_performans_verileri
    ):
        """Öğrenme hızı hesaplama testi"""
        hiz = await zpd_service._hesapla_ogrenme_hizi(sample_performans_verileri)

        assert isinstance(hiz, float)
        assert 0.5 <= hiz <= 2.0

        # Örnek verilerde gelişim var, hız 1.0'dan büyük olmalı
        assert hiz > 1.0

    @pytest.mark.asyncio
    async def test_optimal_ogrenme_yontemi_belirleme(
        self, zpd_service, sample_performans_verileri
    ):
        """Optimal öğrenme yöntemi belirleme testi"""
        yontem = await zpd_service._belirle_optimal_ogrenme_yontemi(
            "test_ogrenci_123", sample_performans_verileri
        )

        assert isinstance(yontem, str)
        assert yontem in ["bireysel", "grup"]

        # Örnek verilerde grup çalışması daha başarılı (0.7, 0.8 vs 0.6)
        assert yontem == "grup"

    @pytest.mark.asyncio
    async def test_grup_calismasi_degerlendirme(
        self, zpd_service, sample_performans_verileri
    ):
        """Grup çalışması değerlendirme testi"""
        oneri = await zpd_service._degerlendirme_grup_calismasi(
            "test_ogrenci_123", sample_performans_verileri
        )

        assert isinstance(oneri, bool)

        # Örnek verilerde grup çalışması daha başarılı
        assert oneri == True

    @pytest.mark.asyncio
    async def test_ogretmen_rehberlik_degerlendirme(self, zpd_service):
        """Öğretmen rehberlik değerlendirme testi"""
        # Düşük başarılı performans verileri
        dusuk_performans = [
            {"basari_orani": 0.3, "zorluk_seviyesi": 5.0},
            {"basari_orani": 0.4, "zorluk_seviyesi": 5.0},
            {"basari_orani": 0.2, "zorluk_seviyesi": 5.0},
        ]

        rehberlik_ihtiyaci = await zpd_service._degerlendirme_ogretmen_rehberlik(
            "test_ogrenci", dusuk_performans
        )

        assert isinstance(rehberlik_ihtiyaci, bool)
        assert rehberlik_ihtiyaci == True  # Düşük başarı, rehberlik gerekli

        # Yüksek başarılı performans verileri
        yuksek_performans = [
            {"basari_orani": 0.8, "zorluk_seviyesi": 7.0},
            {"basari_orani": 0.9, "zorluk_seviyesi": 7.0},
            {"basari_orani": 0.85, "zorluk_seviyesi": 7.0},
        ]

        rehberlik_ihtiyaci = await zpd_service._degerlendirme_ogretmen_rehberlik(
            "test_ogrenci", yuksek_performans
        )

        assert rehberlik_ihtiyaci == False  # Yüksek başarı, rehberlik gerekmez

    @pytest.mark.asyncio
    async def test_icerik_turu_onerileri(self, zpd_service, sample_performans_verileri):
        """İçerik türü önerileri testi"""
        oneriler = await zpd_service._oneriler_icerik_turu(
            "test_ogrenci_123", "matematik", sample_performans_verileri
        )

        assert isinstance(oneriler, list)
        assert len(oneriler) <= 3
        assert all(isinstance(oneri, str) for oneri in oneriler)

        # Örnek verilerde video ve interaktif başarılı
        assert "video" in oneriler or "interaktif" in oneriler

    @pytest.mark.asyncio
    async def test_motivasyon_stratejileri(
        self, zpd_service, sample_performans_verileri
    ):
        """Motivasyon stratejileri belirleme testi"""
        stratejiler = await zpd_service._belirle_motivasyon_stratejileri(
            "test_ogrenci_123", sample_performans_verileri
        )

        assert isinstance(stratejiler, list)
        assert len(stratejiler) <= 5
        assert all(isinstance(strateji, str) for strateji in stratejiler)

        # Türk kültürüne özel stratejiler içermeli
        turk_stratejileri = [
            "aile_katilimi",
            "toplumsal_onay",
            "milli_degerler_vurgusu",
        ]
        assert any(strateji in stratejiler for strateji in turk_stratejileri)

    @pytest.mark.asyncio
    async def test_hesaplama_gecmisi_kaydetme(
        self, zpd_service, sample_kulturel_profil, sample_maarif_profili
    ):
        """Hesaplama geçmişi kaydetme testi"""
        # İlk hesaplama
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_ogrenci_gecmis",
            konu="matematik",
            mevcut_seviye=6.0,
            kulturel_profil=sample_kulturel_profil,
            maarif_profili=sample_maarif_profili,
        )

        # Geçmiş kontrol et
        anahtar = "test_ogrenci_gecmis_matematik"
        assert anahtar in zpd_service.hesaplama_gecmisi
        assert len(zpd_service.hesaplama_gecmisi[anahtar]) == 1

        # İkinci hesaplama
        await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_ogrenci_gecmis",
            konu="matematik",
            mevcut_seviye=6.5,
            kulturel_profil=sample_kulturel_profil,
            maarif_profili=sample_maarif_profili,
        )

        # Geçmiş artmış olmalı
        assert len(zpd_service.hesaplama_gecmisi[anahtar]) == 2

    def test_standart_sapma_hesaplama(self, zpd_service):
        """Standart sapma hesaplama testi"""
        # Basit test verileri
        degerler = [1.0, 2.0, 3.0, 4.0, 5.0]
        standart_sapma = zpd_service._hesapla_standart_sapma(degerler)

        assert isinstance(standart_sapma, float)
        assert standart_sapma > 0.0

        # Aynı değerler - standart sapma 0 olmalı
        ayni_degerler = [5.0, 5.0, 5.0, 5.0]
        standart_sapma_sifir = zpd_service._hesapla_standart_sapma(ayni_degerler)
        assert standart_sapma_sifir == 0.0

        # Tek değer - standart sapma 0 olmalı
        tek_deger = [5.0]
        standart_sapma_tek = zpd_service._hesapla_standart_sapma(tek_deger)
        assert standart_sapma_tek == 0.0


class TestZPDMaarifIntegration:
    """ZPD Maarif entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_tam_zpd_sureci(self):
        """Tam ZPD süreci entegrasyon testi"""
        zpd_service = ZPDMaarifService()

        # 1. Başlangıç ZPD hesaplama
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="entegrasyon_test_ogrenci", konu="matematik", mevcut_seviye=5.0
        )

        assert isinstance(zpd_araligi, TurkZPDAraligi)
        assert zpd_araligi.mevcut_seviye == 5.0

        # 2. Performans verileri simülasyonu
        performans_verileri = [
            {
                "tarih": "2024-01-01",
                "basari_orani": 0.5,
                "zorluk_seviyesi": zpd_araligi.optimal_zorluk,
                "ogrenme_yontemi": "bireysel",
                "icerik_turu": "metin",
            },
            {
                "tarih": "2024-01-02",
                "basari_orani": 0.6,
                "zorluk_seviyesi": zpd_araligi.optimal_zorluk,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "video",
            },
            {
                "tarih": "2024-01-03",
                "basari_orani": 0.7,
                "zorluk_seviyesi": zpd_araligi.optimal_zorluk + 0.5,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "video",
            },
        ]

        # 3. Optimizasyon
        optimizasyon = await zpd_service.optimize_zpd_parametreleri(
            ogrenci_id="entegrasyon_test_ogrenci",
            konu="matematik",
            performans_verileri=performans_verileri,
        )

        assert isinstance(optimizasyon, ZPDOptimizasyonSonucu)
        assert (
            optimizasyon.grup_calismasi_onerisi == True
        )  # Grup çalışması daha başarılı
        assert "video" in optimizasyon.icerik_turu_onerileri  # Video daha başarılı

        # 4. Yeni ZPD hesaplama (gelişmiş seviye ile)
        yeni_zpd = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="entegrasyon_test_ogrenci",
            konu="matematik",
            mevcut_seviye=6.0,  # Gelişim gösterdi
        )

        assert yeni_zpd.mevcut_seviye > zpd_araligi.mevcut_seviye
        assert yeni_zpd.optimal_zorluk > zpd_araligi.optimal_zorluk

        # 5. Geçmiş kontrolü
        anahtar = "entegrasyon_test_ogrenci_matematik"
        assert anahtar in zpd_service.hesaplama_gecmisi
        assert len(zpd_service.hesaplama_gecmisi[anahtar]) == 2  # İki hesaplama

    @pytest.mark.asyncio
    async def test_kulturel_faktorlerin_zpd_etkisi(self):
        """Kültürel faktörlerin ZPD'ye etkisi testi"""
        zpd_service = ZPDMaarifService()

        # Yüksek grup çalışması tercihi profili
        yuksek_grup_profili = KulturelBaglamProfili(
            ogrenci_id="test_yuksek_grup",
            grup_calismasi_tercihi=0.9,
            ogretmene_saygi_seviyesi=0.9,
            kolektif_kimlik_gucu=0.9,
        )

        # Düşük grup çalışması tercihi profili
        dusuk_grup_profili = KulturelBaglamProfili(
            ogrenci_id="test_dusuk_grup",
            grup_calismasi_tercihi=0.3,
            ogretmene_saygi_seviyesi=0.5,
            kolektif_kimlik_gucu=0.4,
        )

        # Aynı mevcut seviye ile ZPD hesapla
        yuksek_zpd = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_yuksek_grup",
            konu="matematik",
            mevcut_seviye=6.0,
            kulturel_profil=yuksek_grup_profili,
        )

        dusuk_zpd = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_dusuk_grup",
            konu="matematik",
            mevcut_seviye=6.0,
            kulturel_profil=dusuk_grup_profili,
        )

        # Yüksek grup çalışması tercihi daha geniş ZPD aralığı vermeli
        yuksek_genislik = yuksek_zpd.ust_sinir - yuksek_zpd.alt_sinir
        dusuk_genislik = dusuk_zpd.ust_sinir - dusuk_zpd.alt_sinir

        assert yuksek_genislik > dusuk_genislik
        assert yuksek_zpd.grup_calismasi_bonusu > dusuk_zpd.grup_calismasi_bonusu

    @pytest.mark.asyncio
    async def test_maarif_degerlerinin_konu_bazli_etkisi(self):
        """MEB Maarif değerlerinin konu bazlı etkisi testi"""
        zpd_service = ZPDMaarifService()

        # Yüksek milli değerler profili
        yuksek_milli_profil = MaarifDegerleriProfili(
            ogrenci_id="test_yuksek_milli",
            vatan_sevgisi=0.95,
            millet_bilinci=0.9,
            aile_birligi=0.95,
            istiklal_ruhu=0.9,
        )

        # Tarih konusu (milli değerler önemli)
        tarih_zpd = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_yuksek_milli",
            konu="tarih",
            mevcut_seviye=6.0,
            maarif_profili=yuksek_milli_profil,
        )

        # Matematik konusu (evrensel değerler önemli)
        matematik_zpd = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_yuksek_milli",
            konu="matematik",
            mevcut_seviye=6.0,
            maarif_profili=yuksek_milli_profil,
        )

        # Tarih konusunda maarif uyumu daha yüksek olmalı
        assert tarih_zpd.maarif_uyum_katsayisi >= matematik_zpd.maarif_uyum_katsayisi
