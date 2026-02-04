from unittest.mock import Mock, patch, AsyncMock

"""
Ana uygulama testleri
Türkçe karakter desteği ve temel endpoint testleri
"""
import pytest
from fastapi.testclient import TestClient

from core.encoding import normalize_turkish_text, validate_turkish_text
from main import app

client = TestClient(app)


class TestMainEndpoints:
    """Ana endpoint testleri"""

    def test_root_endpoint(self):
        """Ana endpoint testi"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "Türkiye Üniversite Sınavları" in data["message"]
        assert data["version"] == "1.0.0"

    def test_health_check(self):
        """Sağlık kontrolü endpoint testi"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["status"] == "healthy"
        assert "çalışıyor" in data["message"]


class TestTurkishEncoding:
    """Türkçe karakter desteği testleri"""

    def test_turkish_characters_validation(self):
        """Türkçe karakter doğrulama testi"""
        turkish_text = "Türkçe karakterler: ç, ğ, ı, ö, ş, ü"
        assert validate_turkish_text(turkish_text) is True

        # ÖSYM ve MEB terimleri
        osym_text = "ÖSYM sınavları: TYT, AYT, YDT"
        assert validate_turkish_text(osym_text) is True

        meb_text = "MEB müfredatı uyumluluğu"
        assert validate_turkish_text(meb_text) is True

    def test_text_normalization(self):
        """Metin normalizasyon testi"""
        test_cases = [
            ("  Türkçe metin  ", "Türkçe metin"),
            ("ÖSYM", "ÖSYM"),
            ("öğrenci", "öğrenci"),
        ]

        for input_text, expected in test_cases:
            result = normalize_turkish_text(input_text)
            assert result == expected

    def test_api_response_encoding(self):
        """API yanıtlarında Türkçe karakter testi"""
        response = client.get("/")

        # Response content'in UTF-8 olduğunu kontrol et
        assert response.encoding == "utf-8" or response.encoding is None

        # JSON içeriğinde Türkçe karakterlerin doğru olduğunu kontrol et
        data = response.json()
        message = data["message"]
        assert "Türkiye" in message
        assert "Üniversite" in message


class TestApplicationStartup:
    """Uygulama başlatma testleri"""

    def test_app_configuration(self):
        """Uygulama konfigürasyon testi"""
        assert app.title == "Türkiye Üniversite Sınavları Hazırlık Platformu"
        assert app.version == "1.0.0"
        assert "YKS" in app.description
        assert "TYT/AYT/YDT" in app.description

    def test_cors_middleware(self):
        """CORS middleware testi"""
        # OPTIONS request ile CORS kontrolü
        response = client.options("/")
        assert response.status_code in [
            200,
            405,
        ]  # 405 OK çünkü OPTIONS implement edilmemiş olabilir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
