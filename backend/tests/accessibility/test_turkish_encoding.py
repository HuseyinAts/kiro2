"""
Test: Turkish Character Encoding Validation
Task 45: Accessibility and Compliance Testing

Bu test dosyası, Türkçe karakterlerin (ç, ğ, ı, ö, ş, ü, Ç, Ğ, İ, Ö, Ş, Ü)
tüm platformda doğru şekilde kodlandığını ve görüntülendiğini test eder.

Requirements: 7.4, 9.1
"""

import os
import sys
import pytest
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch, AsyncMock
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TurkishEncodingValidator:
    """Türkçe karakter encoding doğrulayıcı"""

    def __init__(self):
        self.turkish_chars = {
            "lowercase": ["ç", "ğ", "ı", "ö", "ş", "ü"],
            "uppercase": ["Ç", "Ğ", "İ", "Ö", "Ş", "Ü"],
            "all": ["ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "Ğ", "İ", "Ö", "Ş", "Ü"],
        }
        self.test_results = []
        self.test_sentences = [
            "Çalışkan öğrenciler başarılı olur.",
            "Ğ harfi Türkçe'ye özgüdür.",
            "İstanbul'da güzel bir gün.",
            "Öğretmen öğrencilere ders anlatıyor.",
            "Şehir merkezinde çok kalabalık.",
            "Üniversite sınavına hazırlanıyorum.",
        ]

    def test_utf8_encoding(self, content: str) -> Dict[str, Any]:
        """UTF-8 encoding testi"""
        result = {
            "test_name": "UTF-8 Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
            "tested_chars": [],
        }

        try:
            # UTF-8 encode/decode testi
            encoded = content.encode("utf-8")
            decoded = encoded.decode("utf-8")

            if decoded == content:
                result["passed"] = True

                # Türkçe karakterleri test et
                for char in self.turkish_chars["all"]:
                    if char in content:
                        result["tested_chars"].append(char)
                        # Karakterin doğru encode edildiğini kontrol et
                        char_encoded = char.encode("utf-8")
                        if len(char_encoded) != 2:  # Türkçe karakterler 2 byte olmalı
                            result["issues"].append(
                                f"'{char}' karakteri yanlış encode edilmiş"
                            )
                            result["passed"] = False
            else:
                result["issues"].append("UTF-8 encoding/decoding başarısız")
                result["recommendations"].append(
                    "Tüm dosyaları UTF-8 encoding ile kaydedin"
                )

        except UnicodeEncodeError as e:
            result["issues"].append(f"UTF-8 encoding hatası: {str(e)}")
            result["recommendations"].append(
                "Dosya encoding'ini UTF-8 olarak ayarlayın"
            )
        except UnicodeDecodeError as e:
            result["issues"].append(f"UTF-8 decoding hatası: {str(e)}")
            result["recommendations"].append("Dosya encoding'ini kontrol edin")

        self.test_results.append(result)
        return result

    def test_html_meta_charset(self, html_content: str) -> Dict[str, Any]:
        """HTML meta charset testi"""
        result = {
            "test_name": "HTML Meta Charset",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Meta charset kontrolü
        charset_patterns = [
            r'<meta\s+charset\s*=\s*["\']?utf-8["\']?',
            r'<meta\s+http-equiv\s*=\s*["\']Content-Type["\'][^>]*charset\s*=\s*utf-8',
        ]

        has_utf8_charset = any(
            re.search(pattern, html_content, re.IGNORECASE)
            for pattern in charset_patterns
        )

        if has_utf8_charset:
            result["passed"] = True
        else:
            result["issues"].append("HTML meta charset=utf-8 eksik")
            result["recommendations"].append('<meta charset="UTF-8"> ekleyin')

        self.test_results.append(result)
        return result

    def test_database_encoding(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Veritabanı encoding testi"""
        result = {
            "test_name": "Database Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # PostgreSQL için UTF-8 kontrolü
        if "charset" in db_config or "encoding" in db_config:
            charset = db_config.get("charset") or db_config.get("encoding")
            if charset.upper() in ["UTF8", "UTF-8"]:
                result["passed"] = True
            else:
                result["issues"].append(f"Veritabanı charset '{charset}' UTF-8 değil")
                result["recommendations"].append(
                    "Veritabanı charset'ini UTF-8 olarak ayarlayın"
                )
        else:
            result["issues"].append("Veritabanı charset tanımı bulunamadı")
            result["recommendations"].append(
                "Veritabanı bağlantısına charset=utf8 ekleyin"
            )

        self.test_results.append(result)
        return result

    def test_api_response_encoding(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """API response encoding testi"""
        result = {
            "test_name": "API Response Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
            "tested_fields": [],
        }

        try:
            # JSON serialize/deserialize testi
            json_str = json.dumps(response_data, ensure_ascii=False)
            parsed_data = json.loads(json_str)

            # Türkçe karakterleri kontrol et
            def check_turkish_chars(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        check_turkish_chars(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_turkish_chars(item, f"{path}[{i}]")
                elif isinstance(obj, str):
                    for char in self.turkish_chars["all"]:
                        if char in obj:
                            result["tested_fields"].append(path)
                            # Karakterin doğru encode edildiğini kontrol et
                            if char not in parsed_data.get(path.split(".")[-1], ""):
                                result["issues"].append(
                                    f"'{char}' karakteri {path} alanında kayboldu"
                                )
                                return

            check_turkish_chars(response_data)

            if not result["issues"]:
                result["passed"] = True

        except (json.JSONDecodeError, UnicodeEncodeError) as e:
            result["issues"].append(f"JSON encoding hatası: {str(e)}")
            result["recommendations"].append(
                "API response'larında ensure_ascii=False kullanın"
            )

        self.test_results.append(result)
        return result

    def test_url_encoding(self, url: str) -> Dict[str, Any]:
        """URL encoding testi (Türkçe karakterler için)"""
        result = {
            "test_name": "URL Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Türkçe karakter içeren URL'leri kontrol et
        has_turkish = any(char in url for char in self.turkish_chars["all"])

        if has_turkish:
            # URL encode edilmiş mi kontrol et
            if "%" in url:
                result["passed"] = True
            else:
                result["issues"].append("URL'de Türkçe karakterler encode edilmemiş")
                result["recommendations"].append(
                    "URL'lerdeki Türkçe karakterleri percent-encode edin"
                )
        else:
            result["passed"] = True  # Türkçe karakter yoksa test geçer

        self.test_results.append(result)
        return result

    def test_file_system_encoding(self, file_path: str) -> Dict[str, Any]:
        """Dosya sistemi encoding testi"""
        result = {
            "test_name": "File System Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        try:
            # Dosya adında Türkçe karakter kontrolü
            has_turkish = any(char in file_path for char in self.turkish_chars["all"])

            if has_turkish:
                # Dosya adının encode edilebilir olduğunu kontrol et
                encoded_path = file_path.encode("utf-8")
                decoded_path = encoded_path.decode("utf-8")

                if decoded_path == file_path:
                    result["passed"] = True
                else:
                    result["issues"].append("Dosya adı encoding sorunu")
                    result["recommendations"].append(
                        "Dosya adlarında ASCII karakterler kullanın"
                    )
            else:
                result["passed"] = True

        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            result["issues"].append(f"Dosya adı encoding hatası: {str(e)}")
            result["recommendations"].append(
                "Dosya adlarında Türkçe karakter kullanmaktan kaçının"
            )

        self.test_results.append(result)
        return result

    def test_form_data_encoding(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Form data encoding testi"""
        result = {
            "test_name": "Form Data Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
            "tested_fields": [],
        }

        try:
            # Form data'yı URL encode et
            from urllib.parse import urlencode, parse_qs

            encoded = urlencode(form_data)
            decoded = parse_qs(encoded)

            # Türkçe karakterleri kontrol et
            for key, value in form_data.items():
                if any(char in value for char in self.turkish_chars["all"]):
                    result["tested_fields"].append(key)

                    # Decode edilen değeri kontrol et
                    decoded_value = decoded.get(key, [""])[0]
                    if decoded_value != value:
                        result["issues"].append(
                            f"'{key}' alanında Türkçe karakter kaybı"
                        )

            if not result["issues"]:
                result["passed"] = True

        except Exception as e:
            result["issues"].append(f"Form data encoding hatası: {str(e)}")
            result["recommendations"].append(
                "Form encoding'ini application/x-www-form-urlencoded; charset=UTF-8 olarak ayarlayın"
            )

        self.test_results.append(result)
        return result

    def test_console_output_encoding(self, text: str) -> Dict[str, Any]:
        """Console output encoding testi"""
        result = {
            "test_name": "Console Output Encoding",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        try:
            # Console'a yazdırma simülasyonu
            import sys
            import io

            # UTF-8 destekli StringIO buffer
            buffer = io.StringIO()

            # Türkçe karakterleri yaz
            buffer.write(text)
            output = buffer.getvalue()

            # Türkçe karakterlerin korunduğunu kontrol et
            if output == text:
                result["passed"] = True
            else:
                result["issues"].append("Console output'ta Türkçe karakter kaybı")
                result["recommendations"].append(
                    "PYTHONIOENCODING=utf-8 environment variable'ını ayarlayın"
                )

        except UnicodeEncodeError as e:
            result["issues"].append(f"Console encoding hatası: {str(e)}")
            result["recommendations"].append(
                "Console encoding'ini UTF-8 olarak ayarlayın"
            )

        self.test_results.append(result)
        return result

    def generate_encoding_report(self) -> Dict[str, Any]:
        """Encoding doğrulama raporu oluştur"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "encoding_compliance_percentage": (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0,
            "fully_utf8_compliant": passed_tests == total_tests,
            "turkish_characters_tested": self.turkish_chars["all"],
            "detailed_results": self.test_results,
        }


# Test Fixtures
@pytest.fixture
def encoding_validator():
    """Turkish encoding validator fixture"""
    return TurkishEncodingValidator()


@pytest.fixture
def sample_turkish_content():
    """Türkçe içerik örneği"""
    return """
    Türkiye Üniversite Sınavları Hazırlık Platformu
    
    Çalışkan öğrenciler için özel olarak tasarlanmış bu platform,
    YKS (TYT/AYT/YDT) sınavlarına hazırlık sürecinde öğrencilere
    kapsamlı destek sağlar.
    
    Özellikler:
    - Ğ, ı, ş gibi Türkçe karakterler tam destek
    - İstanbul, Ankara, İzmir gibi şehirlerde kullanılabilir
    - Öğretmen ve öğrenci panelleri
    - Şeffaf ve güvenilir sistem
    """


@pytest.fixture
def sample_html_with_turkish():
    """Türkçe karakterler içeren HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>YKS Hazırlık - Türkçe Dil Desteği</title>
    </head>
    <body>
        <h1>Çalışma Programı</h1>
        <p>Öğrenciler için özel hazırlanmış içerikler.</p>
        <p>Ğ, ı, ö, ş, ü gibi Türkçe karakterler desteklenir.</p>
    </body>
    </html>
    """


@pytest.fixture
def sample_api_response():
    """Türkçe içerikli API response"""
    return {
        "success": True,
        "message": "Sınav başarıyla tamamlandı",
        "data": {
            "student_name": "Çağlar Öztürk",
            "exam_title": "TYT Matematik Denemesi",
            "subjects": ["Türkçe", "Matematik", "Fen Bilimleri"],
            "feedback": "Çok başarılı! Öğrenme hızın çok iyi.",
            "weak_areas": ["Geometri", "Olasılık"],
        },
    }


@pytest.fixture
def sample_db_config():
    """Veritabanı konfigürasyonu"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "turkiye_sinav",
        "charset": "UTF8",
        "encoding": "UTF-8",
    }


# Turkish Encoding Tests


@pytest.mark.asyncio
async def test_utf8_encoding_basic(encoding_validator, sample_turkish_content):
    """
    Test: Temel UTF-8 encoding
    Türkçe karakterler doğru encode/decode edilmeli
    """
    result = encoding_validator.test_utf8_encoding(sample_turkish_content)

    assert result["passed"] == True, "UTF-8 encoding başarılı olmalı"
    assert len(result["tested_chars"]) > 0, "Türkçe karakterler test edilmeli"

    # Tüm Türkçe karakterlerin test edildiğini kontrol et
    for char in ["ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "İ", "Ö", "Ş", "Ü"]:
        if char in sample_turkish_content:
            assert char in result["tested_chars"]


@pytest.mark.asyncio
async def test_html_meta_charset_present(encoding_validator, sample_html_with_turkish):
    """
    Test: HTML meta charset
    HTML dosyaları UTF-8 charset tanımı içermeli
    """
    result = encoding_validator.test_html_meta_charset(sample_html_with_turkish)

    assert result["passed"] == True, "HTML meta charset=UTF-8 olmalı"
    assert '<meta charset="UTF-8">' in sample_html_with_turkish


@pytest.mark.asyncio
async def test_database_utf8_encoding(encoding_validator, sample_db_config):
    """
    Test: Veritabanı UTF-8 encoding
    PostgreSQL veritabanı UTF-8 charset kullanmalı
    """
    result = encoding_validator.test_database_encoding(sample_db_config)

    assert result["passed"] == True, "Veritabanı UTF-8 charset kullanmalı"


@pytest.mark.asyncio
async def test_api_response_turkish_chars(encoding_validator, sample_api_response):
    """
    Test: API response Türkçe karakterler
    API yanıtlarında Türkçe karakterler korunmalı
    """
    result = encoding_validator.test_api_response_encoding(sample_api_response)

    assert result["passed"] == True, "API response'da Türkçe karakterler korunmalı"
    assert len(result["tested_fields"]) > 0


@pytest.mark.asyncio
async def test_url_encoding_turkish_chars(encoding_validator):
    """
    Test: URL encoding Türkçe karakterler
    URL'lerde Türkçe karakterler percent-encode edilmeli
    """
    # Türkçe karakter içeren URL
    url_with_turkish = "https://example.com/search?q=çalışma"
    result_unencoded = encoding_validator.test_url_encoding(url_with_turkish)
    assert result_unencoded["passed"] == False

    # Encode edilmiş URL
    url_encoded = "https://example.com/search?q=%C3%A7al%C4%B1%C5%9Fma"
    result_encoded = encoding_validator.test_url_encoding(url_encoded)
    assert result_encoded["passed"] == True


@pytest.mark.asyncio
async def test_file_system_encoding(encoding_validator):
    """
    Test: Dosya sistemi encoding
    Dosya adlarında Türkçe karakterler doğru işlenmeli
    """
    # ASCII dosya adı
    result_ascii = encoding_validator.test_file_system_encoding("test_file.txt")
    assert result_ascii["passed"] == True

    # Türkçe karakter içeren dosya adı
    result_turkish = encoding_validator.test_file_system_encoding("çalışma_dosyası.txt")
    assert result_turkish["passed"] == True


@pytest.mark.asyncio
async def test_form_data_encoding(encoding_validator):
    """
    Test: Form data encoding
    Form verilerinde Türkçe karakterler korunmalı
    """
    form_data = {
        "student_name": "Öğrenci Adı",
        "subject": "Türkçe",
        "feedback": "Çok başarılı! Öğrenme hızın güzel.",
    }

    result = encoding_validator.test_form_data_encoding(form_data)

    assert result["passed"] == True, "Form data'da Türkçe karakterler korunmalı"
    assert len(result["tested_fields"]) > 0


@pytest.mark.asyncio
async def test_console_output_encoding(encoding_validator):
    """
    Test: Console output encoding
    Console çıktısında Türkçe karakterler doğru görüntülenmeli
    """
    turkish_text = "Çalışkan öğrenciler başarılı olur. Ğ, ı, ö, ş, ü karakterleri."

    result = encoding_validator.test_console_output_encoding(turkish_text)

    assert result["passed"] == True, "Console output'ta Türkçe karakterler korunmalı"


@pytest.mark.asyncio
async def test_json_serialization_turkish(encoding_validator):
    """
    Test: JSON serialization Türkçe karakterler
    JSON serialize/deserialize işlemlerinde Türkçe karakterler korunmalı
    """
    data = {
        "title": "Çalışma Programı",
        "description": "Öğrenciler için özel içerik",
        "tags": ["Türkçe", "Matematik", "Fen Bilimleri"],
    }

    # JSON serialize
    json_str = json.dumps(data, ensure_ascii=False)

    # Türkçe karakterlerin korunduğunu kontrol et
    assert "Çalışma" in json_str
    assert "Öğrenciler" in json_str
    assert "Türkçe" in json_str

    # JSON deserialize
    parsed = json.loads(json_str)
    assert parsed == data


@pytest.mark.asyncio
async def test_all_turkish_characters(encoding_validator):
    """
    Test: Tüm Türkçe karakterler
    Tüm Türkçe karakterlerin (ç, ğ, ı, ö, ş, ü, Ç, Ğ, İ, Ö, Ş, Ü) doğru işlendiğini test et
    """
    all_chars_text = "ç ğ ı ö ş ü Ç Ğ İ Ö Ş Ü çalışma öğrenci ışık şehir üniversite ÇALIŞMA ÖĞRETMEN İSTANBUL ŞUBAT ÜLKE"

    result = encoding_validator.test_utf8_encoding(all_chars_text)

    assert result["passed"] == True

    # Tüm Türkçe karakterlerin test edildiğini kontrol et
    expected_chars = ["ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "Ğ", "İ", "Ö", "Ş", "Ü"]
    for char in expected_chars:
        assert char in result["tested_chars"], f"'{char}' karakteri test edilmedi"


@pytest.mark.asyncio
async def test_generate_full_encoding_report(
    encoding_validator,
    sample_turkish_content,
    sample_html_with_turkish,
    sample_api_response,
    sample_db_config,
):
    """
    Test: Tam encoding doğrulama raporu
    """
    # Tüm testleri çalıştır
    encoding_validator.test_utf8_encoding(sample_turkish_content)
    encoding_validator.test_html_meta_charset(sample_html_with_turkish)
    encoding_validator.test_database_encoding(sample_db_config)
    encoding_validator.test_api_response_encoding(sample_api_response)
    encoding_validator.test_url_encoding(
        "https://example.com/search?q=%C3%A7al%C4%B1%C5%9Fma"
    )
    encoding_validator.test_file_system_encoding("test_file.txt")
    encoding_validator.test_form_data_encoding({"name": "Öğrenci"})
    encoding_validator.test_console_output_encoding("Türkçe metin")

    # Rapor oluştur
    report = encoding_validator.generate_encoding_report()

    assert "total_tests" in report
    assert "passed" in report
    assert "encoding_compliance_percentage" in report
    assert "fully_utf8_compliant" in report
    assert "turkish_characters_tested" in report

    # En az %95 uyumluluk bekliyoruz
    assert report["encoding_compliance_percentage"] >= 95.0

    print(f"\n=== Türkçe Karakter Encoding Raporu ===")
    print(f"Toplam Test: {report['total_tests']}")
    print(f"Başarılı: {report['passed']}")
    print(f"Başarısız: {report['failed']}")
    print(
        f"Encoding Uyumluluk Yüzdesi: {report['encoding_compliance_percentage']:.1f}%"
    )
    print(f"Tam UTF-8 Uyumlu: {'Evet' if report['fully_utf8_compliant'] else 'Hayır'}")
    print(
        f"Test Edilen Türkçe Karakterler: {', '.join(report['turkish_characters_tested'])}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
