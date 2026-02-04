"""
Comprehensive unit tests for ZPD Maarif models
Testing Turkish educational culture adaptation models for Zone of Proximal Development
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from models.zpd_maarif import (
    MaarifDegeri,
    TurkKulturFaktoru,
    ZPDSeviyesi,
    KulturelBaglamProfili,
    MaarifDegerleriProfili,
    TurkZPDAraligi,
    ZPDHesaplamaParametreleri,
    ZPDHesaplamaGecmisi,
    ZPDOptimizasyonSonucu,
)


class TestMaarifDegeriEnum:
    """Test MaarifDegeri enum values"""

    def test_milli_degerler_values(self):
        """Test national values"""
        assert MaarifDegeri.VATAN_SEVGISI == "vatan_sevgisi"
        assert MaarifDegeri.MILLET_BILINCI == "millet_bilinci"
        assert MaarifDegeri.AILE_BIRLIGI == "aile_birligi"
        assert MaarifDegeri.BAYRAK_SEVGISI == "bayrak_sevgisi"
        assert MaarifDegeri.ISTIKLAL_RUHU == "istiklal_ruhu"

    def test_evrensel_degerler_values(self):
        """Test universal values"""
        assert MaarifDegeri.ADALET == "adalet"
        assert MaarifDegeri.DOSTLUK == "dostluk"
        assert MaarifDegeri.DURUSTLUK == "durustluk"
        assert MaarifDegeri.OZGURLUK == "ozgurluk"
        assert MaarifDegeri.ESITLIK == "esitlik"
        assert MaarifDegeri.BARIŞ == "baris"

    def test_kok_degerler_values(self):
        """Test core values"""
        assert MaarifDegeri.SABIR == "sabir"
        assert MaarifDegeri.SAYGI == "saygi"
        assert MaarifDegeri.SEVGI == "sevgi"
        assert MaarifDegeri.SORUMLULUK == "sorumluluk"
        assert MaarifDegeri.DUYARLILIK == "duyarlilik"
        assert MaarifDegeri.HOSGORU == "hosgoru"


class TestTurkKulturFaktoruEnum:
    """Test Turkish culture factor enum"""

    def test_all_kultur_faktoru_values(self):
        """Test all cultural factor values"""
        assert TurkKulturFaktoru.GRUP_CALISMASI_TERCIHI == "grup_calismasi_tercihi"
        assert TurkKulturFaktoru.OGRETMENE_SAYGI == "ogretmene_saygi"
        assert TurkKulturFaktoru.AILE_KATILIMI == "aile_katilimi"
        assert TurkKulturFaktoru.AKRAN_REKABETI == "akran_rekabeti"
        assert TurkKulturFaktoru.OTORITE_KABULU == "otorite_kabulu"
        assert TurkKulturFaktoru.TOPLUMSAL_ONAY == "toplumsal_onay"
        assert TurkKulturFaktoru.BASARI_ODAKLILIK == "basari_odaklilik"
        assert TurkKulturFaktoru.KOLEKTIF_KIMLIK == "kolektif_kimlik"


class TestZPDSeviyesiEnum:
    """Test ZPD difficulty level enum"""

    def test_all_zpd_seviyeleri(self):
        """Test all ZPD levels"""
        assert ZPDSeviyesi.COK_KOLAY == "cok_kolay"
        assert ZPDSeviyesi.KOLAY == "kolay"
        assert ZPDSeviyesi.OPTIMAL == "optimal"
        assert ZPDSeviyesi.ZOR == "zor"
        assert ZPDSeviyesi.COK_ZOR == "cok_zor"


class TestKulturelBaglamProfili:
    """Test cultural context profile model"""

    def test_valid_profil_with_defaults(self):
        """Test creating profile with default values"""
        profil = KulturelBaglamProfili(ogrenci_id="student123")

        assert profil.ogrenci_id == "student123"
        assert profil.grup_calismasi_tercihi == 0.7
        assert profil.ogretmene_saygi_seviyesi == 0.8
        assert profil.aile_katilim_derecesi == 0.6
        assert profil.akran_rekabet_egilimi == 0.5
        assert profil.otorite_kabul_seviyesi == 0.7
        assert profil.toplumsal_onay_ihtiyaci == 0.6
        assert profil.basari_odaklilik == 0.8
        assert profil.kolektif_kimlik_gucu == 0.7

    def test_valid_profil_with_custom_values(self):
        """Test creating profile with custom values"""
        profil = KulturelBaglamProfili(
            ogrenci_id="student456",
            grup_calismasi_tercihi=0.9,
            ogretmene_saygi_seviyesi=0.95,
            aile_katilim_derecesi=0.85,
            akran_rekabet_egilimi=0.7,
            bolge="Marmara",
            sosyoekonomik_durum="orta",
            okul_turu="devlet",
        )

        assert profil.ogrenci_id == "student456"
        assert profil.grup_calismasi_tercihi == 0.9
        assert profil.bolge == "Marmara"
        assert profil.okul_turu == "devlet"

    @pytest.mark.parametrize(
        "field_name,invalid_value",
        [
            ("grup_calismasi_tercihi", -0.1),
            ("ogretmene_saygi_seviyesi", 1.5),
            ("aile_katilim_derecesi", 2.0),
            ("akran_rekabet_egilimi", -1.0),
        ],
    )
    def test_invalid_score_values(self, field_name, invalid_value):
        """Test validation fails for scores outside 0-1 range"""
        with pytest.raises(ValidationError):
            KulturelBaglamProfili(ogrenci_id="test", **{field_name: invalid_value})

    def test_boundary_values(self):
        """Test boundary values (0.0 and 1.0)"""
        profil = KulturelBaglamProfili(
            ogrenci_id="boundary_test",
            grup_calismasi_tercihi=0.0,
            ogretmene_saygi_seviyesi=1.0,
            aile_katilim_derecesi=0.0,
            akran_rekabet_egilimi=1.0,
        )

        assert profil.grup_calismasi_tercihi == 0.0
        assert profil.ogretmene_saygi_seviyesi == 1.0


class TestMaarifDegerleriProfili:
    """Test Maarif values profile model"""

    def test_valid_profil_with_defaults(self):
        """Test creating profile with default values"""
        profil = MaarifDegerleriProfili(ogrenci_id="student789")

        assert profil.ogrenci_id == "student789"
        # Milli değerler
        assert profil.vatan_sevgisi == 0.8
        assert profil.millet_bilinci == 0.7
        assert profil.aile_birligi == 0.9
        # Evrensel değerler
        assert profil.adalet == 0.8
        assert profil.dostluk == 0.9
        # Kök değerler
        assert profil.sabir == 0.7
        assert profil.saygi == 0.9

    def test_milli_degerler_ortalamasi(self):
        """Test calculating average of national values"""
        profil = MaarifDegerleriProfili(
            ogrenci_id="test",
            vatan_sevgisi=0.8,
            millet_bilinci=0.7,
            aile_birligi=0.9,
            bayrak_sevgisi=0.8,
            istiklal_ruhu=0.8,
        )

        ortalama = profil.get_milli_degerler_ortalamasi()
        expected = (0.8 + 0.7 + 0.9 + 0.8 + 0.8) / 5
        assert abs(ortalama - expected) < 0.001

    def test_evrensel_degerler_ortalamasi(self):
        """Test calculating average of universal values"""
        profil = MaarifDegerleriProfili(
            ogrenci_id="test",
            adalet=0.9,
            dostluk=0.8,
            durustluk=0.85,
            ozgurluk=0.75,
            esitlik=0.8,
            baris=0.9,
        )

        ortalama = profil.get_evrensel_degerler_ortalamasi()
        expected = (0.9 + 0.8 + 0.85 + 0.75 + 0.8 + 0.9) / 6
        assert abs(ortalama - expected) < 0.001

    def test_kok_degerler_ortalamasi(self):
        """Test calculating average of core values"""
        profil = MaarifDegerleriProfili(
            ogrenci_id="test",
            sabir=0.7,
            saygi=0.9,
            sevgi=0.8,
            sorumluluk=0.85,
            duyarlilik=0.75,
            hosgoru=0.8,
        )

        ortalama = profil.get_kok_degerler_ortalamasi()
        expected = (0.7 + 0.9 + 0.8 + 0.85 + 0.75 + 0.8) / 6
        assert abs(ortalama - expected) < 0.001

    def test_all_ortalamalar(self):
        """Test all average calculations work together"""
        profil = MaarifDegerleriProfili(ogrenci_id="comprehensive_test")

        milli_ort = profil.get_milli_degerler_ortalamasi()
        evrensel_ort = profil.get_evrensel_degerler_ortalamasi()
        kok_ort = profil.get_kok_degerler_ortalamasi()

        assert 0.0 <= milli_ort <= 1.0
        assert 0.0 <= evrensel_ort <= 1.0
        assert 0.0 <= kok_ort <= 1.0


class TestTurkZPDAraligi:
    """Test Turkish ZPD range model"""

    def test_valid_zpd_araligi(self):
        """Test creating valid ZPD range"""
        zpd = TurkZPDAraligi(
            ogrenci_id="student123",
            konu="Matematik",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        assert zpd.ogrenci_id == "student123"
        assert zpd.konu == "Matematik"
        assert zpd.mevcut_seviye == 5.0
        assert zpd.alt_sinir == 4.0
        assert zpd.ust_sinir == 7.0
        assert zpd.optimal_zorluk == 6.0

    def test_is_gecerli_within_validity(self):
        """Test validity check for recent calculation"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
            gecerlilik_suresi_gun=7,
        )

        assert zpd.is_gecerli() is True

    def test_is_gecerli_expired(self):
        """Test validity check for expired calculation"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
            hesaplama_tarihi=datetime.now() - timedelta(days=10),
            gecerlilik_suresi_gun=7,
        )

        assert zpd.is_gecerli() is False

    def test_get_zorluk_seviyesi_cok_kolay(self):
        """Test difficulty level: very easy"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        seviye = zpd.get_zorluk_seviyesi(3.0)
        assert seviye == ZPDSeviyesi.COK_KOLAY

    def test_get_zorluk_seviyesi_kolay(self):
        """Test difficulty level: easy"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        seviye = zpd.get_zorluk_seviyesi(4.5)
        assert seviye == ZPDSeviyesi.KOLAY

    def test_get_zorluk_seviyesi_optimal(self):
        """Test difficulty level: optimal"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        seviye = zpd.get_zorluk_seviyesi(5.5)
        assert seviye == ZPDSeviyesi.OPTIMAL

    def test_get_zorluk_seviyesi_zor(self):
        """Test difficulty level: hard"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        seviye = zpd.get_zorluk_seviyesi(6.5)
        assert seviye == ZPDSeviyesi.ZOR

    def test_get_zorluk_seviyesi_cok_zor(self):
        """Test difficulty level: very hard"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        seviye = zpd.get_zorluk_seviyesi(8.0)
        assert seviye == ZPDSeviyesi.COK_ZOR

    def test_kulturel_ayarlamalar(self):
        """Test cultural adjustments fields"""
        zpd = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Test",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
            kulturel_carpan=1.2,
            maarif_uyum_katsayisi=0.9,
            grup_calismasi_bonusu=0.2,
            ogretmen_rehberlik_faktoru=0.15,
        )

        assert zpd.kulturel_carpan == 1.2
        assert zpd.maarif_uyum_katsayisi == 0.9
        assert zpd.grup_calismasi_bonusu == 0.2
        assert zpd.ogretmen_rehberlik_faktoru == 0.15


class TestZPDHesaplamaParametreleri:
    """Test ZPD calculation parameters model"""

    def test_default_parametreler(self):
        """Test default parameters"""
        params = ZPDHesaplamaParametreleri()

        assert params.temel_zpd_genisligi == 0.3
        assert params.optimal_zorluk_orani == 0.7
        assert params.grup_calismasi_agirligi == 0.2
        assert params.ogretmen_saygi_agirligi == 0.15
        assert params.basari_artis_carpani == 1.1
        assert params.basarisizlik_azalma_carpani == 0.9

    def test_custom_parametreler(self):
        """Test custom parameters"""
        params = ZPDHesaplamaParametreleri(
            temel_zpd_genisligi=0.4,
            optimal_zorluk_orani=0.8,
            grup_calismasi_agirligi=0.3,
            milli_degerler_agirligi=0.2,
        )

        assert params.temel_zpd_genisligi == 0.4
        assert params.optimal_zorluk_orani == 0.8
        assert params.grup_calismasi_agirligi == 0.3
        assert params.milli_degerler_agirligi == 0.2

    def test_parameter_boundaries(self):
        """Test parameter boundary validation"""
        # Valid boundaries
        params = ZPDHesaplamaParametreleri(
            temel_zpd_genisligi=0.1,
            optimal_zorluk_orani=0.5,
            basari_artis_carpani=1.0,
            basarisizlik_azalma_carpani=1.0,
        )
        assert params.temel_zpd_genisligi == 0.1

        # Invalid boundaries should raise ValidationError
        with pytest.raises(ValidationError):
            ZPDHesaplamaParametreleri(temel_zpd_genisligi=0.05)


class TestZPDHesaplamaGecmisi:
    """Test ZPD calculation history model"""

    def test_complete_hesaplama_gecmisi(self):
        """Test creating complete calculation history"""
        zpd_araligi = TurkZPDAraligi(
            ogrenci_id="test",
            konu="Matematik",
            mevcut_seviye=5.0,
            alt_sinir=4.0,
            ust_sinir=7.0,
            optimal_zorluk=6.0,
        )

        params = ZPDHesaplamaParametreleri()
        kulturel_profil = KulturelBaglamProfili(ogrenci_id="test")
        maarif_profili = MaarifDegerleriProfili(ogrenci_id="test")

        gecmis = ZPDHesaplamaGecmisi(
            ogrenci_id="test",
            konu="Matematik",
            hesaplama_tarihi=datetime.now(),
            zpd_araligi=zpd_araligi,
            kullanilan_parametreler=params,
            kulturel_profil=kulturel_profil,
            maarif_profili=maarif_profili,
            onceki_basari_orani=0.75,
            sonraki_basari_orani=0.82,
            tahmin_dogrulugu=0.88,
        )

        assert gecmis.ogrenci_id == "test"
        assert gecmis.konu == "Matematik"
        assert gecmis.onceki_basari_orani == 0.75
        assert gecmis.sonraki_basari_orani == 0.82
        assert gecmis.tahmin_dogrulugu == 0.88


class TestZPDOptimizasyonSonucu:
    """Test ZPD optimization result model"""

    def test_complete_optimizasyon_sonucu(self):
        """Test creating complete optimization result"""
        sonuc = ZPDOptimizasyonSonucu(
            ogrenci_id="student123",
            konu="Fizik",
            onerilen_zorluk_seviyesi=6.5,
            onerilen_ogrenme_yontemi="Görsel öğrenme",
            grup_calismasi_onerisi=True,
            ogretmen_rehberlik_ihtiyaci=False,
            icerik_turu_onerileri=["Video", "Infografik", "İnteraktif simülasyon"],
            ogrenme_hizi_ayarlama=1.2,
            motivasyon_stratejileri=[
                "Oyunlaştırma",
                "Ödül sistemi",
                "Başarı rozetleri",
            ],
            oneri_guveni=0.85,
            beklenen_basari_artisi=0.15,
        )

        assert sonuc.ogrenci_id == "student123"
        assert sonuc.konu == "Fizik"
        assert sonuc.onerilen_zorluk_seviyesi == 6.5
        assert sonuc.grup_calismasi_onerisi is True
        assert sonuc.ogretmen_rehberlik_ihtiyaci is False
        assert len(sonuc.icerik_turu_onerileri) == 3
        assert len(sonuc.motivasyon_stratejileri) == 3
        assert sonuc.oneri_guveni == 0.85
        assert sonuc.beklenen_basari_artisi == 0.15

    def test_optimizasyon_guven_validation(self):
        """Test confidence score validation"""
        # Valid confidence scores
        sonuc = ZPDOptimizasyonSonucu(
            ogrenci_id="test",
            konu="Test",
            onerilen_zorluk_seviyesi=5.0,
            onerilen_ogrenme_yontemi="Test",
            grup_calismasi_onerisi=False,
            ogretmen_rehberlik_ihtiyaci=False,
            icerik_turu_onerileri=[],
            ogrenme_hizi_ayarlama=1.0,
            motivasyon_stratejileri=[],
            oneri_guveni=0.0,
            beklenen_basari_artisi=1.0,
        )
        assert sonuc.oneri_guveni == 0.0
        assert sonuc.beklenen_basari_artisi == 1.0

        # Invalid confidence scores should raise ValidationError
        with pytest.raises(ValidationError):
            ZPDOptimizasyonSonucu(
                ogrenci_id="test",
                konu="Test",
                onerilen_zorluk_seviyesi=5.0,
                onerilen_ogrenme_yontemi="Test",
                grup_calismasi_onerisi=False,
                ogretmen_rehberlik_ihtiyaci=False,
                icerik_turu_onerileri=[],
                ogrenme_hizi_ayarlama=1.0,
                motivasyon_stratejileri=[],
                oneri_guveni=1.5,
                beklenen_basari_artisi=0.5,
            )
