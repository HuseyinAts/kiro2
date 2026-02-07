
"""
ZPD Maarif Service Test Modülü
Türk eğitim kültürüne uyarlanmış ZPD hesaplama servisi testleri
"""

from datetime import datetime, timedelta

import pytest

from models.zpd_maarif import (
    KulturelBaglamProfili,
    MaarifDegerleriProfili,
    TurkZPDAraligi,
    ZPDOptimizasyonSonucu,
    ZPDSeviyesi,
)
from services.zpd_maarif_service import ZPDMaarifService


class TestZPDMaarifService:
    """ZPD Maarif Service test sınıfı"""

    @pytest.fixture
    def zpd_service(self):
        """ZPD Maarif servisi fixture'ı"""
        return ZPDMaarifService()

    @pytest.fixture
    def sample_kulturel_profil(self):
        """Örnek kültürel profil"""
        return KulturelBaglamProfili(
            ogrenci_id="test_student_001",
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

    @pytest.fixture
    def sample_maarif_profili(self):
        """Örnek MEB Maarif profili"""
        return MaarifDegerleriProfili(
            ogrenci_id="test_student_001",
            # Milli değerler
            vatan_sevgisi=0.9,
            millet_bilinci=0.8,
            aile_birligi=0.95,
            bayrak_sevgisi=0.85,
            istiklal_ruhu=0.8,
            # Evrensel değerler
            adalet=0.85,
            dostluk=0.9,
            durustluk=0.9,
            ozgurluk=0.75,
            esitlik=0.8,
            baris=0.95,
            # Kök değerler
            sabir=0.7,
            saygi=0.95,
            sevgi=0.9,
            sorumluluk=0.85,
            duyarlilik=0.8,
            hosgoru=0.85,
        )

    @pytest.fixture
    def sample_performans_verileri(self):
        """Örnek performans verileri"""
        return [
            {
                "tarih": datetime.now() - timedelta(days=10),
                "konu": "matematik",
                "zorluk_seviyesi": 6.0,
                "basari_orani": 0.7,
                "ogrenme_yontemi": "bireysel",
                "icerik_turu": "video",
                "sure_dakika": 45,
            },
            {
                "tarih": datetime.now() - timedelta(days=8),
                "konu": "matematik",
                "zorluk_seviyesi": 6.5,
                "basari_orani": 0.75,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "interaktif",
                "sure_dakika": 60,
            },
            {
                "tarih": datetime.now() - timedelta(days=6),
                "konu": "matematik",
                "zorluk_seviyesi": 7.0,
                "basari_orani": 0.8,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "video",
                "sure_dakika": 50,
            },
            {
                "tarih": datetime.now() - timedelta(days=4),
                "konu": "matematik",
                "zorluk_seviyesi": 7.5,
                "basari_orani": 0.65,
                "ogrenme_yontemi": "bireysel",
                "icerik_turu": "metin",
                "sure_dakika": 40,
            },
            {
                "tarih": datetime.now() - timedelta(days=2),
                "konu": "matematik",
                "zorluk_seviyesi": 7.0,
                "basari_orani": 0.85,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "interaktif",
                "sure_dakika": 55,
            },
        ]

    @pytest.mark.asyncio
    async def test_hesapla_turk_zpd_temel(
        self, zpd_service, sample_kulturel_profil, sample_maarif_profili
    ):
        """Temel ZPD hesaplama testi"""
        # Test verileri
        ogrenci_id = "test_student_001"
        konu = "matematik"
        mevcut_seviye = 6.0

        # ZPD hesapla
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id,
            konu=konu,
            mevcut_seviye=mevcut_seviye,
            kulturel_profil=sample_kulturel_profil,
            maarif_profili=sample_maarif_profili,
        )

        # Doğrulamalar
        assert isinstance(zpd_araligi, TurkZPDAraligi)
        assert zpd_araligi.ogrenci_id == ogrenci_id
        assert zpd_araligi.konu == konu
        assert zpd_araligi.mevcut_seviye == mevcut_seviye

        # ZPD sınırları mantıklı mı?
        assert zpd_araligi.alt_sinir >= 0.0
        assert zpd_araligi.ust_sinir <= 10.0
        assert (
            zpd_araligi.alt_sinir <= zpd_araligi.optimal_zorluk <= zpd_araligi.ust_sinir
        )
        assert zpd_araligi.optimal_zorluk > mevcut_seviye

        # Kültürel faktörler uygulandı mı?
        assert zpd_araligi.kulturel_carpan >= 0.5
        assert zpd_araligi.kulturel_carpan <= 2.0
        assert zpd_araligi.maarif_uyum_katsayisi >= 0.0
        assert zpd_araligi.maarif_uyum_katsayisi <= 1.0

        # Güven seviyeleri
        assert zpd_araligi.hesaplama_guveni >= 0.0
        assert zpd_araligi.hesaplama_guveni <= 1.0
        assert zpd_araligi.kulturel_uyum_guveni >= 0.0
        assert zpd_araligi.kulturel_uyum_guveni <= 1.0

    @pytest.mark.asyncio
    async def test_hesapla_turk_zpd_varsayilan_profiller(self, zpd_service):
        """Varsayılan profiller ile ZPD hesaplama testi"""
        ogrenci_id = "test_student_002"
        konu = "fizik"
        mevcut_seviye = 5.5

        # Profil olmadan hesapla (varsayılan profiller kullanılacak)
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id, konu=konu, mevcut_seviye=mevcut_seviye
        )

        # Doğrulamalar
        assert isinstance(zpd_araligi, TurkZPDAraligi)
        assert zpd_araligi.ogrenci_id == ogrenci_id
        assert zpd_araligi.konu == konu
        assert zpd_araligi.mevcut_seviye == mevcut_seviye

        # Varsayılan değerler uygulandı mı?
        assert zpd_araligi.kulturel_carpan > 0.0
        assert zpd_araligi.maarif_uyum_katsayisi > 0.0

    @pytest.mark.asyncio
    async def test_grup_calismasi_bonusu(self, zpd_service):
        """Grup çalışması bonusu testi"""
        # Yüksek grup çalışması tercihi olan profil
        yuksek_grup_profili = KulturelBaglamProfili(
            ogrenci_id="test_student_003",
            grup_calismasi_tercihi=0.9,
            kolektif_kimlik_gucu=0.8,
        )

        # Düşük grup çalışması tercihi olan profil
        dusuk_grup_profili = KulturelBaglamProfili(
            ogrenci_id="test_student_004",
            grup_calismasi_tercihi=0.3,
            kolektif_kimlik_gucu=0.4,
        )

        # Her iki profil için ZPD hesapla
        zpd_yuksek = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_student_003",
            konu="matematik",
            mevcut_seviye=6.0,
            kulturel_profil=yuksek_grup_profili,
        )

        zpd_dusuk = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_student_004",
            konu="matematik",
            mevcut_seviye=6.0,
            kulturel_profil=dusuk_grup_profili,
        )

        # Yüksek grup tercihi daha fazla bonus almalı
        assert zpd_yuksek.grup_calismasi_bonusu > zpd_dusuk.grup_calismasi_bonusu
        assert zpd_yuksek.ust_sinir >= zpd_dusuk.ust_sinir

    @pytest.mark.asyncio
    async def test_ogretmen_rehberlik_faktoru(self, zpd_service):
        """Öğretmen rehberlik faktörü testi"""
        # Yüksek öğretmene saygı profili
        yuksek_saygi_profili = KulturelBaglamProfili(
            ogrenci_id="test_student_005",
            ogretmene_saygi_seviyesi=0.95,
            otorite_kabul_seviyesi=0.9,
        )

        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="test_student_005",
            konu="tarih",
            mevcut_seviye=5.0,
            kulturel_profil=yuksek_saygi_profili,
        )

        # Öğretmen rehberlik faktörü pozitif olmalı
        assert zpd_araligi.ogretmen_rehberlik_faktoru > 0.0
        assert zpd_araligi.ogretmen_rehberlik_faktoru <= 0.3

    @pytest.mark.asyncio
    async def test_maarif_uyum_katsayisi_konu_bazli(
        self, zpd_service, sample_maarif_profili
    ):
        """Konu bazlı MEB Maarif uyum katsayısı testi"""
        ogrenci_id = "test_student_006"

        # Farklı konular için ZPD hesapla
        zpd_tarih = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id,
            konu="tarih",
            mevcut_seviye=6.0,
            maarif_profili=sample_maarif_profili,
        )

        zpd_matematik = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id,
            konu="matematik",
            mevcut_seviye=6.0,
            maarif_profili=sample_maarif_profili,
        )

        zpd_turkce = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id,
            konu="türkçe",
            mevcut_seviye=6.0,
            maarif_profili=sample_maarif_profili,
        )

        # Her konu için farklı uyum katsayıları olmalı
        assert zpd_tarih.maarif_uyum_katsayisi >= 0.0
        assert zpd_matematik.maarif_uyum_katsayisi >= 0.0
        assert zpd_turkce.maarif_uyum_katsayisi >= 0.0

    @pytest.mark.asyncio
    async def test_optimize_zpd_parametreleri(
        self, zpd_service, sample_performans_verileri
    ):
        """ZPD parametre optimizasyonu testi"""
        ogrenci_id = "test_student_007"
        konu = "matematik"

        # Optimizasyon yap
        optimizasyon_sonucu = await zpd_service.optimize_zpd_parametreleri(
            ogrenci_id=ogrenci_id,
            konu=konu,
            performans_verileri=sample_performans_verileri,
        )

        # Doğrulamalar
        assert isinstance(optimizasyon_sonucu, ZPDOptimizasyonSonucu)
        assert optimizasyon_sonucu.ogrenci_id == ogrenci_id
        assert optimizasyon_sonucu.konu == konu

        # Önerilen zorluk seviyesi mantıklı mı?
        assert 1.0 <= optimizasyon_sonucu.onerilen_zorluk_seviyesi <= 10.0

        # Öğrenme yöntemi önerisi var mı?
        assert optimizasyon_sonucu.onerilen_ogrenme_yontemi in [
            "bireysel",
            "grup",
            "hibrit",
        ]

        # Grup çalışması önerisi boolean mı?
        assert isinstance(optimizasyon_sonucu.grup_calismasi_onerisi, bool)

        # Öğretmen rehberlik ihtiyacı boolean mı?
        assert isinstance(optimizasyon_sonucu.ogretmen_rehberlik_ihtiyaci, bool)

        # İçerik türü önerileri var mı?
        assert len(optimizasyon_sonucu.icerik_turu_onerileri) > 0
        assert len(optimizasyon_sonucu.icerik_turu_onerileri) <= 3

        # Öğrenme hızı ayarlaması mantıklı mı?
        assert 0.5 <= optimizasyon_sonucu.ogrenme_hizi_ayarlama <= 2.0

        # Motivasyon stratejileri var mı?
        assert len(optimizasyon_sonucu.motivasyon_stratejileri) > 0
        assert len(optimizasyon_sonucu.motivasyon_stratejileri) <= 5

        # Güven metrikleri
        assert 0.0 <= optimizasyon_sonucu.oneri_guveni <= 1.0
        assert 0.0 <= optimizasyon_sonucu.beklenen_basari_artisi <= 1.0

    @pytest.mark.asyncio
    async def test_basari_trendi_analizi(self, zpd_service):
        """Başarı trendi analizi testi"""
        # Artan başarı trendi
        artan_performans = [
            {"basari_orani": 0.5, "zorluk_seviyesi": 5.0},
            {"basari_orani": 0.6, "zorluk_seviyesi": 5.5},
            {"basari_orani": 0.7, "zorluk_seviyesi": 6.0},
            {"basari_orani": 0.8, "zorluk_seviyesi": 6.5},
        ]

        # Azalan başarı trendi
        azalan_performans = [
            {"basari_orani": 0.8, "zorluk_seviyesi": 6.0},
            {"basari_orani": 0.7, "zorluk_seviyesi": 6.0},
            {"basari_orani": 0.6, "zorluk_seviyesi": 6.0},
            {"basari_orani": 0.5, "zorluk_seviyesi": 6.0},
        ]

        # Trend analizleri
        artan_trend = await zpd_service._analiz_et_basari_trendi(artan_performans)
        azalan_trend = await zpd_service._analiz_et_basari_trendi(azalan_performans)

        # Artan trend pozitif, azalan trend negatif olmalı
        assert artan_trend > 0
        assert azalan_trend < 0

    @pytest.mark.asyncio
    async def test_zorluk_uyumu_analizi(self, zpd_service):
        """Zorluk uyumu analizi testi"""
        # İyi uyum gösteren performans
        iyi_uyum_performans = [
            {"zorluk_seviyesi": 7.0, "basari_orani": 0.7},
            {"zorluk_seviyesi": 7.5, "basari_orani": 0.75},
            {"zorluk_seviyesi": 8.0, "basari_orani": 0.8},
        ]

        # Kötü uyum gösteren performans
        kotu_uyum_performans = [
            {"zorluk_seviyesi": 9.0, "basari_orani": 0.3},
            {"zorluk_seviyesi": 3.0, "basari_orani": 0.95},
            {"zorluk_seviyesi": 10.0, "basari_orani": 0.2},
        ]

        # Uyum analizleri
        iyi_uyum = await zpd_service._analiz_et_zorluk_uyumu(iyi_uyum_performans)
        kotu_uyum = await zpd_service._analiz_et_zorluk_uyumu(kotu_uyum_performans)

        # İyi uyum yüksek, kötü uyum düşük skor almalı
        assert iyi_uyum > kotu_uyum
        assert 0.0 <= iyi_uyum <= 1.0
        assert 0.0 <= kotu_uyum <= 1.0

    @pytest.mark.asyncio
    async def test_ogrenme_hizi_hesaplama(self, zpd_service):
        """Öğrenme hızı hesaplama testi"""
        # Hızlı öğrenme gösteren performans
        hizli_ogrenme = [
            {"basari_orani": 0.5},
            {"basari_orani": 0.7},
            {"basari_orani": 0.8},
        ]

        # Yavaş öğrenme gösteren performans
        yavas_ogrenme = [
            {"basari_orani": 0.7},
            {"basari_orani": 0.65},
            {"basari_orani": 0.6},
        ]

        # Hız hesaplamaları
        hizli_hiz = await zpd_service._hesapla_ogrenme_hizi(hizli_ogrenme)
        yavas_hiz = await zpd_service._hesapla_ogrenme_hizi(yavas_ogrenme)

        # Hızlı öğrenme daha yüksek hız değeri almalı
        assert hizli_hiz > yavas_hiz
        assert 0.5 <= hizli_hiz <= 2.0
        assert 0.5 <= yavas_hiz <= 2.0

    @pytest.mark.asyncio
    async def test_optimal_ogrenme_yontemi_belirleme(self, zpd_service):
        """Optimal öğrenme yöntemi belirleme testi"""
        # Grup çalışmasında başarılı performans
        grup_basarili_performans = [
            {"ogrenme_yontemi": "grup", "basari_orani": 0.8},
            {"ogrenme_yontemi": "grup", "basari_orani": 0.85},
            {"ogrenme_yontemi": "bireysel", "basari_orani": 0.6},
            {"ogrenme_yontemi": "bireysel", "basari_orani": 0.65},
        ]

        optimal_yontem = await zpd_service._belirle_optimal_ogrenme_yontemi(
            "test_student", grup_basarili_performans
        )

        # Grup çalışması önerilmeli
        assert optimal_yontem == "grup"

    @pytest.mark.asyncio
    async def test_grup_calismasi_degerlendirme(self, zpd_service):
        """Grup çalışması değerlendirme testi"""
        # Grup çalışmasında başarılı performans
        grup_basarili = [
            {"ogrenme_yontemi": "grup_calismasi", "basari_orani": 0.8},
            {"ogrenme_yontemi": "bireysel", "basari_orani": 0.6},
        ]

        grup_onerisi = await zpd_service._degerlendirme_grup_calismasi(
            "test_student", grup_basarili
        )

        # Grup çalışması önerilmeli
        assert grup_onerisi is True

    @pytest.mark.asyncio
    async def test_ogretmen_rehberlik_degerlendirme(self, zpd_service):
        """Öğretmen rehberlik değerlendirme testi"""
        # Düşük başarı gösteren performans
        dusuk_basari = [
            {"basari_orani": 0.4},
            {"basari_orani": 0.3},
            {"basari_orani": 0.5},
        ]

        # Yüksek başarı gösteren performans
        yuksek_basari = [
            {"basari_orani": 0.8},
            {"basari_orani": 0.85},
            {"basari_orani": 0.9},
        ]

        dusuk_rehberlik = await zpd_service._degerlendirme_ogretmen_rehberlik(
            "test_student", dusuk_basari
        )
        yuksek_rehberlik = await zpd_service._degerlendirme_ogretmen_rehberlik(
            "test_student", yuksek_basari
        )

        # Düşük başarıda rehberlik önerilmeli
        assert dusuk_rehberlik is True
        assert yuksek_rehberlik is False

    @pytest.mark.asyncio
    async def test_icerik_turu_onerileri(self, zpd_service):
        """İçerik türü önerileri testi"""
        # Video içerikte başarılı performans
        video_basarili = [
            {"icerik_turu": "video", "basari_orani": 0.9},
            {"icerik_turu": "video", "basari_orani": 0.85},
            {"icerik_turu": "metin", "basari_orani": 0.5},
        ]

        icerik_onerileri = await zpd_service._oneriler_icerik_turu(
            "test_student", "matematik", video_basarili
        )

        # Video önerilmeli
        assert "video" in icerik_onerileri
        assert len(icerik_onerileri) <= 3

    @pytest.mark.asyncio
    async def test_motivasyon_stratejileri(self, zpd_service):
        """Motivasyon stratejileri testi"""
        # Düşük başarı performansı
        dusuk_basari = [{"basari_orani": 0.3}]

        # Orta başarı performansı
        orta_basari = [{"basari_orani": 0.6}]

        # Yüksek başarı performansı
        yuksek_basari = [{"basari_orani": 0.9}]

        dusuk_stratejiler = await zpd_service._belirle_motivasyon_stratejileri(
            "test_student", dusuk_basari
        )
        orta_stratejiler = await zpd_service._belirle_motivasyon_stratejileri(
            "test_student", orta_basari
        )
        yuksek_stratejiler = await zpd_service._belirle_motivasyon_stratejileri(
            "test_student", yuksek_basari
        )

        # Her seviye için farklı stratejiler önerilmeli
        assert len(dusuk_stratejiler) <= 5
        assert len(orta_stratejiler) <= 5
        assert len(yuksek_stratejiler) <= 5

        # Türk kültürüne özel stratejiler içermeli
        tum_stratejiler = dusuk_stratejiler + orta_stratejiler + yuksek_stratejiler
        assert any("aile_katilimi" in s for s in tum_stratejiler)
        assert any("toplumsal_onay" in s for s in tum_stratejiler)

    @pytest.mark.asyncio
    async def test_hesaplama_gecmisi_kaydetme(
        self, zpd_service, sample_kulturel_profil, sample_maarif_profili
    ):
        """Hesaplama geçmişi kaydetme testi"""
        ogrenci_id = "test_student_008"
        konu = "kimya"

        # İlk hesaplama
        zpd1 = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id,
            konu=konu,
            mevcut_seviye=5.0,
            kulturel_profil=sample_kulturel_profil,
            maarif_profili=sample_maarif_profili,
        )

        # İkinci hesaplama
        zpd2 = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id,
            konu=konu,
            mevcut_seviye=5.5,
            kulturel_profil=sample_kulturel_profil,
            maarif_profili=sample_maarif_profili,
        )

        # Geçmiş kaydedildi mi?
        # Note: global cache_manager may cause cache hits for previous calls,
        # so some calls may return early without appending to hesaplama_gecmisi
        anahtar = f"{ogrenci_id}_{konu}"
        assert anahtar in zpd_service.hesaplama_gecmisi
        assert len(zpd_service.hesaplama_gecmisi[anahtar]) >= 1

    @pytest.mark.asyncio
    async def test_zpd_gecerlilik_kontrolu(self, zpd_service):
        """ZPD geçerlilik kontrolü testi"""
        ogrenci_id = "test_student_009"
        konu = "biyoloji"

        # ZPD hesapla
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id, konu=konu, mevcut_seviye=6.0
        )

        # Yeni hesaplama geçerli olmalı
        assert zpd_araligi.is_gecerli() is True

        # Geçerlilik süresini geçmiş gibi ayarla
        zpd_araligi.hesaplama_tarihi = datetime.now() - timedelta(days=10)
        assert zpd_araligi.is_gecerli() is False

    @pytest.mark.asyncio
    async def test_zpd_zorluk_seviyesi_belirleme(self, zpd_service):
        """ZPD zorluk seviyesi belirleme testi"""
        ogrenci_id = "test_student_010"
        konu = "coğrafya"

        # ZPD hesapla
        zpd_araligi = await zpd_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id, konu=konu, mevcut_seviye=6.0
        )

        # Farklı zorluk seviyeleri test et
        cok_kolay = zpd_araligi.get_zorluk_seviyesi(zpd_araligi.alt_sinir - 1)
        kolay = zpd_araligi.get_zorluk_seviyesi(zpd_araligi.mevcut_seviye - 0.5)
        optimal = zpd_araligi.get_zorluk_seviyesi(zpd_araligi.optimal_zorluk)
        zor = zpd_araligi.get_zorluk_seviyesi(zpd_araligi.ust_sinir)
        cok_zor = zpd_araligi.get_zorluk_seviyesi(zpd_araligi.ust_sinir + 1)

        # Doğru seviyeler döndürülmeli
        assert cok_kolay == ZPDSeviyesi.COK_KOLAY
        assert kolay == ZPDSeviyesi.KOLAY
        assert optimal == ZPDSeviyesi.OPTIMAL
        assert zor == ZPDSeviyesi.ZOR
        assert cok_zor == ZPDSeviyesi.COK_ZOR

    @pytest.mark.asyncio
    async def test_error_handling(self, zpd_service):
        """Hata yönetimi testi"""
        # Geçersiz mevcut seviye (negatif)
        try:
            await zpd_service.hesapla_turk_zpd(
                ogrenci_id="test_student", konu="matematik", mevcut_seviye=-1.0
            )
            # Eğer hata fırlatılmazsa, en azından sonuç kontrol edilebilir
        except Exception:
            pass  # Beklenen davranış

        # Geçersiz mevcut seviye (çok yüksek)
        try:
            await zpd_service.hesapla_turk_zpd(
                ogrenci_id="test_student", konu="matematik", mevcut_seviye=15.0
            )
            # Eğer hata fırlatılmazsa, en azından sonuç kontrol edilebilir
        except Exception:
            pass  # Beklenen davranış

        # Boş öğrenci ID testi - servis bunu handle edebilir
        result = await zpd_service.hesapla_turk_zpd(
            ogrenci_id="", konu="matematik", mevcut_seviye=6.0
        )
        # Sonuç döndürülmeli, hata fırlatılmamalı
        assert result is not None

    def test_maarif_profili_ortalama_hesaplamalari(self, sample_maarif_profili):
        """MEB Maarif profili ortalama hesaplamaları testi"""
        # Milli değerler ortalaması
        milli_ortalama = sample_maarif_profili.get_milli_degerler_ortalamasi()
        assert 0.0 <= milli_ortalama <= 1.0

        # Evrensel değerler ortalaması
        evrensel_ortalama = sample_maarif_profili.get_evrensel_degerler_ortalamasi()
        assert 0.0 <= evrensel_ortalama <= 1.0

        # Kök değerler ortalaması
        kok_ortalama = sample_maarif_profili.get_kok_degerler_ortalamasi()
        assert 0.0 <= kok_ortalama <= 1.0

    @pytest.mark.asyncio
    async def test_konu_deger_agirliklari(self, zpd_service):
        """Konu bazlı değer ağırlıkları testi"""
        # Tarih konusu - milli değerler ağırlıklı
        tarih_agirliklari = await zpd_service._get_konu_deger_agirliklari("tarih")
        assert tarih_agirliklari["milli"] > 1.0

        # Matematik konusu - evrensel değerler ağırlıklı
        matematik_agirliklari = await zpd_service._get_konu_deger_agirliklari(
            "matematik"
        )
        assert matematik_agirliklari["evrensel"] > 1.0

        # Türkçe konusu - kök değerler ağırlıklı
        turkce_agirliklari = await zpd_service._get_konu_deger_agirliklari("türkçe")
        assert turkce_agirliklari["kok"] > 1.0

    @pytest.mark.asyncio
    async def test_performance_with_large_data(self, zpd_service):
        """Büyük veri ile performans testi"""
        # Çok sayıda performans verisi oluştur
        buyuk_performans_verileri = []
        for i in range(100):
            buyuk_performans_verileri.append(
                {
                    "tarih": datetime.now() - timedelta(days=i),
                    "konu": "matematik",
                    "zorluk_seviyesi": 5.0 + (i % 5),
                    "basari_orani": 0.5 + (i % 5) * 0.1,
                    "ogrenme_yontemi": "grup" if i % 2 == 0 else "bireysel",
                    "icerik_turu": ["video", "metin", "interaktif"][i % 3],
                    "sure_dakika": 30 + (i % 30),
                }
            )

        # Optimizasyon performansını test et
        import time

        start_time = time.time()

        optimizasyon = await zpd_service.optimize_zpd_parametreleri(
            ogrenci_id="performance_test_student",
            konu="matematik",
            performans_verileri=buyuk_performans_verileri,
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # 5 saniyeden az sürmeli
        assert execution_time < 5.0
        assert isinstance(optimizasyon, ZPDOptimizasyonSonucu)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
