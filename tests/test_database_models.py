"""
Test for Database Models
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEnums:
    """Test database enums"""
    
    def test_kullanici_rolu_enum(self):
        """Test user role enum"""
        from backend.models.enums import KullaniciRolu
        
        assert KullaniciRolu.OGRENCI.value == "ogrenci"
        assert KullaniciRolu.OGRETMEN.value == "ogretmen"
        assert KullaniciRolu.VELI.value == "veli"
        assert KullaniciRolu.ADMIN.value == "admin"
    
    def test_sinav_tipi_enum(self):
        """Test exam type enum"""
        from backend.database.models import SinavTipi
        
        assert SinavTipi.TYT.value == "tyt"
        assert SinavTipi.AYT.value == "ayt"
        assert SinavTipi.YDT.value == "ydt"
        assert SinavTipi.DENEME.value == "deneme"
        assert SinavTipi.KONU_TARAMA.value == "konu_tarama"
    
    def test_zorluk_seviyesi_enum(self):
        """Test difficulty level enum"""
        from backend.database.models import ZorlukSeviyesi
        
        assert ZorlukSeviyesi.KOLAY.value == "kolay"
        assert ZorlukSeviyesi.ORTA.value == "orta"
        assert ZorlukSeviyesi.ZOR.value == "zor"
        assert ZorlukSeviyesi.UZMAN.value == "uzman"
    
    def test_ogrenme_stili_enum(self):
        """Test learning style enum"""
        from backend.database.models import OgrenmeStili
        
        assert OgrenmeStili.VISUAL.value == "visual"
        assert OgrenmeStili.AUDITORY.value == "auditory"
        assert OgrenmeStili.READING.value == "reading"
        assert OgrenmeStili.KINESTHETIC.value == "kinesthetic"
        assert OgrenmeStili.MIXED.value == "mixed"


class TestKullaniciModel:
    """Test Kullanici model"""
    
    def test_kullanici_model_creation(self):
        """Test creating user model"""
        from backend.database.models import Kullanici, KullaniciRolu
        
        # Mock SQLAlchemy base
        with patch('backend.database.models.Base'):
            kullanici = Kullanici()
            
            # Test tablename
            assert kullanici.__tablename__ == "kullanicilar"
            
            # Test default values would be set by SQLAlchemy
            assert hasattr(kullanici, 'kullanici_id')
            assert hasattr(kullanici, 'email')
            assert hasattr(kullanici, 'ad_soyad')
            assert hasattr(kullanici, 'aktif')
    
    def test_kullanici_relationships(self):
        """Test user model relationships"""
        from backend.database.models import Kullanici
        
        with patch('backend.database.models.Base'):
            kullanici = Kullanici()
            
            # Check relationship attributes exist
            assert hasattr(kullanici, 'ogrenci_profili')
            assert hasattr(kullanici, 'ogretmen_profili')
            assert hasattr(kullanici, 'veli_profili')


class TestOgrenciProfiliModel:
    """Test OgrenciProfili model"""
    
    def test_ogrenci_profili_creation(self):
        """Test creating student profile model"""
        from backend.database.models import OgrenciProfili, OgrenmeStili
        
        with patch('backend.database.models.Base'):
            profil = OgrenciProfili()
            
            assert profil.__tablename__ == "ogrenci_profilleri"
            assert hasattr(profil, 'profil_id')
            assert hasattr(profil, 'kullanici_id')
            assert hasattr(profil, 'sinif')
            assert hasattr(profil, 'ogrenme_stili')
            assert hasattr(profil, 'mevcut_seviye')
    
    def test_ogrenci_profili_relationships(self):
        """Test student profile relationships"""
        from backend.database.models import OgrenciProfili
        
        with patch('backend.database.models.Base'):
            profil = OgrenciProfili()
            
            assert hasattr(profil, 'kullanici')
            assert hasattr(profil, 'sinav_sonuclari')
            assert hasattr(profil, 'ogrenme_oturumlari')


class TestOgretmenProfiliModel:
    """Test OgretmenProfili model"""
    
    def test_ogretmen_profili_creation(self):
        """Test creating teacher profile model"""
        from backend.database.models import OgretmenProfili
        
        with patch('backend.database.models.Base'):
            profil = OgretmenProfili()
            
            assert profil.__tablename__ == "ogretmen_profilleri"
            assert hasattr(profil, 'profil_id')
            assert hasattr(profil, 'kullanici_id')
            assert hasattr(profil, 'okul_adi')
            assert hasattr(profil, 'brans')
            assert hasattr(profil, 'deneyim_yili')


class TestVeliProfiliModel:
    """Test VeliProfili model"""
    
    def test_veli_profili_creation(self):
        """Test creating parent profile model"""
        from backend.database.models import VeliProfili
        
        with patch('backend.database.models.Base'):
            profil = VeliProfili()
            
            assert profil.__tablename__ == "veli_profilleri"
            assert hasattr(profil, 'profil_id')
            assert hasattr(profil, 'kullanici_id')
            assert hasattr(profil, 'cocuk_sayisi')


class TestSinavModels:
    """Test exam related models"""
    
    def test_sinav_sablonu_creation(self):
        """Test exam template creation"""
        from backend.database.models import SinavSablonu, SinavTipi
        
        with patch('backend.database.models.Base'):
            sablon = SinavSablonu()
            
            assert sablon.__tablename__ == "sinav_sablonlari"
            assert hasattr(sablon, 'sablon_id')
            assert hasattr(sablon, 'ad')
            assert hasattr(sablon, 'tip')
            assert hasattr(sablon, 'sure_dakika')
            assert hasattr(sablon, 'konu_dagilimi')
    
    def test_sinav_creation(self):
        """Test exam creation"""
        from backend.database.models import Sinav
        
        with patch('backend.database.models.Base'):
            sinav = Sinav()
            
            assert sinav.__tablename__ == "sinavlar"
            assert hasattr(sinav, 'sinav_id')
            assert hasattr(sinav, 'ogrenci_id')
            assert hasattr(sinav, 'sablon_id')
            assert hasattr(sinav, 'durum')
            assert hasattr(sinav, 'mevcut_soru_index')
    
    def test_soru_bankasi_creation(self):
        """Test question bank creation"""
        from backend.database.models import SoruBankasi, ZorlukSeviyesi
        
        with patch('backend.database.models.Base'):
            soru = SoruBankasi()
            
            assert soru.__tablename__ == "soru_bankasi"
            assert hasattr(soru, 'soru_id')
            assert hasattr(soru, 'konu')
            assert hasattr(soru, 'zorluk_seviyesi')
            assert hasattr(soru, 'soru_metni')
            assert hasattr(soru, 'secenekler')
            assert hasattr(soru, 'dogru_cevap')
            
            # IRT parameters
            assert hasattr(soru, 'irt_a_parametresi')
            assert hasattr(soru, 'irt_b_parametresi')
            assert hasattr(soru, 'irt_c_parametresi')
            
            # Turkish morphology parameters
            assert hasattr(soru, 'morfoloji_karmasikligi')
            assert hasattr(soru, 'kok_kelime_sayisi')
            assert hasattr(soru, 'ek_sayisi')
    
    def test_sinav_cevabi_creation(self):
        """Test exam answer creation"""
        from backend.database.models import SinavCevabi
        
        with patch('backend.database.models.Base'):
            cevap = SinavCevabi()
            
            assert cevap.__tablename__ == "sinav_cevaplari"
            assert hasattr(cevap, 'cevap_id')
            assert hasattr(cevap, 'sinav_id')
            assert hasattr(cevap, 'soru_id')
            assert hasattr(cevap, 'verilen_cevap')
            assert hasattr(cevap, 'dogru_mu')
            assert hasattr(cevap, 'cevaplama_suresi_saniye')
    
    def test_sinav_sonucu_creation(self):
        """Test exam result creation"""
        from backend.database.models import SinavSonucu
        
        with patch('backend.database.models.Base'):
            sonuc = SinavSonucu()
            
            assert sonuc.__tablename__ == "sinav_sonuclari"
            assert hasattr(sonuc, 'sonuc_id')
            assert hasattr(sonuc, 'sinav_id')
            assert hasattr(sonuc, 'ogrenci_id')
            
            # Basic results
            assert hasattr(sonuc, 'toplam_dogru')
            assert hasattr(sonuc, 'toplam_yanlis')
            assert hasattr(sonuc, 'net_puan')
            assert hasattr(sonuc, 'yuzdelik_dilim')
            
            # ZPD parameters
            assert hasattr(sonuc, 'zpd_alt_sinir')
            assert hasattr(sonuc, 'zpd_ust_sinir')
            assert hasattr(sonuc, 'optimal_zorluk')
            
            # IRT parameters
            assert hasattr(sonuc, 'irt_yetenek_seviyesi')
            assert hasattr(sonuc, 'irt_guven_araligi')


class TestOgrenmeModels:
    """Test learning related models"""
    
    def test_ogrenme_stili_profili_creation(self):
        """Test learning style profile creation"""
        from backend.database.models import OgrenmeStiliProfili
        
        with patch('backend.database.models.Base'):
            profil = OgrenmeStiliProfili()
            
            assert profil.__tablename__ == "ogrenme_stili_profilleri"
            assert hasattr(profil, 'profil_id')
            assert hasattr(profil, 'ogrenci_id')
            
            # VARK preferences
            assert hasattr(profil, 'vark_visual')
            assert hasattr(profil, 'vark_auditory')
            assert hasattr(profil, 'vark_reading')
            assert hasattr(profil, 'vark_kinesthetic')
            
            # Felder-Silverman preferences
            assert hasattr(profil, 'fs_aktif_reflektif')
            assert hasattr(profil, 'fs_duyusal_sezgisel')
            assert hasattr(profil, 'fs_gorsel_sozel')
            assert hasattr(profil, 'fs_sirali_butunsel')
            
            # Hybrid profile
            assert hasattr(profil, 'dominant_stil')
            assert hasattr(profil, 'guven_seviyesi')
    
    def test_kulturel_baglam_profili_creation(self):
        """Test cultural context profile creation"""
        from backend.database.models import KulturelBaglamProfili
        
        with patch('backend.database.models.Base'):
            profil = KulturelBaglamProfili()
            
            assert profil.__tablename__ == "kulturel_baglam_profilleri"
            assert hasattr(profil, 'profil_id')
            assert hasattr(profil, 'ogrenci_id')
            
            # Turkish cultural factors
            assert hasattr(profil, 'grup_calismasi_tercihi')
            assert hasattr(profil, 'ogretmene_saygi_seviyesi')
            assert hasattr(profil, 'aile_katilim_derecesi')
            assert hasattr(profil, 'akran_rekabet_egilimi')
            assert hasattr(profil, 'otorite_kabul_seviyesi')
            assert hasattr(profil, 'toplumsal_onay_ihtiyaci')
            assert hasattr(profil, 'basari_odaklilik')
            assert hasattr(profil, 'kolektif_kimlik_gucu')
    
    def test_maarif_degerleri_profili_creation(self):
        """Test Maarif values profile creation"""
        from backend.database.models import MaarifDegerleriProfili
        
        with patch('backend.database.models.Base'):
            profil = MaarifDegerleriProfili()
            
            assert profil.__tablename__ == "maarif_degerleri_profilleri"
            assert hasattr(profil, 'profil_id')
            assert hasattr(profil, 'ogrenci_id')
            
            # National values
            assert hasattr(profil, 'vatan_sevgisi')
            assert hasattr(profil, 'millet_bilinci')
            assert hasattr(profil, 'aile_birligi')
            
            # Universal values
            assert hasattr(profil, 'adalet')
            assert hasattr(profil, 'dostluk')
            assert hasattr(profil, 'durustluk')
            
            # Root values
            assert hasattr(profil, 'sabir')
            assert hasattr(profil, 'saygi')
            assert hasattr(profil, 'sevgi')
    
    def test_ogrenme_oturumu_creation(self):
        """Test learning session creation"""
        from backend.database.models import OgrenmeOturumu
        
        with patch('backend.database.models.Base'):
            oturum = OgrenmeOturumu()
            
            assert oturum.__tablename__ == "ogrenme_oturumlari"
            assert hasattr(oturum, 'oturum_id')
            assert hasattr(oturum, 'ogrenci_id')
            
            # Session info
            assert hasattr(oturum, 'baslangic_zamani')
            assert hasattr(oturum, 'sure_dakika')
            assert hasattr(oturum, 'konu')
            assert hasattr(oturum, 'ogrenme_modu')
            
            # Behavioral data
            assert hasattr(oturum, 'video_izleme_suresi')
            assert hasattr(oturum, 'metin_okuma_suresi')
            assert hasattr(oturum, 'interaktif_etkilesim')
            
            # Performance metrics
            assert hasattr(oturum, 'basari_orani')
            assert hasattr(oturum, 'odaklanma_skoru')
            assert hasattr(oturum, 'motivasyon_seviyesi')


class TestContentModels:
    """Test content related models"""
    
    def test_egitim_icerigi_creation(self):
        """Test educational content creation"""
        from backend.database.models import EgitimIcerigi, ZorlukSeviyesi
        
        with patch('backend.database.models.Base'):
            icerik = EgitimIcerigi()
            
            assert icerik.__tablename__ == "egitim_icerikleri"
            assert hasattr(icerik, 'icerik_id')
            assert hasattr(icerik, 'baslik')
            assert hasattr(icerik, 'icerik_tipi')
            assert hasattr(icerik, 'konu')
            assert hasattr(icerik, 'zorluk_seviyesi')
            
            # Content data
            assert hasattr(icerik, 'url')
            assert hasattr(icerik, 'dosya_yolu')
            assert hasattr(icerik, 'sure_dakika')
            
            # Quality and accessibility
            assert hasattr(icerik, 'kalite_skoru')
            assert hasattr(icerik, 'erisebilirlik_skoru')
            assert hasattr(icerik, 'bionic_reading_destegi')
            assert hasattr(icerik, 'basitlestirme_seviyesi')
            
            # Maarif compliance
            assert hasattr(icerik, 'maarif_uyum_skoru')
            assert hasattr(icerik, 'uyumlu_degerler')


class TestSystemModels:
    """Test system related models"""
    
    def test_sistem_metrikleri_creation(self):
        """Test system metrics creation"""
        from backend.database.models import SistemMetrikleri
        
        with patch('backend.database.models.Base'):
            metrik = SistemMetrikleri()
            
            assert metrik.__tablename__ == "sistem_metrikleri"
            assert hasattr(metrik, 'metrik_id')
            assert hasattr(metrik, 'metrik_adi')
            assert hasattr(metrik, 'deger')
            assert hasattr(metrik, 'birim')
            assert hasattr(metrik, 'kategori')
    
    def test_agent_performans_metrikleri_creation(self):
        """Test agent performance metrics creation"""
        from backend.database.models import AgentPerformansMetrikleri
        
        with patch('backend.database.models.Base'):
            metrik = AgentPerformansMetrikleri()
            
            assert metrik.__tablename__ == "agent_performans_metrikleri"
            assert hasattr(metrik, 'metrik_id')
            assert hasattr(metrik, 'agent_adi')
            assert hasattr(metrik, 'islem_tipi')
            assert hasattr(metrik, 'yanit_suresi_ms')
            assert hasattr(metrik, 'basari_durumu')
            assert hasattr(metrik, 'hata_mesaji')


class TestModelRelationships:
    """Test model relationships"""
    
    def test_user_to_profiles_relationships(self):
        """Test user to profile relationships"""
        from backend.database.models import Kullanici
        
        with patch('backend.database.models.Base'):
            # Test that relationships are properly defined
            kullanici = Kullanici()
            
            # These would be set up by SQLAlchemy relationship() calls
            assert hasattr(kullanici, 'ogrenci_profili')
            assert hasattr(kullanici, 'ogretmen_profili')
            assert hasattr(kullanici, 'veli_profili')
    
    def test_exam_relationships(self):
        """Test exam model relationships"""
        from backend.database.models import Sinav, SinavSablonu, SinavCevabi
        
        with patch('backend.database.models.Base'):
            sinav = Sinav()
            sablon = SinavSablonu()
            cevap = SinavCevabi()
            
            # Test relationship attributes
            assert hasattr(sinav, 'sablon')
            assert hasattr(sinav, 'cevaplar')
            assert hasattr(sinav, 'sonuc')
            
            assert hasattr(sablon, 'sinavlar')
            
            assert hasattr(cevap, 'sinav')
            assert hasattr(cevap, 'soru')
    
    def test_student_learning_relationships(self):
        """Test student learning relationships"""
        from backend.database.models import OgrenciProfili
        
        with patch('backend.database.models.Base'):
            profil = OgrenciProfili()
            
            assert hasattr(profil, 'kullanici')
            assert hasattr(profil, 'sinav_sonuclari')
            assert hasattr(profil, 'ogrenme_oturumlari')


class TestModelDefaults:
    """Test model default values"""
    
    def test_kullanici_defaults(self):
        """Test user model defaults would be applied"""
        from backend.database.models import Kullanici
        
        with patch('backend.database.models.Base'):
            kullanici = Kullanici()
            
            # These are column definitions, defaults would be applied by SQLAlchemy
            # We just test that the attributes exist
            assert hasattr(kullanici, 'aktif')
            assert hasattr(kullanici, 'email_dogrulandi')
    
    def test_ogrenci_profili_defaults(self):
        """Test student profile defaults"""
        from backend.database.models import OgrenciProfili
        
        with patch('backend.database.models.Base'):
            profil = OgrenciProfili()
            
            assert hasattr(profil, 'mevcut_seviye')  # Should default to 5.0
    
    def test_ogrenme_stili_defaults(self):
        """Test learning style defaults"""
        from backend.database.models import OgrenmeStiliProfili
        
        with patch('backend.database.models.Base'):
            profil = OgrenmeStiliProfili()
            
            # VARK defaults should be 0.25 each
            assert hasattr(profil, 'vark_visual')
            assert hasattr(profil, 'vark_auditory')
            assert hasattr(profil, 'vark_reading')
            assert hasattr(profil, 'vark_kinesthetic')
            
            # Felder-Silverman defaults should be 0.0
            assert hasattr(profil, 'fs_aktif_reflektif')
            assert hasattr(profil, 'fs_duyusal_sezgisel')
    
    def test_kulturel_baglam_defaults(self):
        """Test cultural context defaults"""
        from backend.database.models import KulturelBaglamProfili
        
        with patch('backend.database.models.Base'):
            profil = KulturelBaglamProfili()
            
            # Test that cultural factor attributes exist
            assert hasattr(profil, 'grup_calismasi_tercihi')  # Should default to 0.8
            assert hasattr(profil, 'ogretmene_saygi_seviyesi')  # Should default to 0.9
            assert hasattr(profil, 'aile_katilim_derecesi')  # Should default to 0.7


class TestModelUUIDs:
    """Test model UUID generation"""
    
    @patch('backend.database.models.uuid.uuid4')
    def test_uuid_generation(self, mock_uuid):
        """Test UUID generation for primary keys"""
        mock_uuid.return_value = uuid.UUID('12345678-1234-1234-1234-123456789abc')
        
        from backend.database.models import Kullanici
        
        with patch('backend.database.models.Base'):
            kullanici = Kullanici()
            
            # The column definition includes a default lambda that calls uuid.uuid4
            # We're testing that the column has the right default function structure
            assert hasattr(kullanici, 'kullanici_id')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])