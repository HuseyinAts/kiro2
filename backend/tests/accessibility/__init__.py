"""
Accessibility and Compliance Testing Suite
Task 45: Accessibility and Compliance Testing

Bu paket, platformun erişilebilirlik ve uyumluluk testlerini içerir.

Test Modülleri:
- test_wcag_compliance.py: WCAG 2.1 Level AA uyumluluk testleri
- test_screen_reader_compatibility.py: Ekran okuyucu uyumluluk testleri
- test_keyboard_navigation.py: Klavye navigasyon testleri
- test_turkish_encoding.py: Türkçe karakter encoding testleri

Requirements: 9.1-9.5, 7.4
"""

__version__ = "1.0.0"
__all__ = [
    "WCAGComplianceChecker",
    "ScreenReaderCompatibilityTester",
    "KeyboardNavigationTester",
    "TurkishEncodingValidator",
]
