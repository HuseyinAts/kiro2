from unittest.mock import Mock, patch, AsyncMock

"""
Kimlik doğrulama API testleri
"""
from fastapi.testclient import TestClient

from main import app
from models import KullaniciRolu

client = TestClient(app)


class TestAuthAPI:
    """Kimlik doğrulama API testleri"""

    def test_root_endpoint(self):
        """Ana endpoint testi"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Türkiye Üniversite Sınavları" in data["message"]

    def test_health_check(self):
        """Sağlık kontrolü endpoint testi"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "healthy"

    def test_kullanici_kayit_basarili(self):
        """Başarılı kullanıcı kaydı testi"""
        kullanici_data = {
            "email": "test@example.com",
            "ad_soyad": "Test Kullanıcı",
            "sifre": "test123",
            "rol": KullaniciRolu.OGRENCI,
        }

        response = client.post("/api/v1/auth/kayit", json=kullanici_data)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == kullanici_data["email"]
        assert data["ad_soyad"] == kullanici_data["ad_soyad"]
        assert data["rol"] == kullanici_data["rol"]
        assert "kullanici_id" in data

    def test_kullanici_kayit_duplicate_email(self):
        """Aynı e-posta ile ikinci kayıt testi"""
        kullanici_data = {
            "email": "duplicate@example.com",
            "ad_soyad": "Test Kullanıcı",
            "sifre": "test123",
            "rol": KullaniciRolu.OGRENCI,
        }

        # İlk kayıt
        response1 = client.post("/api/v1/auth/kayit", json=kullanici_data)
        assert response1.status_code == 200

        # İkinci kayıt (aynı e-posta)
        response2 = client.post("/api/v1/auth/kayit", json=kullanici_data)
        assert response2.status_code == 400
        assert "Bu e-posta adresi zaten kullanımda" in response2.json()["detail"]

    def test_kullanici_giris_basarili(self):
        """Başarılı kullanıcı girişi testi"""
        # Önce kullanıcı kaydet
        kullanici_data = {
            "email": "giris@example.com",
            "ad_soyad": "Giriş Test",
            "sifre": "test123",
            "rol": KullaniciRolu.OGRENCI,
        }
        client.post("/api/v1/auth/kayit", json=kullanici_data)

        # Giriş yap
        giris_data = {"email": "giris@example.com", "sifre": "test123"}

        response = client.post("/api/v1/auth/giris", json=giris_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["kullanici"]["email"] == giris_data["email"]

    def test_kullanici_giris_gecersiz_email(self):
        """Geçersiz e-posta ile giriş testi"""
        giris_data = {"email": "yokolmayan@example.com", "sifre": "test123"}

        response = client.post("/api/v1/auth/giris", json=giris_data)
        assert response.status_code == 401
        assert "Geçersiz e-posta veya şifre" in response.json()["detail"]

    def test_kullanici_giris_gecersiz_sifre(self):
        """Geçersiz şifre ile giriş testi"""
        # Önce kullanıcı kaydet
        kullanici_data = {
            "email": "sifre@example.com",
            "ad_soyad": "Şifre Test",
            "sifre": "dogruSifre",
            "rol": KullaniciRolu.OGRENCI,
        }
        client.post("/api/v1/auth/kayit", json=kullanici_data)

        # Yanlış şifre ile giriş yap
        giris_data = {"email": "sifre@example.com", "sifre": "yanlisSifre"}

        response = client.post("/api/v1/auth/giris", json=giris_data)
        assert response.status_code == 401
        assert "Geçersiz e-posta veya şifre" in response.json()["detail"]

    def test_profil_endpoint_token_gerekli(self):
        """Profil endpoint'i için token gerekli testi"""
        response = client.get("/api/v1/auth/profil")
        assert response.status_code == 403  # Forbidden - token yok

    def test_profil_endpoint_gecerli_token(self):
        """Geçerli token ile profil endpoint testi"""
        # Kullanıcı kaydet ve giriş yap
        kullanici_data = {
            "email": "profil@example.com",
            "ad_soyad": "Profil Test",
            "sifre": "test123",
            "rol": KullaniciRolu.OGRENCI,
        }
        client.post("/api/v1/auth/kayit", json=kullanici_data)

        giris_data = {"email": "profil@example.com", "sifre": "test123"}
        giris_response = client.post("/api/v1/auth/giris", json=giris_data)
        token = giris_response.json()["access_token"]

        # Profil bilgilerini al
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/profil", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == kullanici_data["email"]
        assert data["ad_soyad"] == kullanici_data["ad_soyad"]

    def test_kullanici_cikis(self):
        """Kullanıcı çıkış testi"""
        # Kullanıcı kaydet ve giriş yap
        kullanici_data = {
            "email": "cikis@example.com",
            "ad_soyad": "Çıkış Test",
            "sifre": "test123",
            "rol": KullaniciRolu.OGRENCI,
        }
        client.post("/api/v1/auth/kayit", json=kullanici_data)

        giris_data = {"email": "cikis@example.com", "sifre": "test123"}
        giris_response = client.post("/api/v1/auth/giris", json=giris_data)
        token = giris_response.json()["access_token"]

        # Çıkış yap
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/cikis", headers=headers)

        assert response.status_code == 200
        assert "Başarıyla çıkış yapıldı" in response.json()["message"]

        # Token artık geçersiz olmalı
        profil_response = client.get("/api/v1/auth/profil", headers=headers)
        assert profil_response.status_code == 401


class TestTurkceKarakterDestegi:
    """Türkçe karakter desteği testleri"""

    def test_turkce_karakterli_kullanici_kayit(self):
        """Türkçe karakterlerle kullanıcı kaydı testi"""
        kullanici_data = {
            "email": "öğrenci@örnek.com",
            "ad_soyad": "Çağlar Şahin Öğrenci",
            "sifre": "şifre123",
            "rol": KullaniciRolu.OGRENCI,
        }

        response = client.post("/api/v1/auth/kayit", json=kullanici_data)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == kullanici_data["email"]
        assert data["ad_soyad"] == kullanici_data["ad_soyad"]
        assert "Ç" in data["ad_soyad"]
        assert "ş" in data["ad_soyad"]
        assert "Ö" in data["ad_soyad"]

    def test_turkce_karakterli_giris(self):
        """Türkçe karakterlerle giriş testi"""
        # Türkçe karakterli kullanıcı kaydet
        kullanici_data = {
            "email": "türkçe@test.com",
            "ad_soyad": "Türkçe Test Kullanıcısı",
            "sifre": "türkçeŞifre123",
            "rol": KullaniciRolu.OGRENCI,
        }
        client.post("/api/v1/auth/kayit", json=kullanici_data)

        # Türkçe karakterli giriş
        giris_data = {"email": "türkçe@test.com", "sifre": "türkçeŞifre123"}

        response = client.post("/api/v1/auth/giris", json=giris_data)
        assert response.status_code == 200

        data = response.json()
        assert data["kullanici"]["ad_soyad"] == "Türkçe Test Kullanıcısı"
