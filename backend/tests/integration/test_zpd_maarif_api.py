"""
Zone of Proximal Development + MEB Maarif API Testleri
ZPD Maarif sistemi API endpoint'leri için kapsamlı testler
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestZPDMaarifAPI:
    """ZPD Maarif API testleri"""

    def test_zpd_hesaplama_endpoint(self):
        """ZPD hesaplama endpoint testi"""
        request_data = {
            "ogrenci_id": "test_api_ogrenci_123",
            "konu": "matematik",
            "mevcut_seviye": 6.0,
        }

        response = client.post("/api/v1/zpd-maarif/hesapla", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data
        assert "message" in data
        assert "timestamp" in data

        zpd_data = data["data"]
        assert zpd_data["ogrenci_id"] == "test_api_ogrenci_123"
        assert zpd_data["konu"] == "matematik"
        assert zpd_data["mevcut_seviye"] == 6.0
        assert "optimal_zorluk" in zpd_data
        assert "hesaplama_guveni" in zpd_data
        assert "kulturel_uyum_guveni" in zpd_data

    def test_zpd_hesaplama_with_profiles(self):
        """Profiller ile ZPD hesaplama testi"""
        kulturel_profil = {
            "ogrenci_id": "test_api_ogrenci_123",
            "grup_calismasi_tercihi": 0.8,
            "ogretmene_saygi_seviyesi": 0.9,
            "aile_katilim_derecesi": 0.7,
            "akran_rekabet_egilimi": 0.6,
            "otorite_kabul_seviyesi": 0.8,
            "toplumsal_onay_ihtiyaci": 0.7,
            "basari_odaklilik": 0.9,
            "kolektif_kimlik_gucu": 0.8,
        }

        maarif_profili = {
            "ogrenci_id": "test_api_ogrenci_123",
            "vatan_sevgisi": 0.9,
            "millet_bilinci": 0.8,
            "aile_birligi": 0.95,
            "adalet": 0.85,
            "dostluk": 0.9,
            "durustluk": 0.8,
            "sabir": 0.7,
            "saygi": 0.95,
            "sevgi": 0.9,
        }

        request_data = {
            "ogrenci_id": "test_api_ogrenci_123",
            "konu": "matematik",
            "mevcut_seviye": 6.0,
            "kulturel_profil": kulturel_profil,
            "maarif_profili": maarif_profili,
        }

        response = client.post("/api/v1/zpd-maarif/hesapla", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

        zpd_data = data["data"]
        assert zpd_data["kulturel_carpan"] > 1.0  # Yüksek kültürel faktörler
        assert zpd_data["grup_calismasi_bonusu"] > 0.0  # Grup çalışması bonusu

    def test_zpd_hesaplama_invalid_data(self):
        """Geçersiz veri ile ZPD hesaplama testi"""
        # Geçersiz mevcut seviye
        request_data = {
            "ogrenci_id": "test_api_ogrenci_123",
            "konu": "matematik",
            "mevcut_seviye": 15.0,  # 10.0'dan büyük
        }

        response = client.post("/api/v1/zpd-maarif/hesapla", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_zpd_optimizasyon_endpoint(self):
        """ZPD optimizasyon endpoint testi"""
        performans_verileri = [
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

        request_data = {
            "ogrenci_id": "test_api_ogrenci_123",
            "konu": "matematik",
            "performans_verileri": performans_verileri,
        }

        response = client.post("/api/v1/zpd-maarif/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        optimizasyon_data = data["data"]
        assert optimizasyon_data["ogrenci_id"] == "test_api_ogrenci_123"
        assert optimizasyon_data["konu"] == "matematik"
        assert "onerilen_zorluk_seviyesi" in optimizasyon_data
        assert "onerilen_ogrenme_yontemi" in optimizasyon_data
        assert "grup_calismasi_onerisi" in optimizasyon_data
        assert "ogretmen_rehberlik_ihtiyaci" in optimizasyon_data
        assert "icerik_turu_onerileri" in optimizasyon_data
        assert "motivasyon_stratejileri" in optimizasyon_data
        assert "oneri_guveni" in optimizasyon_data
        assert "beklenen_basari_artisi" in optimizasyon_data

        # Grup çalışması daha başarılı olduğu için önerilmeli
        assert optimizasyon_data["grup_calismasi_onerisi"] == True

    def test_kulturel_profil_getirme(self):
        """Kültürel profil getirme endpoint testi"""
        response = client.get("/api/v1/zpd-maarif/profil/kulturel/test_api_ogrenci_123")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        profil_data = data["data"]
        assert profil_data["ogrenci_id"] == "test_api_ogrenci_123"
        assert "grup_calismasi_tercihi" in profil_data
        assert "ogretmene_saygi_seviyesi" in profil_data
        assert "aile_katilim_derecesi" in profil_data
        assert 0.0 <= profil_data["grup_calismasi_tercihi"] <= 1.0

    def test_maarif_profili_getirme(self):
        """MEB Maarif profili getirme endpoint testi"""
        response = client.get("/api/v1/zpd-maarif/profil/maarif/test_api_ogrenci_123")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        profil_data = data["data"]
        assert profil_data["ogrenci_id"] == "test_api_ogrenci_123"
        assert "vatan_sevgisi" in profil_data
        assert "millet_bilinci" in profil_data
        assert "adalet" in profil_data
        assert "sabir" in profil_data
        assert 0.0 <= profil_data["vatan_sevgisi"] <= 1.0

    def test_kulturel_profil_guncelleme(self):
        """Kültürel profil güncelleme endpoint testi"""
        updated_profil = {
            "ogrenci_id": "test_api_ogrenci_123",
            "grup_calismasi_tercihi": 0.9,
            "ogretmene_saygi_seviyesi": 0.95,
            "aile_katilim_derecesi": 0.8,
            "akran_rekabet_egilimi": 0.7,
            "otorite_kabul_seviyesi": 0.85,
            "toplumsal_onay_ihtiyaci": 0.75,
            "basari_odaklilik": 0.95,
            "kolektif_kimlik_gucu": 0.85,
            "bolge": "İç Anadolu",
            "sosyoekonomik_durum": "yüksek",
            "okul_turu": "özel",
        }

        response = client.put(
            "/api/v1/zpd-maarif/profil/kulturel/test_api_ogrenci_123",
            json=updated_profil,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        profil_data = data["data"]
        assert profil_data["grup_calismasi_tercihi"] == 0.9
        assert profil_data["bolge"] == "İç Anadolu"
        assert profil_data["okul_turu"] == "özel"

    def test_maarif_profili_guncelleme(self):
        """MEB Maarif profili güncelleme endpoint testi"""
        updated_profil = {
            "ogrenci_id": "test_api_ogrenci_123",
            "vatan_sevgisi": 0.95,
            "millet_bilinci": 0.9,
            "aile_birligi": 0.98,
            "bayrak_sevgisi": 0.9,
            "istiklal_ruhu": 0.85,
            "adalet": 0.9,
            "dostluk": 0.95,
            "durustluk": 0.85,
            "ozgurluk": 0.8,
            "esitlik": 0.85,
            "baris": 0.95,
            "sabir": 0.8,
            "saygi": 0.98,
            "sevgi": 0.95,
            "sorumluluk": 0.9,
            "duyarlilik": 0.8,
            "hosgoru": 0.85,
        }

        response = client.put(
            "/api/v1/zpd-maarif/profil/maarif/test_api_ogrenci_123", json=updated_profil
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        profil_data = data["data"]
        assert profil_data["vatan_sevgisi"] == 0.95
        assert profil_data["aile_birligi"] == 0.98
        assert profil_data["saygi"] == 0.98

    def test_zorluk_seviyesi_belirleme(self):
        """Zorluk seviyesi belirleme endpoint testi"""
        # Önce bir ZPD hesapla
        zpd_request = {
            "ogrenci_id": "test_zorluk_ogrenci",
            "konu": "matematik",
            "mevcut_seviye": 6.0,
        }

        zpd_response = client.post("/api/v1/zpd-maarif/hesapla", json=zpd_request)
        assert zpd_response.status_code == 200

        # Zorluk seviyesi belirle
        response = client.get(
            "/api/v1/zpd-maarif/zorluk-seviyesi",
            params={
                "ogrenci_id": "test_zorluk_ogrenci",
                "konu": "matematik",
                "hedef_zorluk": 7.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        zorluk_data = data["data"]
        assert zorluk_data["hedef_zorluk"] == 7.0
        assert "zorluk_seviyesi" in zorluk_data
        assert "zpd_araligi" in zorluk_data
        assert "oneri" in zorluk_data

        # Zorluk seviyesi enum değerlerinden biri olmalı
        valid_levels = ["cok_kolay", "kolay", "optimal", "zor", "cok_zor"]
        assert zorluk_data["zorluk_seviyesi"] in valid_levels

    def test_zpd_gecmisi_getirme(self):
        """ZPD geçmişi getirme endpoint testi"""
        # Önce birkaç ZPD hesapla
        for i, konu in enumerate(["matematik", "fizik", "kimya"]):
            zpd_request = {
                "ogrenci_id": "test_gecmis_ogrenci",
                "konu": konu,
                "mevcut_seviye": 5.0 + i,
            }

            response = client.post("/api/v1/zpd-maarif/hesapla", json=zpd_request)
            assert response.status_code == 200

        # Geçmişi getir
        response = client.get("/api/v1/zpd-maarif/gecmis/test_gecmis_ogrenci")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        gecmis_data = data["data"]
        assert "gecmis" in gecmis_data
        assert "toplam_kayit" in gecmis_data
        assert gecmis_data["toplam_kayit"] == 3

        # Geçmiş kayıtları kontrol et
        gecmis_listesi = gecmis_data["gecmis"]
        assert len(gecmis_listesi) == 3

        for kayit in gecmis_listesi:
            assert "konu" in kayit
            assert "hesaplama_tarihi" in kayit
            assert "optimal_zorluk" in kayit
            assert "hesaplama_guveni" in kayit
            assert kayit["konu"] in ["matematik", "fizik", "kimya"]

    def test_zpd_gecmisi_konu_filtresi(self):
        """ZPD geçmişi konu filtresi testi"""
        # Geçmişi matematik konusu ile filtrele
        response = client.get(
            "/api/v1/zpd-maarif/gecmis/test_gecmis_ogrenci",
            params={"konu": "matematik", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        gecmis_data = data["data"]
        gecmis_listesi = gecmis_data["gecmis"]

        # Sadece matematik konusu olmalı
        for kayit in gecmis_listesi:
            assert kayit["konu"] == "matematik"

    def test_zpd_istatistikleri(self):
        """ZPD istatistikleri endpoint testi"""
        response = client.get("/api/v1/zpd-maarif/istatistikler/test_gecmis_ogrenci")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "data" in data

        istatistik_data = data["data"]
        assert "toplam_hesaplama" in istatistik_data
        assert "ortalama_optimal_zorluk" in istatistik_data
        assert "ortalama_hesaplama_guveni" in istatistik_data
        assert "konu_dagilimi" in istatistik_data

        assert istatistik_data["toplam_hesaplama"] == 3
        assert isinstance(istatistik_data["ortalama_optimal_zorluk"], float)
        assert isinstance(istatistik_data["ortalama_hesaplama_guveni"], float)
        assert isinstance(istatistik_data["konu_dagilimi"], dict)

        # Konu dağılımında matematik, fizik, kimya olmalı
        konu_dagilimi = istatistik_data["konu_dagilimi"]
        assert "matematik" in konu_dagilimi
        assert "fizik" in konu_dagilimi
        assert "kimya" in konu_dagilimi

    def test_zpd_istatistikleri_bos_gecmis(self):
        """Boş geçmiş ile ZPD istatistikleri testi"""
        response = client.get("/api/v1/zpd-maarif/istatistikler/bos_gecmis_ogrenci")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        istatistik_data = data["data"]

        assert istatistik_data["toplam_hesaplama"] == 0
        assert istatistik_data["ortalama_optimal_zorluk"] == 0.0
        assert istatistik_data["ortalama_hesaplama_guveni"] == 0.0
        assert istatistik_data["konu_dagilimi"] == {}

    def test_api_error_handling(self):
        """API hata yönetimi testi"""
        # Geçersiz öğrenci ID ile profil getirme
        response = client.get("/api/v1/zpd-maarif/profil/kulturel/")
        assert response.status_code == 404  # Not found

        # Geçersiz JSON ile ZPD hesaplama
        response = client.post("/api/v1/zpd-maarif/hesapla", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

        # Geçersiz parametre ile zorluk seviyesi
        response = client.get(
            "/api/v1/zpd-maarif/zorluk-seviyesi",
            params={
                "ogrenci_id": "test",
                "konu": "matematik",
                "hedef_zorluk": 15.0,  # 10.0'dan büyük
            },
        )
        assert response.status_code == 422  # Validation error

    def test_api_response_format(self):
        """API yanıt formatı testi"""
        request_data = {
            "ogrenci_id": "test_format_ogrenci",
            "konu": "matematik",
            "mevcut_seviye": 6.0,
        }

        response = client.post("/api/v1/zpd-maarif/hesapla", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Standart API yanıt formatı
        required_fields = ["success", "data", "message", "timestamp"]
        for field in required_fields:
            assert field in data

        assert isinstance(data["success"], bool)
        assert data["success"] == True
        assert isinstance(data["message"], str)
        assert isinstance(data["timestamp"], str)

        # Timestamp ISO format kontrolü
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Timestamp ISO formatında değil")


class TestZPDMaarifAPIIntegration:
    """ZPD Maarif API entegrasyon testleri"""

    def test_full_zpd_workflow_via_api(self):
        """API üzerinden tam ZPD iş akışı testi"""
        ogrenci_id = "test_workflow_ogrenci"

        # 1. Başlangıç ZPD hesaplama
        zpd_request = {
            "ogrenci_id": ogrenci_id,
            "konu": "matematik",
            "mevcut_seviye": 5.0,
        }

        zpd_response = client.post("/api/v1/zpd-maarif/hesapla", json=zpd_request)
        assert zpd_response.status_code == 200

        zpd_data = zpd_response.json()["data"]
        optimal_zorluk = zpd_data["optimal_zorluk"]

        # 2. Performans verileri ile optimizasyon
        performans_verileri = [
            {
                "tarih": "2024-01-01",
                "basari_orani": 0.6,
                "zorluk_seviyesi": optimal_zorluk,
                "ogrenme_yontemi": "bireysel",
                "icerik_turu": "metin",
            },
            {
                "tarih": "2024-01-02",
                "basari_orani": 0.75,
                "zorluk_seviyesi": optimal_zorluk + 0.2,
                "ogrenme_yontemi": "grup",
                "icerik_turu": "video",
            },
        ]

        optimize_request = {
            "ogrenci_id": ogrenci_id,
            "konu": "matematik",
            "performans_verileri": performans_verileri,
        }

        optimize_response = client.post(
            "/api/v1/zpd-maarif/optimize", json=optimize_request
        )
        assert optimize_response.status_code == 200

        optimize_data = optimize_response.json()["data"]
        onerilen_zorluk = optimize_data["onerilen_zorluk_seviyesi"]

        # 3. Zorluk seviyesi kontrolü
        zorluk_response = client.get(
            "/api/v1/zpd-maarif/zorluk-seviyesi",
            params={
                "ogrenci_id": ogrenci_id,
                "konu": "matematik",
                "hedef_zorluk": onerilen_zorluk,
            },
        )

        assert zorluk_response.status_code == 200
        zorluk_data = zorluk_response.json()["data"]

        # Önerilen zorluk optimal seviyede olmalı
        assert zorluk_data["zorluk_seviyesi"] in ["optimal", "zor"]

        # 4. Geçmiş kontrolü
        gecmis_response = client.get(f"/api/v1/zpd-maarif/gecmis/{ogrenci_id}")
        assert gecmis_response.status_code == 200

        gecmis_data = gecmis_response.json()["data"]
        assert gecmis_data["toplam_kayit"] >= 1

        # 5. İstatistikler
        istatistik_response = client.get(
            f"/api/v1/zpd-maarif/istatistikler/{ogrenci_id}"
        )
        assert istatistik_response.status_code == 200

        istatistik_data = istatistik_response.json()["data"]
        assert istatistik_data["toplam_hesaplama"] >= 1
        assert "matematik" in istatistik_data["konu_dagilimi"]

    def test_profile_update_affects_zpd(self):
        """Profil güncellemesinin ZPD'ye etkisi testi"""
        ogrenci_id = "test_profile_effect_ogrenci"

        # 1. İlk ZPD hesaplama (varsayılan profil ile)
        zpd_request = {
            "ogrenci_id": ogrenci_id,
            "konu": "matematik",
            "mevcut_seviye": 6.0,
        }

        ilk_zpd_response = client.post("/api/v1/zpd-maarif/hesapla", json=zpd_request)
        assert ilk_zpd_response.status_code == 200

        ilk_zpd_data = ilk_zpd_response.json()["data"]
        ilk_optimal_zorluk = ilk_zpd_data["optimal_zorluk"]

        # 2. Kültürel profili güncelle (yüksek grup çalışması tercihi)
        updated_kulturel_profil = {
            "ogrenci_id": ogrenci_id,
            "grup_calismasi_tercihi": 0.95,
            "ogretmene_saygi_seviyesi": 0.95,
            "aile_katilim_derecesi": 0.9,
            "akran_rekabet_egilimi": 0.8,
            "otorite_kabul_seviyesi": 0.9,
            "toplumsal_onay_ihtiyaci": 0.8,
            "basari_odaklilik": 0.95,
            "kolektif_kimlik_gucu": 0.9,
        }

        profil_response = client.put(
            f"/api/v1/zpd-maarif/profil/kulturel/{ogrenci_id}",
            json=updated_kulturel_profil,
        )
        assert profil_response.status_code == 200

        # 3. Güncellenmiş profil ile ZPD hesaplama
        zpd_request_with_profile = {
            "ogrenci_id": ogrenci_id,
            "konu": "matematik",
            "mevcut_seviye": 6.0,
            "kulturel_profil": updated_kulturel_profil,
        }

        yeni_zpd_response = client.post(
            "/api/v1/zpd-maarif/hesapla", json=zpd_request_with_profile
        )
        assert yeni_zpd_response.status_code == 200

        yeni_zpd_data = yeni_zpd_response.json()["data"]
        yeni_optimal_zorluk = yeni_zpd_data["optimal_zorluk"]

        # 4. Profil güncellemesi ZPD'yi etkilemeli
        assert yeni_zpd_data["kulturel_carpan"] > ilk_zpd_data["kulturel_carpan"]
        assert (
            yeni_zpd_data["grup_calismasi_bonusu"]
            > ilk_zpd_data["grup_calismasi_bonusu"]
        )

        # Yüksek grup çalışması tercihi daha yüksek optimal zorluk vermeli
        assert yeni_optimal_zorluk >= ilk_optimal_zorluk
