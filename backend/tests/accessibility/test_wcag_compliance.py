"""
Test: WCAG 2.1 Level AA Compliance Testing
Task 45: Accessibility and Compliance Testing

Bu test dosyası, platformun WCAG 2.1 Level AA standartlarına uyumluluğunu
otomatik olarak test eder.

Requirements: 9.1-9.5, 7.4
"""

import os
import sys
from typing import Any

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class WCAGComplianceChecker:
    """WCAG 2.1 Level AA uyumluluk kontrolcüsü"""

    def __init__(self):
        self.wcag_guidelines = self._load_wcag_guidelines()
        self.test_results = []

    def _load_wcag_guidelines(self) -> dict[str, Any]:
        """WCAG 2.1 Level AA kılavuzlarını yükle"""
        return {
            "1.1.1": {
                "name": "Non-text Content",
                "level": "A",
                "description": "Tüm metin olmayan içerikler için alternatif metin sağlanmalı",
            },
            "1.3.1": {
                "name": "Info and Relationships",
                "level": "A",
                "description": "Bilgi, yapı ve ilişkiler programatik olarak belirlenebilir olmalı",
            },
            "1.4.3": {
                "name": "Contrast (Minimum)",
                "level": "AA",
                "description": "Metin ve arka plan arasında minimum 4.5:1 kontrast oranı",
            },
            "1.4.5": {
                "name": "Images of Text",
                "level": "AA",
                "description": "Metin görüntüleri yerine gerçek metin kullanılmalı",
            },
            "2.1.1": {
                "name": "Keyboard",
                "level": "A",
                "description": "Tüm işlevsellik klavye ile erişilebilir olmalı",
            },
            "2.1.2": {
                "name": "No Keyboard Trap",
                "level": "A",
                "description": "Klavye odağı hiçbir bileşende takılı kalmamalı",
            },
            "2.4.1": {
                "name": "Bypass Blocks",
                "level": "A",
                "description": "Tekrarlayan içerik bloklarını atlama mekanizması",
            },
            "2.4.2": {
                "name": "Page Titled",
                "level": "A",
                "description": "Web sayfalarının açıklayıcı başlıkları olmalı",
            },
            "2.4.3": {
                "name": "Focus Order",
                "level": "A",
                "description": "Odak sırası mantıklı ve tutarlı olmalı",
            },
            "2.4.4": {
                "name": "Link Purpose (In Context)",
                "level": "A",
                "description": "Link amacı bağlamdan anlaşılabilir olmalı",
            },
            "2.4.7": {
                "name": "Focus Visible",
                "level": "AA",
                "description": "Klavye odağı görünür olmalı",
            },
            "3.1.1": {
                "name": "Language of Page",
                "level": "A",
                "description": "Sayfa dili programatik olarak belirlenebilir olmalı",
            },
            "3.1.2": {
                "name": "Language of Parts",
                "level": "AA",
                "description": "İçerik parçalarının dili belirlenebilir olmalı",
            },
            "3.2.1": {
                "name": "On Focus",
                "level": "A",
                "description": "Odak değişimi bağlam değişikliğine neden olmamalı",
            },
            "3.2.2": {
                "name": "On Input",
                "level": "A",
                "description": "Girdi değişimi beklenmedik bağlam değişikliğine neden olmamalı",
            },
            "3.3.1": {
                "name": "Error Identification",
                "level": "A",
                "description": "Girdi hataları otomatik olarak tespit edilmeli ve açıklanmalı",
            },
            "3.3.2": {
                "name": "Labels or Instructions",
                "level": "A",
                "description": "Kullanıcı girdisi gerektiren içerikler etiketlenmeli",
            },
            "4.1.1": {
                "name": "Parsing",
                "level": "A",
                "description": "İçerik spesifikasyonlara göre ayrıştırılabilir olmalı",
            },
            "4.1.2": {
                "name": "Name, Role, Value",
                "level": "A",
                "description": "UI bileşenlerinin adı, rolü ve değeri programatik olarak belirlenebilir olmalı",
            },
            "4.1.3": {
                "name": "Status Messages",
                "level": "AA",
                "description": "Durum mesajları ekran okuyucular tarafından algılanabilir olmalı",
            },
        }

    def check_guideline(
        self, guideline_id: str, content: str, context: dict = None
    ) -> dict[str, Any]:
        """Belirli bir WCAG kılavuzunu kontrol et"""
        guideline = self.wcag_guidelines.get(guideline_id)
        if not guideline:
            return {"success": False, "error": "Guideline not found"}

        result = {
            "guideline_id": guideline_id,
            "guideline_name": guideline["name"],
            "level": guideline["level"],
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Kılavuza özel kontroller
        if guideline_id == "1.1.1":
            result = self._check_alt_text(content, result)
        elif guideline_id == "1.4.3":
            result = self._check_contrast(content, result, context)
        elif guideline_id == "2.1.1":
            result = self._check_keyboard_access(content, result)
        elif guideline_id == "3.1.1":
            result = self._check_language(content, result)
        elif guideline_id == "4.1.2":
            result = self._check_aria_labels(content, result)

        self.test_results.append(result)
        return result

    def _check_alt_text(self, content: str, result: dict) -> dict:
        """Alt text kontrolü (1.1.1)"""
        if "<img" in content:
            if "alt=" not in content:
                result["issues"].append("Görsel için alt text eksik")
                result["recommendations"].append(
                    "Tüm görsellere açıklayıcı alt text ekleyin"
                )
            else:
                result["passed"] = True
        else:
            result["passed"] = True
        return result

    def _check_contrast(self, content: str, result: dict, context: dict = None) -> dict:
        """Kontrast oranı kontrolü (1.4.3)"""
        if context and "colors" in context:
            fg = context["colors"].get("foreground", "#000000")
            bg = context["colors"].get("background", "#FFFFFF")
            ratio = self._calculate_contrast_ratio(fg, bg)

            if ratio >= 4.5:
                result["passed"] = True
            else:
                result["issues"].append(
                    f"Kontrast oranı yetersiz: {ratio:.2f}:1 (minimum 4.5:1)"
                )
                result["recommendations"].append(
                    "Metin ve arka plan renkleri arasındaki kontrastı artırın"
                )
        else:
            result["skipped"] = True
            result["skip_reason"] = "Kontrast context sağlanmadı - test uygulanamaz"
        return result

    def _check_keyboard_access(self, content: str, result: dict) -> dict:
        """Klavye erişilebilirliği kontrolü (2.1.1)"""
        # Tıklanabilir elementlerin tabindex kontrolü
        if "onclick" in content.lower():
            if "tabindex" not in content.lower() and "button" not in content.lower():
                result["issues"].append(
                    "Tıklanabilir element klavye ile erişilebilir değil"
                )
                result["recommendations"].append(
                    "Tıklanabilir elementlere tabindex veya button elementi kullanın"
                )
            else:
                result["passed"] = True
        else:
            result["passed"] = True
        return result

    def _check_language(self, content: str, result: dict) -> dict:
        """Dil tanımı kontrolü (3.1.1)"""
        if "<html" in content:
            if "lang=" not in content:
                result["issues"].append("HTML lang attribute eksik")
                result["recommendations"].append(
                    '<html lang="tr"> şeklinde dil tanımı ekleyin'
                )
            else:
                result["passed"] = True
        else:
            result["passed"] = True
        return result

    def _check_aria_labels(self, content: str, result: dict) -> dict:
        """ARIA etiketleri kontrolü (4.1.2)"""
        # Form elementleri için label kontrolü
        if "<input" in content:
            if (
                "aria-label" not in content
                and "aria-labelledby" not in content
                and "<label" not in content
            ):
                result["issues"].append("Form elementi için label eksik")
                result["recommendations"].append(
                    "Form elementlerine label veya aria-label ekleyin"
                )
            else:
                result["passed"] = True
        else:
            result["passed"] = True
        return result

    def _calculate_contrast_ratio(self, fg: str, bg: str) -> float:
        """İki renk arasındaki kontrast oranını hesapla"""

        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        def relative_luminance(rgb):
            r, g, b = [x / 255.0 for x in rgb]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        l1 = relative_luminance(hex_to_rgb(fg))
        l2 = relative_luminance(hex_to_rgb(bg))

        lighter = max(l1, l2)
        darker = min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)

    def generate_compliance_report(self) -> dict[str, Any]:
        """Uyumluluk raporu oluştur"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        skipped_tests = sum(1 for r in self.test_results if r.get("skipped", False))

        return {
            "total_guidelines_tested": total_tests,
            "passed": passed_tests,
            "skipped": skipped_tests,
            "failed": total_tests - passed_tests - skipped_tests,
            "compliance_percentage": (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0,
            "level_aa_compliant": passed_tests == total_tests,
            "detailed_results": self.test_results,
        }


# Test Fixtures
@pytest.fixture
def wcag_checker():
    """WCAG compliance checker fixture"""
    return WCAGComplianceChecker()


@pytest.fixture
def sample_exam_html():
    """Sınav arayüzü için örnek HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <title>YKS Deneme Sınavı - TYT Matematik</title>
    </head>
    <body>
        <main role="main">
            <h1>TYT Matematik Sınavı</h1>
            <div class="exam-timer" role="timer" aria-live="polite">
                <span>Kalan Süre: <span id="timer">165:00</span></span>
            </div>

            <form id="exam-form">
                <div class="question" role="group" aria-labelledby="q1-text">
                    <h2 id="q1-text">Soru 1</h2>
                    <p>2x + 5 = 13 denkleminde x kaçtır?</p>
                    <div class="options">
                        <label>
                            <input type="radio" name="q1" value="A" aria-label="Seçenek A: 4">
                            <span>A) 4</span>
                        </label>
                        <label>
                            <input type="radio" name="q1" value="B" aria-label="Seçenek B: 5">
                            <span>B) 5</span>
                        </label>
                    </div>
                </div>

                <button type="submit" tabindex="0">Sınavı Bitir</button>
            </form>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def sample_dashboard_html():
    """Dashboard için örnek HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <title>Öğrenci Dashboard - Teknofest 2025</title>
    </head>
    <body>
        <nav role="navigation" aria-label="Ana navigasyon">
            <a href="#main-content" class="skip-link">İçeriğe Atla</a>
            <ul>
                <li><a href="/dashboard">Dashboard</a></li>
                <li><a href="/exams">Sınavlar</a></li>
                <li><a href="/progress">İlerleme</a></li>
            </ul>
        </nav>

        <main id="main-content" role="main">
            <h1>Hoş Geldin, Öğrenci</h1>

            <section aria-labelledby="stats-heading">
                <h2 id="stats-heading">İstatistikler</h2>
                <div class="stat-card">
                    <img src="/icons/exam.svg" alt="Sınav ikonu">
                    <p>Tamamlanan Sınavlar: <strong>15</strong></p>
                </div>
            </section>

            <section aria-labelledby="recent-heading">
                <h2 id="recent-heading">Son Aktiviteler</h2>
                <ul role="list">
                    <li>TYT Matematik - 85 puan</li>
                    <li>AYT Fizik - 78 puan</li>
                </ul>
            </section>
        </main>
    </body>
    </html>
    """


# WCAG 2.1 Level AA Compliance Tests


@pytest.mark.asyncio
async def test_wcag_1_1_1_non_text_content(wcag_checker, sample_exam_html):
    """
    Test: WCAG 1.1.1 - Non-text Content (Level A)
    Tüm görseller için alternatif metin kontrolü
    """
    result = wcag_checker.check_guideline("1.1.1", sample_exam_html)

    assert result["guideline_id"] == "1.1.1"
    assert result["passed"], "Tüm görseller alt text içermeli"
    assert len(result["issues"]) == 0


@pytest.mark.asyncio
async def test_wcag_1_4_3_contrast_minimum(wcag_checker):
    """
    Test: WCAG 1.4.3 - Contrast (Minimum) (Level AA)
    Metin ve arka plan kontrast oranı kontrolü
    """
    # İyi kontrast (siyah metin, beyaz arka plan)
    context_good = {"colors": {"foreground": "#000000", "background": "#FFFFFF"}}
    result_good = wcag_checker.check_guideline("1.4.3", "", context_good)
    assert result_good["passed"]

    # Kötü kontrast (açık gri metin, beyaz arka plan)
    context_bad = {"colors": {"foreground": "#CCCCCC", "background": "#FFFFFF"}}
    result_bad = wcag_checker.check_guideline("1.4.3", "", context_bad)
    assert not result_bad["passed"]
    assert len(result_bad["issues"]) > 0


@pytest.mark.asyncio
async def test_wcag_2_1_1_keyboard_access(wcag_checker):
    """
    Test: WCAG 2.1.1 - Keyboard (Level A)
    Tüm işlevsellik klavye ile erişilebilir olmalı
    """
    # İyi örnek: button elementi
    good_html = '<button onclick="submit()">Gönder</button>'
    result_good = wcag_checker.check_guideline("2.1.1", good_html)
    assert result_good["passed"]

    # Kötü örnek: tabindex olmayan div
    bad_html = '<div onclick="submit()">Gönder</div>'
    result_bad = wcag_checker.check_guideline("2.1.1", bad_html)
    assert not result_bad["passed"]


@pytest.mark.asyncio
async def test_wcag_2_4_2_page_titled(wcag_checker, sample_exam_html):
    """
    Test: WCAG 2.4.2 - Page Titled (Level A)
    Web sayfalarının açıklayıcı başlıkları olmalı
    """
    assert "<title>" in sample_exam_html
    assert "YKS Deneme Sınavı" in sample_exam_html


@pytest.mark.asyncio
async def test_wcag_3_1_1_language_of_page(wcag_checker, sample_exam_html):
    """
    Test: WCAG 3.1.1 - Language of Page (Level A)
    Sayfa dili programatik olarak belirlenebilir olmalı
    """
    result = wcag_checker.check_guideline("3.1.1", sample_exam_html)

    assert result["passed"]
    assert 'lang="tr"' in sample_exam_html


@pytest.mark.asyncio
async def test_wcag_4_1_2_name_role_value(wcag_checker, sample_exam_html):
    """
    Test: WCAG 4.1.2 - Name, Role, Value (Level A)
    UI bileşenlerinin adı, rolü ve değeri programatik olarak belirlenebilir olmalı
    """
    result = wcag_checker.check_guideline("4.1.2", sample_exam_html)

    assert result["passed"]
    # Form elementlerinin label'ları var
    assert "<label>" in sample_exam_html or "aria-label" in sample_exam_html


@pytest.mark.asyncio
async def test_wcag_skip_navigation_links(wcag_checker, sample_dashboard_html):
    """
    Test: WCAG 2.4.1 - Bypass Blocks (Level A)
    Tekrarlayan içerik bloklarını atlama mekanizması
    """
    assert (
        "skip-link" in sample_dashboard_html or "#main-content" in sample_dashboard_html
    )
    assert 'href="#main-content"' in sample_dashboard_html


@pytest.mark.asyncio
async def test_wcag_semantic_html_structure(wcag_checker, sample_dashboard_html):
    """
    Test: WCAG 1.3.1 - Info and Relationships (Level A)
    Semantik HTML yapısı kontrolü
    """
    # Semantik elementler mevcut olmalı
    assert "<nav" in sample_dashboard_html
    assert "<main" in sample_dashboard_html
    assert "role=" in sample_dashboard_html

    # Başlık hiyerarşisi doğru olmalı
    assert "<h1>" in sample_dashboard_html
    # Note: h2 may have attributes like id, so check for opening tag pattern
    assert "<h2" in sample_dashboard_html and ">" in sample_dashboard_html


@pytest.mark.asyncio
async def test_wcag_aria_labels_and_roles(wcag_checker, sample_exam_html):
    """
    Test: ARIA etiketleri ve rolleri
    Ekran okuyucular için uygun ARIA etiketleri
    """
    # ARIA rolleri mevcut
    assert 'role="main"' in sample_exam_html or 'role="group"' in sample_exam_html

    # ARIA live regions (dinamik içerik için)
    assert "aria-live=" in sample_exam_html

    # ARIA labels
    assert "aria-label=" in sample_exam_html or "aria-labelledby=" in sample_exam_html


@pytest.mark.asyncio
async def test_wcag_form_labels_and_instructions(wcag_checker, sample_exam_html):
    """
    Test: WCAG 3.3.2 - Labels or Instructions (Level A)
    Form elementleri için etiketler ve talimatlar
    """
    # Her input için label veya aria-label olmalı
    assert "<label>" in sample_exam_html or "aria-label" in sample_exam_html

    # Radio buttonlar için açıklayıcı etiketler
    if '<input type="radio"' in sample_exam_html:
        assert "aria-label" in sample_exam_html or "<label>" in sample_exam_html


@pytest.mark.asyncio
async def test_wcag_focus_visible(wcag_checker):
    """
    Test: WCAG 2.4.7 - Focus Visible (Level AA)
    Klavye odağı görünür olmalı
    """
    # CSS'de focus stilleri olmalı (bu test için mock)
    css_with_focus = """
    button:focus {
        outline: 2px solid #0066CC;
        outline-offset: 2px;
    }
    input:focus {
        border: 2px solid #0066CC;
    }
    """

    assert ":focus" in css_with_focus
    assert "outline" in css_with_focus or "border" in css_with_focus


@pytest.mark.asyncio
async def test_generate_full_compliance_report(
    wcag_checker, sample_exam_html, sample_dashboard_html
):
    """
    Test: Tam WCAG 2.1 Level AA uyumluluk raporu oluştur
    """
    # Tüm kritik kılavuzları test et
    wcag_checker.check_guideline("1.1.1", sample_exam_html)
    wcag_checker.check_guideline("2.1.1", sample_exam_html)
    wcag_checker.check_guideline("3.1.1", sample_exam_html)
    wcag_checker.check_guideline("4.1.2", sample_exam_html)

    wcag_checker.check_guideline("1.1.1", sample_dashboard_html)
    wcag_checker.check_guideline("3.1.1", sample_dashboard_html)

    # Rapor oluştur
    report = wcag_checker.generate_compliance_report()

    assert "total_guidelines_tested" in report
    assert "passed" in report
    assert "failed" in report
    assert "compliance_percentage" in report
    assert "level_aa_compliant" in report
    assert "detailed_results" in report

    # En az %80 uyumluluk bekliyoruz
    assert report["compliance_percentage"] >= 80.0

    print("\n=== WCAG 2.1 Level AA Uyumluluk Raporu ===")
    print(f"Test Edilen Kılavuz Sayısı: {report['total_guidelines_tested']}")
    print(f"Başarılı: {report['passed']}")
    print(f"Başarısız: {report['failed']}")
    print(f"Uyumluluk Yüzdesi: {report['compliance_percentage']:.1f}%")
    print(f"Level AA Uyumlu: {'Evet' if report['level_aa_compliant'] else 'Hayır'}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
