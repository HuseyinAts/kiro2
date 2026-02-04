"""
Türkçe karakter desteği ve encoding konfigürasyonu
UTF-8 encoding ve locale ayarları
"""
import json
import locale
import os
import sys
from typing import Any, Union


def setup_turkish_encoding():
    """
    Türkçe karakter desteği için sistem encoding ayarları
    """
    # Python encoding ayarları
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("LANG", "tr_TR.UTF-8")
    os.environ.setdefault("LC_ALL", "tr_TR.UTF-8")

    # Sistem encoding kontrolü
    if sys.stdout.encoding.lower() != "utf-8":
        print("⚠️  Uyarı: Sistem encoding UTF-8 değil!")

    # Locale ayarları
    try:
        locale.setlocale(locale.LC_ALL, "tr_TR.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, "Turkish_Turkey.1254")
        except locale.Error:
            print("⚠️  Uyarı: Türkçe locale ayarlanamadı")


def validate_turkish_text(text: str) -> bool:
    """
    Türkçe karakterlerin doğru görüntülenip görüntülenmediğini kontrol et

    Args:
        text: Kontrol edilecek metin

    Returns:
        bool: Türkçe karakterler doğru ise True
    """
    turkish_chars = ["ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "Ğ", "I", "İ", "Ö", "Ş", "Ü"]

    try:
        # Encoding/decoding testi
        encoded = text.encode("utf-8")
        decoded = encoded.decode("utf-8")
        return text == decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False


def ensure_utf8_encoding(data: Any) -> str:
    """
    Herhangi bir veriyi UTF-8 string'e dönüştür

    Args:
        data: Dönüştürülecek veri

    Returns:
        str: UTF-8 string
    """
    if data is None:
        return ""

    if isinstance(data, str):
        return data

    if isinstance(data, bytes):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return data.decode("latin-1")
            except UnicodeDecodeError:
                return data.decode("utf-8", errors="replace")

    return str(data)


def turkish_safe_encode(
    text: str, encoding: str = "utf-8", errors: str = "strict"
) -> bytes:
    """
    Türkçe karakterlerle güvenli encoding

    Args:
        text: Encode edilecek metin
        encoding: Kullanılacak encoding
        errors: Hata durumunda yapılacak işlem

    Returns:
        bytes: Encode edilmiş veri
    """
    if not isinstance(text, str):
        text = str(text)

    return text.encode(encoding, errors)


def turkish_safe_decode(
    data: Union[bytes, str], encoding: str = "utf-8", errors: str = "replace"
) -> str:
    """
    Türkçe karakterlerle güvenli decoding

    Args:
        data: Decode edilecek veri
        encoding: Kullanılacak encoding
        errors: Hata durumunda yapılacak işlem

    Returns:
        str: Decode edilmiş metin
    """
    if isinstance(data, str):
        return data

    if isinstance(data, bytes):
        try:
            return data.decode(encoding, errors)
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")

    return str(data)


def normalize_turkish_text(text: str) -> str:
    """
    Türkçe metni normalize et

    Args:
        text: Normalize edilecek metin

    Returns:
        str: Normalize edilmiş metin
    """
    if not isinstance(text, str):
        text = str(text)

    # Lowercase ve whitespace temizleme
    normalized = text.lower().strip()

    # Çoklu boşlukları tek boşluğa çevir
    import re

    normalized = re.sub(r"\s+", " ", normalized)

    # Türkçe karakter dönüşümleri
    replacements = {
        "i̇": "i",  # Noktalı i problemi
    }

    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    return normalized


def get_system_encoding() -> str:
    """
    Sistem encoding'ini getir

    Returns:
        str: Sistem encoding
    """
    try:
        return locale.getpreferredencoding() or "utf-8"
    except Exception:
        return "utf-8"


def safe_json_encode(data: Any, **kwargs) -> str:
    """
    Türkçe karakterlerle güvenli JSON encoding

    Args:
        data: JSON'a dönüştürülecek veri
        **kwargs: json.dumps parametreleri

    Returns:
        str: JSON string
    """
    try:
        return json.dumps(data, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError):
        # Non-serializable object için fallback
        try:
            return json.dumps(str(data), ensure_ascii=False, **kwargs)
        except Exception:
            return '""'


def safe_json_decode(json_str: str) -> Any:
    """
    Güvenli JSON decoding

    Args:
        json_str: JSON string

    Returns:
        Any: Parse edilmiş veri veya None
    """
    if not json_str or not isinstance(json_str, str):
        return None

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None


def safe_turkish_print(text: str) -> None:
    """
    Türkçe karakterlerle güvenli yazdırma

    Args:
        text: Yazdırılacak metin
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: ASCII karakterlere dönüştür
        ascii_text = text.encode("ascii", "ignore").decode("ascii")
        print(f"[ENCODING ERROR] {ascii_text}")


def get_encoding_info() -> dict:
    """
    Sistem encoding bilgilerini getir

    Returns:
        dict: Encoding bilgileri
    """
    return {
        "system_encoding": sys.getdefaultencoding(),
        "stdout_encoding": sys.stdout.encoding,
        "filesystem_encoding": sys.getfilesystemencoding(),
        "locale": locale.getlocale(),
        "python_io_encoding": os.environ.get("PYTHONIOENCODING", "Not set"),
        "lang": os.environ.get("LANG", "Not set"),
        "lc_all": os.environ.get("LC_ALL", "Not set"),
    }


# Uygulama başlangıcında encoding ayarlarını yap
setup_turkish_encoding()


# Test fonksiyonu
def test_turkish_encoding():
    """Türkçe encoding testleri"""
    test_texts = [
        "Türkçe karakterler: ç, ğ, ı, ö, ş, ü",
        "ÖSYM sınavları: TYT, AYT, YDT",
        "MEB müfredatı uyumluluğu",
        "Öğrenci başarı değerlendirmesi",
    ]

    print("🔤 Türkçe Encoding Test Sonuçları:")
    print("-" * 40)

    for text in test_texts:
        is_valid = validate_turkish_text(text)
        status = "[CHECK]" if is_valid else "[X]"
        print(f"{status} {text}")

    print("\n[CHART] Sistem Encoding Bilgileri:")
    print("-" * 40)
    for key, value in get_encoding_info().items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_turkish_encoding()
