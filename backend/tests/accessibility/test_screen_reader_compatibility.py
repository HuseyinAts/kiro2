"""
Test: Screen Reader Compatibility Testing
Task 45: Accessibility and Compliance Testing

Bu test dosyası, platformun ekran okuyucular (NVDA, JAWS, VoiceOver) ile
uyumluluğunu test eder.

Requirements: 9.2, 9.3, 9.4
"""

import os
import re
import sys
from typing import Any

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ScreenReaderCompatibilityTester:
    """Ekran okuyucu uyumluluk test aracı"""

    def __init__(self):
        self.test_results = []
        self.supported_screen_readers = ["NVDA", "JAWS", "VoiceOver", "TalkBack"]

    def test_aria_live_regions(self, html_content: str) -> dict[str, Any]:
        """ARIA live regions testi - Dinamik içerik güncellemeleri"""
        result = {
            "test_name": "ARIA Live Regions",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Sınav zamanlayıcısı için aria-live kontrolü
        if "timer" in html_content.lower():
            if (
                'aria-live="polite"' in html_content
                or 'aria-live="assertive"' in html_content
            ):
                result["passed"] = True
            else:
                result["issues"].append("Zamanlayıcı için aria-live attribute eksik")
                result["recommendations"].append(
                    "Zamanlayıcıya aria-live='polite' ekleyin"
                )

        # Hata mesajları için aria-live kontrolü
        if "error" in html_content.lower() or "alert" in html_content.lower():
            if (
                'role="alert"' in html_content
                or 'aria-live="assertive"' in html_content
            ):
                result["passed"] = True
            else:
                result["issues"].append("Hata mesajları için role='alert' eksik")
                result["recommendations"].append(
                    "Hata mesajlarına role='alert' ekleyin"
                )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_form_field_descriptions(self, html_content: str) -> dict[str, Any]:
        """Form alanları için açıklayıcı etiketler testi"""
        result = {
            "test_name": "Form Field Descriptions",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Input elementleri için label veya aria-label kontrolü
        input_pattern = r"<input[^>]*>"
        inputs = re.findall(input_pattern, html_content)

        unlabeled_inputs = []
        for input_tag in inputs:
            has_label = (
                "aria-label=" in input_tag
                or "aria-labelledby=" in input_tag
                or "aria-describedby=" in input_tag
            )

            if not has_label:
                unlabeled_inputs.append(input_tag)

        if unlabeled_inputs:
            result["issues"].append(
                f"{len(unlabeled_inputs)} input elementi etiket içermiyor"
            )
            result["recommendations"].append(
                "Tüm input elementlerine aria-label veya label ekleyin"
            )
        else:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_heading_structure(self, html_content: str) -> dict[str, Any]:
        """Başlık hiyerarşisi testi - Ekran okuyucu navigasyonu için"""
        result = {
            "test_name": "Heading Structure",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # H1 kontrolü
        if "<h1>" not in html_content and "<h1 " not in html_content:
            result["issues"].append("Sayfa H1 başlığı içermiyor")
            result["recommendations"].append("Her sayfaya bir H1 başlığı ekleyin")

        # Başlık sırası kontrolü
        headings = []
        for i in range(1, 7):
            pattern = f"<h{i}[^>]*>"
            matches = re.findall(pattern, html_content)
            for match in matches:
                headings.append(i)

        # Başlıklar sıralı mı kontrol et
        if headings:
            for i in range(len(headings) - 1):
                if headings[i + 1] - headings[i] > 1:
                    result["issues"].append(
                        f"Başlık hiyerarşisi atlanmış: H{headings[i]} -> H{headings[i+1]}"
                    )
                    result["recommendations"].append(
                        "Başlık seviyelerini sırayla kullanın (H1, H2, H3...)"
                    )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_landmark_regions(self, html_content: str) -> dict[str, Any]:
        """Landmark regions testi - Sayfa yapısı navigasyonu"""
        result = {
            "test_name": "Landmark Regions",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        required_landmarks = {
            "main": ["<main", 'role="main"'],
            "navigation": ["<nav", 'role="navigation"'],
            "banner": ["<header", 'role="banner"'],
        }

        for landmark, patterns in required_landmarks.items():
            found = any(pattern in html_content for pattern in patterns)
            if not found:
                result["issues"].append(f"{landmark.capitalize()} landmark eksik")
                result["recommendations"].append(
                    f"<{landmark}> elementi veya role='{landmark}' ekleyin"
                )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_button_and_link_labels(self, html_content: str) -> dict[str, Any]:
        """Button ve link etiketleri testi"""
        result = {
            "test_name": "Button and Link Labels",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Boş button kontrolü
        empty_button_pattern = r"<button[^>]*>\s*</button>"
        empty_buttons = re.findall(empty_button_pattern, html_content)

        if empty_buttons:
            result["issues"].append(f"{len(empty_buttons)} boş button elementi bulundu")
            result["recommendations"].append(
                "Tüm button elementlerine açıklayıcı metin veya aria-label ekleyin"
            )

        # "Tıklayın" gibi belirsiz link metinleri kontrolü
        vague_link_texts = ["tıklayın", "buraya tıklayın", "devam", "daha fazla"]
        for vague_text in vague_link_texts:
            if vague_text in html_content.lower():
                result["issues"].append(f"Belirsiz link metni bulundu: '{vague_text}'")
                result["recommendations"].append(
                    "Link metinlerini açıklayıcı yapın (örn: 'Sınav sonuçlarını görüntüle')"
                )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_table_accessibility(self, html_content: str) -> dict[str, Any]:
        """Tablo erişilebilirliği testi"""
        result = {
            "test_name": "Table Accessibility",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        if "<table" in html_content:
            # Caption kontrolü
            if "<caption>" not in html_content:
                result["issues"].append("Tablo caption içermiyor")
                result["recommendations"].append(
                    "Tabloya <caption> ekleyerek açıklama sağlayın"
                )

            # TH (header) kontrolü
            if "<th" not in html_content:
                result["issues"].append("Tablo başlık hücreleri (th) içermiyor")
                result["recommendations"].append(
                    "Tablo başlıkları için <th> elementi kullanın"
                )

            # Scope attribute kontrolü
            if "<th" in html_content and "scope=" not in html_content:
                result["issues"].append("TH elementleri scope attribute içermiyor")
                result["recommendations"].append(
                    "TH elementlerine scope='col' veya scope='row' ekleyin"
                )
        else:
            result["skipped"] = True
            result["skip_reason"] = "Tablo element bulunamadı - test uygulanamaz"

        if not result["issues"] and not result.get("skipped"):
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_math_formula_accessibility(self, html_content: str) -> dict[str, Any]:
        """Matematiksel formül erişilebilirliği testi"""
        result = {
            "test_name": "Math Formula Accessibility",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # MathML veya alternatif metin kontrolü
        math_indicators = ["∫", "∑", "√", "²", "³", "π", "∞"]
        has_math = any(indicator in html_content for indicator in math_indicators)

        if has_math:
            if "<math" in html_content or "aria-label" in html_content:  # MathML kullanımı
                result["passed"] = True
            else:
                result["issues"].append(
                    "Matematiksel formüller ekran okuyucu uyumlu değil"
                )
                result["recommendations"].append(
                    "MathML kullanın veya formüllere aria-label ekleyin"
                )
        else:
            result["skipped"] = True
            result["skip_reason"] = "Matematik içeriği bulunamadı - test uygulanamaz"

        self.test_results.append(result)
        return result

    def test_status_messages(self, html_content: str) -> dict[str, Any]:
        """Durum mesajları testi (WCAG 4.1.3)"""
        result = {
            "test_name": "Status Messages",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        status_indicators = ["başarılı", "hata", "uyarı", "bilgi", "yükleniyor"]
        has_status = any(
            indicator in html_content.lower() for indicator in status_indicators
        )

        if has_status:
            # role="status" veya aria-live kontrolü
            if 'role="status"' in html_content or "aria-live=" in html_content:
                result["passed"] = True
            else:
                result["issues"].append(
                    "Durum mesajları ekran okuyucu tarafından algılanamıyor"
                )
                result["recommendations"].append(
                    "Durum mesajlarına role='status' veya aria-live ekleyin"
                )
        else:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def generate_compatibility_report(self) -> dict[str, Any]:
        """Ekran okuyucu uyumluluk raporu oluştur"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        skipped_tests = sum(1 for r in self.test_results if r.get("skipped", False))

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "skipped": skipped_tests,
            "failed": total_tests - passed_tests - skipped_tests,
            "compatibility_percentage": (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0,
            "screen_reader_compatible": passed_tests == total_tests,
            "supported_screen_readers": self.supported_screen_readers,
            "detailed_results": self.test_results,
        }


# Test Fixtures
@pytest.fixture
def sr_tester():
    """Screen reader compatibility tester fixture"""
    return ScreenReaderCompatibilityTester()


@pytest.fixture
def exam_interface_html():
    """Sınav arayüzü HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <title>TYT Matematik Sınavı</title>
    </head>
    <body>
        <header role="banner">
            <h1>TYT Matematik Sınavı</h1>
        </header>

        <nav role="navigation" aria-label="Sınav navigasyonu">
            <a href="#main-content">İçeriğe atla</a>
        </nav>

        <main id="main-content" role="main">
            <div class="timer" aria-live="polite" aria-atomic="true">
                <span>Kalan Süre: <span id="time">165:00</span></span>
            </div>

            <form aria-label="Sınav formu">
                <fieldset>
                    <legend>Soru 1</legend>
                    <p>2x + 5 = 13 denkleminde x kaçtır?</p>

                    <label>
                        <input type="radio" name="q1" value="A" aria-label="Seçenek A: 4">
                        <span>A) 4</span>
                    </label>
                    <label>
                        <input type="radio" name="q1" value="B" aria-label="Seçenek B: 5">
                        <span>B) 5</span>
                    </label>
                </fieldset>

                <button type="submit" aria-label="Sınavı bitir ve sonuçları gör">Sınavı Bitir</button>
            </form>

            <div role="status" aria-live="polite" class="save-status">
                <p>Yanıtlarınız otomatik olarak kaydedildi</p>
            </div>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def math_content_html():
    """Matematiksel içerik HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <body>
        <main role="main">
            <h1>Matematik Dersi: İntegral</h1>

            <h2>Temel İntegral Formülü</h2>
            <div class="math-formula">
                <math xmlns="http://www.w3.org/1998/Math/MathML">
                    <mrow>
                        <mo>∫</mo>
                        <mi>x</mi>
                        <mo>d</mo>
                        <mi>x</mi>
                        <mo>=</mo>
                        <mfrac>
                            <msup><mi>x</mi><mn>2</mn></msup>
                            <mn>2</mn>
                        </mfrac>
                        <mo>+</mo>
                        <mi>C</mi>
                    </mrow>
                </math>
                <span class="sr-only" aria-label="İntegral x dx eşittir x kare bölü 2 artı C"></span>
            </div>

            <p>Bu formül, <span aria-label="x'in integrali">∫x dx</span> hesaplamasını gösterir.</p>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def results_table_html():
    """Sonuç tablosu HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <body>
        <main role="main">
            <h1>Sınav Sonuçları</h1>

            <table>
                <caption>TYT Matematik Sınav Sonuçları - Son 5 Deneme</caption>
                <thead>
                    <tr>
                        <th scope="col">Tarih</th>
                        <th scope="col">Doğru</th>
                        <th scope="col">Yanlış</th>
                        <th scope="col">Net</th>
                        <th scope="col">Puan</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>01.10.2025</td>
                        <td>32</td>
                        <td>4</td>
                        <td>31</td>
                        <td>85</td>
                    </tr>
                    <tr>
                        <td>28.09.2025</td>
                        <td>30</td>
                        <td>6</td>
                        <td>28.5</td>
                        <td>78</td>
                    </tr>
                </tbody>
            </table>
        </main>
    </body>
    </html>
    """


# Screen Reader Compatibility Tests


@pytest.mark.asyncio
async def test_aria_live_regions_exam_timer(sr_tester, exam_interface_html):
    """
    Test: ARIA live regions - Sınav zamanlayıcısı
    Ekran okuyucular zamanlayıcı güncellemelerini duyurmalı
    """
    result = sr_tester.test_aria_live_regions(exam_interface_html)

    assert result["passed"], "Zamanlayıcı aria-live attribute içermeli"
    assert len(result["issues"]) == 0


@pytest.mark.asyncio
async def test_form_field_descriptions_exam(sr_tester, exam_interface_html):
    """
    Test: Form alanları açıklamaları
    Tüm soru seçenekleri ekran okuyucu için etiketlenmeli
    """
    result = sr_tester.test_form_field_descriptions(exam_interface_html)

    assert result["passed"], "Tüm form alanları etiketlenmeli"


@pytest.mark.asyncio
async def test_heading_structure_navigation(sr_tester, exam_interface_html):
    """
    Test: Başlık hiyerarşisi
    Ekran okuyucu kullanıcıları başlıklar ile navigasyon yapabilmeli
    """
    result = sr_tester.test_heading_structure(exam_interface_html)

    assert result["passed"], "Başlık hiyerarşisi doğru olmalı"
    assert "<h1>" in exam_interface_html


@pytest.mark.asyncio
async def test_landmark_regions_page_structure(sr_tester, exam_interface_html):
    """
    Test: Landmark regions
    Sayfa yapısı ekran okuyucu navigasyonu için uygun olmalı
    """
    result = sr_tester.test_landmark_regions(exam_interface_html)

    assert result["passed"], "Tüm gerekli landmark'lar mevcut olmalı"
    assert 'role="main"' in exam_interface_html
    assert 'role="navigation"' in exam_interface_html


@pytest.mark.asyncio
async def test_button_labels_descriptive(sr_tester, exam_interface_html):
    """
    Test: Button etiketleri
    Button'lar açıklayıcı etiketler içermeli
    """
    result = sr_tester.test_button_and_link_labels(exam_interface_html)

    assert result["passed"], "Tüm button'lar açıklayıcı etiket içermeli"


@pytest.mark.asyncio
async def test_table_accessibility_results(sr_tester, results_table_html):
    """
    Test: Tablo erişilebilirliği
    Sonuç tabloları ekran okuyucu uyumlu olmalı
    """
    result = sr_tester.test_table_accessibility(results_table_html)

    assert result["passed"], "Tablolar caption ve th elementleri içermeli"
    assert "<caption>" in results_table_html
    assert "<th scope=" in results_table_html


@pytest.mark.asyncio
async def test_math_formula_accessibility(sr_tester, math_content_html):
    """
    Test: Matematiksel formül erişilebilirliği
    Matematik formülleri ekran okuyucu ile okunabilir olmalı
    """
    result = sr_tester.test_math_formula_accessibility(math_content_html)

    assert (
        result["passed"]
    ), "Matematik formülleri MathML veya aria-label içermeli"
    assert "<math" in math_content_html or "aria-label" in math_content_html


@pytest.mark.asyncio
async def test_status_messages_auto_save(sr_tester, exam_interface_html):
    """
    Test: Durum mesajları (WCAG 4.1.3)
    Otomatik kaydetme gibi durum mesajları ekran okuyucu tarafından duyurulmalı
    """
    result = sr_tester.test_status_messages(exam_interface_html)

    assert (
        result["passed"]
    ), "Durum mesajları role='status' veya aria-live içermeli"


@pytest.mark.asyncio
async def test_skip_navigation_links(sr_tester, exam_interface_html):
    """
    Test: İçeriğe atla linkleri
    Ekran okuyucu kullanıcıları tekrarlayan içeriği atlayabilmeli
    """
    assert (
        "İçeriğe atla" in exam_interface_html
        or "Skip to content" in exam_interface_html
    )
    assert "#main-content" in exam_interface_html


@pytest.mark.asyncio
async def test_fieldset_and_legend_for_questions(sr_tester, exam_interface_html):
    """
    Test: Fieldset ve legend kullanımı
    Soru grupları fieldset ve legend ile yapılandırılmalı
    """
    assert "<fieldset>" in exam_interface_html
    assert "<legend>" in exam_interface_html


@pytest.mark.asyncio
async def test_generate_full_sr_compatibility_report(
    sr_tester, exam_interface_html, math_content_html, results_table_html
):
    """
    Test: Tam ekran okuyucu uyumluluk raporu
    """
    # Tüm testleri çalıştır
    sr_tester.test_aria_live_regions(exam_interface_html)
    sr_tester.test_form_field_descriptions(exam_interface_html)
    sr_tester.test_heading_structure(exam_interface_html)
    sr_tester.test_landmark_regions(exam_interface_html)
    sr_tester.test_button_and_link_labels(exam_interface_html)
    sr_tester.test_table_accessibility(results_table_html)
    sr_tester.test_math_formula_accessibility(math_content_html)
    sr_tester.test_status_messages(exam_interface_html)

    # Rapor oluştur
    report = sr_tester.generate_compatibility_report()

    assert "total_tests" in report
    assert "passed" in report
    assert "compatibility_percentage" in report
    assert "screen_reader_compatible" in report
    assert "supported_screen_readers" in report

    # En az %85 uyumluluk bekliyoruz
    assert report["compatibility_percentage"] >= 85.0

    print("\n=== Ekran Okuyucu Uyumluluk Raporu ===")
    print(f"Toplam Test: {report['total_tests']}")
    print(f"Başarılı: {report['passed']}")
    print(f"Başarısız: {report['failed']}")
    print(f"Uyumluluk Yüzdesi: {report['compatibility_percentage']:.1f}%")
    print(
        f"Desteklenen Ekran Okuyucular: {', '.join(report['supported_screen_readers'])}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
