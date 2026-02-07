"""
Test: Keyboard Navigation Testing
Task 45: Accessibility and Compliance Testing

Bu test dosyası, sınav arayüzü ve diğer bileşenlerin klavye ile
tam erişilebilirliğini test eder.

Requirements: 9.1, 9.2, 2.1.1, 2.1.2
"""

import os
import sys
import pytest
from typing import Dict, Any
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class KeyboardNavigationTester:
    """Klavye navigasyon test aracı"""

    def __init__(self):
        self.test_results = []
        self.keyboard_shortcuts = {
            "Tab": "Sonraki elemente geç",
            "Shift+Tab": "Önceki elemente geç",
            "Enter": "Aktif elementi etkinleştir",
            "Space": "Checkbox/radio seç, button etkinleştir",
            "Arrow Keys": "Radio group, dropdown navigasyonu",
            "Escape": "Modal/dialog kapat",
            "Home": "İlk elemente git",
            "End": "Son elemente git",
        }

    def test_tab_order(self, html_content: str) -> Dict[str, Any]:
        """Tab sırası testi - Mantıklı ve tutarlı odak sırası"""
        result = {
            "test_name": "Tab Order",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Tüm focusable elementleri bul
        focusable_patterns = [
            r"<a\s+[^>]*href",
            r"<button[^>]*>",
            r"<input[^>]*>",
            r"<select[^>]*>",
            r"<textarea[^>]*>",
            r'\btabindex\s*=\s*["\']?[0-9]',
        ]

        focusable_elements = []
        for pattern in focusable_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            focusable_elements.extend(matches)

        if not focusable_elements:
            result["issues"].append("Focusable element bulunamadı")
            result["recommendations"].append("Sayfaya interaktif elementler ekleyin")
        else:
            # Negatif tabindex kontrolü (tabindex="-1" hariç)
            negative_tabindex = re.findall(r'tabindex\s*=\s*["\']?-[2-9]', html_content)
            if negative_tabindex:
                result["issues"].append(
                    f"{len(negative_tabindex)} element negatif tabindex içeriyor"
                )
                result["recommendations"].append(
                    "Negatif tabindex kullanmaktan kaçının (tabindex='-1' hariç)"
                )

            # Çok yüksek tabindex kontrolü
            high_tabindex = re.findall(
                r'tabindex\s*=\s*["\']?[1-9][0-9]{2,}', html_content
            )
            if high_tabindex:
                result["issues"].append("Çok yüksek tabindex değerleri bulundu")
                result["recommendations"].append(
                    "Tabindex değerlerini düşük tutun veya DOM sırasını kullanın"
                )

            if not result["issues"]:
                result["passed"] = True

        self.test_results.append(result)
        return result

    def test_keyboard_trap(self, html_content: str) -> Dict[str, Any]:
        """Klavye tuzağı testi - WCAG 2.1.2"""
        result = {
            "test_name": "No Keyboard Trap",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Modal/dialog kontrolü
        if "modal" in html_content.lower() or "dialog" in html_content.lower():
            # Escape tuşu ile kapatma kontrolü
            if (
                "escape" not in html_content.lower()
                and "esc" not in html_content.lower()
            ):
                result["issues"].append("Modal/dialog Escape tuşu ile kapatılamıyor")
                result["recommendations"].append(
                    "Modal'lara Escape tuşu ile kapatma özelliği ekleyin"
                )

            # Focus trap kontrolü (modal içinde odak kalmalı)
            if (
                "focus-trap" not in html_content.lower()
                and "data-focus" not in html_content.lower()
            ):
                result["issues"].append("Modal focus trap içermiyor")
                result["recommendations"].append(
                    "Modal açıkken odağı modal içinde tutun"
                )

        # Autocomplete/dropdown kontrolü
        if "autocomplete" in html_content.lower() or "dropdown" in html_content.lower():
            if "aria-expanded" not in html_content:
                result["issues"].append("Dropdown aria-expanded attribute içermiyor")
                result["recommendations"].append("Dropdown'lara aria-expanded ekleyin")

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_focus_indicators(self, css_content: str) -> Dict[str, Any]:
        """Odak göstergeleri testi - WCAG 2.4.7"""
        result = {
            "test_name": "Focus Indicators",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # :focus pseudo-class kontrolü
        if ":focus" not in css_content:
            result["issues"].append("CSS'de :focus stilleri bulunamadı")
            result["recommendations"].append(
                "Tüm interaktif elementler için :focus stilleri ekleyin"
            )
        else:
            # outline: none kontrolü (kötü pratik)
            if (
                "outline:none" in css_content.replace(" ", "")
                or "outline: none" in css_content
            ):
                if "outline:" not in css_content or "border:" not in css_content:
                    result["issues"].append(
                        "outline: none kullanılmış ama alternatif odak göstergesi yok"
                    )
                    result["recommendations"].append(
                        "outline: none kullanıyorsanız alternatif odak göstergesi ekleyin"
                    )

            # Yeterli kontrast kontrolü (basit kontrol)
            if "outline" in css_content or "border" in css_content:
                result["passed"] = True

        if not result["issues"] and ":focus" in css_content:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_skip_links(self, html_content: str) -> Dict[str, Any]:
        """İçeriğe atla linkleri testi - WCAG 2.4.1"""
        result = {
            "test_name": "Skip Links",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Skip link kontrolü
        skip_patterns = [
            r'href\s*=\s*["\']#main',
            r'href\s*=\s*["\']#content',
            r"skip.*link",
            r"içeriğe.*atla",
        ]

        has_skip_link = any(
            re.search(pattern, html_content, re.IGNORECASE) for pattern in skip_patterns
        )

        if not has_skip_link:
            result["issues"].append("İçeriğe atla linki bulunamadı")
            result["recommendations"].append(
                "Sayfanın başına 'İçeriğe Atla' linki ekleyin"
            )
        else:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_interactive_elements_keyboard_accessible(
        self, html_content: str
    ) -> Dict[str, Any]:
        """İnteraktif elementlerin klavye erişilebilirliği"""
        result = {
            "test_name": "Interactive Elements Keyboard Accessible",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # onclick ile div/span kullanımı (kötü pratik)
        onclick_divs = re.findall(
            r"<div[^>]*onclick[^>]*>", html_content, re.IGNORECASE
        )
        onclick_spans = re.findall(
            r"<span[^>]*onclick[^>]*>", html_content, re.IGNORECASE
        )

        problematic_elements = onclick_divs + onclick_spans

        if problematic_elements:
            # Tabindex veya role kontrolü
            accessible_count = 0
            for elem in problematic_elements:
                if "tabindex" in elem or 'role="button"' in elem:
                    accessible_count += 1

            if accessible_count < len(problematic_elements):
                result["issues"].append(
                    f"{len(problematic_elements) - accessible_count} tıklanabilir div/span klavye ile erişilebilir değil"
                )
                result["recommendations"].append(
                    "Tıklanabilir elementler için <button> kullanın veya tabindex ve role ekleyin"
                )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_form_keyboard_navigation(self, html_content: str) -> Dict[str, Any]:
        """Form klavye navigasyonu testi"""
        result = {
            "test_name": "Form Keyboard Navigation",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        if "<form" in html_content:
            # Radio button grupları için arrow key navigasyonu
            if '<input type="radio"' in html_content:
                # Radio buttonlar aynı name attribute'a sahip olmalı
                radio_names = re.findall(
                    r'<input[^>]*type\s*=\s*["\']radio["\'][^>]*name\s*=\s*["\']([^"\']+)',
                    html_content,
                )
                if not radio_names:
                    result["issues"].append("Radio buttonlar name attribute içermiyor")
                    result["recommendations"].append(
                        "Radio button gruplarına name attribute ekleyin"
                    )

            # Submit button kontrolü
            if "submit" not in html_content.lower():
                result["issues"].append("Form submit button içermiyor")
                result["recommendations"].append("Forma submit button ekleyin")

            # Fieldset ve legend kontrolü (soru grupları için)
            if "soru" in html_content.lower() or "question" in html_content.lower():
                if "<fieldset>" not in html_content:
                    result["issues"].append("Soru grupları fieldset içermiyor")
                    result["recommendations"].append(
                        "Soru gruplarını fieldset ve legend ile yapılandırın"
                    )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_modal_keyboard_interaction(self, html_content: str) -> Dict[str, Any]:
        """Modal klavye etkileşimi testi"""
        result = {
            "test_name": "Modal Keyboard Interaction",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        if "modal" in html_content.lower() or "dialog" in html_content.lower():
            # role="dialog" kontrolü
            if 'role="dialog"' not in html_content:
                result["issues"].append("Modal role='dialog' içermiyor")
                result["recommendations"].append("Modal'lara role='dialog' ekleyin")

            # aria-modal kontrolü
            if "aria-modal" not in html_content:
                result["issues"].append("Modal aria-modal attribute içermiyor")
                result["recommendations"].append("Modal'lara aria-modal='true' ekleyin")

            # Kapatma butonu kontrolü
            close_button_patterns = [r"close", r"kapat", r"×", r"&times;"]
            has_close_button = any(
                re.search(pattern, html_content, re.IGNORECASE)
                for pattern in close_button_patterns
            )

            if not has_close_button:
                result["issues"].append("Modal kapatma butonu içermiyor")
                result["recommendations"].append(
                    "Modal'a klavye ile erişilebilir kapatma butonu ekleyin"
                )
        else:
            result["skipped"] = True
            result["skip_reason"] = "Modal element bulunamadı - test uygulanamaz"

        if not result["issues"] and not result.get("skipped"):
            result["passed"] = True

        self.test_results.append(result)
        return result

    def test_custom_controls_keyboard_support(
        self, html_content: str
    ) -> Dict[str, Any]:
        """Özel kontrollerin klavye desteği testi"""
        result = {
            "test_name": "Custom Controls Keyboard Support",
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Özel slider/range kontrolü
        if "slider" in html_content.lower() or "range" in html_content.lower():
            if 'role="slider"' not in html_content:
                result["issues"].append("Özel slider role='slider' içermiyor")
                result["recommendations"].append(
                    "Özel slider'lara role='slider' ve arrow key desteği ekleyin"
                )

        # Özel dropdown/combobox kontrolü
        if (
            "combobox" in html_content.lower()
            or "custom-select" in html_content.lower()
        ):
            if 'role="combobox"' not in html_content:
                result["issues"].append("Özel dropdown role='combobox' içermiyor")
                result["recommendations"].append(
                    "Özel dropdown'lara role='combobox' ve klavye desteği ekleyin"
                )

        # Tab panel kontrolü
        if "tab" in html_content.lower() and "panel" in html_content.lower():
            if 'role="tablist"' not in html_content:
                result["issues"].append("Tab interface ARIA rolleri içermiyor")
                result["recommendations"].append(
                    "Tab interface'e role='tablist', role='tab', role='tabpanel' ekleyin"
                )

        if not result["issues"]:
            result["passed"] = True

        self.test_results.append(result)
        return result

    def generate_keyboard_navigation_report(self) -> Dict[str, Any]:
        """Klavye navigasyon raporu oluştur"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        skipped_tests = sum(1 for r in self.test_results if r.get("skipped", False))

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "skipped": skipped_tests,
            "failed": total_tests - passed_tests - skipped_tests,
            "keyboard_accessible_percentage": (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0,
            "fully_keyboard_accessible": passed_tests == total_tests,
            "supported_shortcuts": self.keyboard_shortcuts,
            "detailed_results": self.test_results,
        }


# Test Fixtures
@pytest.fixture
def kb_tester():
    """Keyboard navigation tester fixture"""
    return KeyboardNavigationTester()


@pytest.fixture
def exam_interface_html():
    """Sınav arayüzü HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <title>TYT Matematik Sınavı</title>
        <style>
            button:focus, input:focus, a:focus {
                outline: 2px solid #0066CC;
                outline-offset: 2px;
            }
            .skip-link:focus {
                position: absolute;
                top: 0;
                left: 0;
                background: #000;
                color: #fff;
                padding: 10px;
            }
        </style>
    </head>
    <body>
        <a href="#main-content" class="skip-link">İçeriğe Atla</a>

        <nav role="navigation">
            <button type="button" aria-label="Menü">☰</button>
        </nav>

        <main id="main-content" role="main">
            <h1>TYT Matematik Sınavı</h1>

            <form id="exam-form">
                <fieldset>
                    <legend>Soru 1: 2x + 5 = 13 denkleminde x kaçtır?</legend>

                    <label>
                        <input type="radio" name="q1" value="A" tabindex="0">
                        <span>A) 4</span>
                    </label>

                    <label>
                        <input type="radio" name="q1" value="B" tabindex="0">
                        <span>B) 5</span>
                    </label>

                    <label>
                        <input type="radio" name="q1" value="C" tabindex="0">
                        <span>C) 6</span>
                    </label>
                </fieldset>

                <div class="navigation-buttons">
                    <button type="button" tabindex="0">Önceki Soru</button>
                    <button type="button" tabindex="0">Sonraki Soru</button>
                    <button type="submit" tabindex="0">Sınavı Bitir</button>
                </div>
            </form>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def modal_dialog_html():
    """Modal dialog HTML - WCAG 2.1.2 compliant with focus-trap and escape key support"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <body>
        <button id="open-modal" type="button">Sonuçları Gör</button>

        <!-- Modal with focus-trap and escape key support (WCAG 2.1.2) -->
        <div id="results-modal"
             role="dialog"
             aria-modal="true"
             aria-labelledby="modal-title"
             data-focus-trap="true"
             data-escape-close="true">
            <h2 id="modal-title">Sınav Sonuçları</h2>

            <div class="modal-content">
                <p>Toplam Puan: 85</p>
                <p>Doğru: 32</p>
                <p>Yanlış: 4</p>
            </div>

            <div class="modal-actions">
                <button type="button" tabindex="0">Detaylı Rapor</button>
                <button type="button"
                        class="close-modal"
                        tabindex="0"
                        aria-label="Kapat (Escape)"
                        data-key="escape">×</button>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def custom_controls_html():
    """Özel kontroller HTML"""
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <body>
        <div class="difficulty-slider">
            <label id="slider-label">Zorluk Seviyesi</label>
            <div role="slider"
                 aria-labelledby="slider-label"
                 aria-valuemin="1"
                 aria-valuemax="10"
                 aria-valuenow="5"
                 tabindex="0">
                <div class="slider-track"></div>
                <div class="slider-thumb"></div>
            </div>
        </div>

        <div class="subject-tabs">
            <div role="tablist" aria-label="Ders Seçimi">
                <button role="tab" aria-selected="true" aria-controls="math-panel" tabindex="0">
                    Matematik
                </button>
                <button role="tab" aria-selected="false" aria-controls="physics-panel" tabindex="-1">
                    Fizik
                </button>
            </div>

            <div role="tabpanel" id="math-panel" aria-labelledby="math-tab">
                <p>Matematik içeriği</p>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_css():
    """Örnek CSS"""
    return """
    /* Focus indicators */
    button:focus {
        outline: 2px solid #0066CC;
        outline-offset: 2px;
    }

    input:focus {
        border: 2px solid #0066CC;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.2);
    }

    a:focus {
        outline: 2px dashed #0066CC;
        outline-offset: 4px;
    }

    .skip-link {
        position: absolute;
        left: -9999px;
    }

    .skip-link:focus {
        position: absolute;
        top: 0;
        left: 0;
        z-index: 9999;
    }
    """


# Keyboard Navigation Tests


@pytest.mark.asyncio
async def test_tab_order_logical(kb_tester, exam_interface_html):
    """
    Test: Tab sırası mantıklı ve tutarlı
    WCAG 2.4.3 - Focus Order
    """
    result = kb_tester.test_tab_order(exam_interface_html)

    assert result["passed"], "Tab sırası mantıklı olmalı"
    assert len(result["issues"]) == 0


@pytest.mark.asyncio
async def test_no_keyboard_trap(kb_tester, modal_dialog_html):
    """
    Test: Klavye tuzağı yok
    WCAG 2.1.2 - No Keyboard Trap
    """
    result = kb_tester.test_keyboard_trap(modal_dialog_html)

    assert result["passed"], "Klavye odağı hiçbir yerde takılı kalmamalı"


@pytest.mark.asyncio
async def test_focus_indicators_visible(kb_tester, sample_css):
    """
    Test: Odak göstergeleri görünür
    WCAG 2.4.7 - Focus Visible
    """
    result = kb_tester.test_focus_indicators(sample_css)

    assert (
        result["passed"]
    ), "Tüm interaktif elementler odak göstergesi içermeli"
    assert ":focus" in sample_css


@pytest.mark.asyncio
async def test_skip_links_present(kb_tester, exam_interface_html):
    """
    Test: İçeriğe atla linkleri mevcut
    WCAG 2.4.1 - Bypass Blocks
    """
    result = kb_tester.test_skip_links(exam_interface_html)

    assert result["passed"], "İçeriğe atla linki olmalı"
    assert "İçeriğe Atla" in exam_interface_html


@pytest.mark.asyncio
async def test_interactive_elements_accessible(kb_tester, exam_interface_html):
    """
    Test: İnteraktif elementler klavye ile erişilebilir
    WCAG 2.1.1 - Keyboard
    """
    result = kb_tester.test_interactive_elements_keyboard_accessible(
        exam_interface_html
    )

    assert (
        result["passed"]
    ), "Tüm interaktif elementler klavye ile erişilebilir olmalı"


@pytest.mark.asyncio
async def test_form_keyboard_navigation(kb_tester, exam_interface_html):
    """
    Test: Form klavye navigasyonu
    Radio buttonlar arrow key ile navigasyon yapılabilmeli
    """
    result = kb_tester.test_form_keyboard_navigation(exam_interface_html)

    assert (
        result["passed"]
    ), "Form elementleri klavye ile navigasyon yapılabilir olmalı"
    assert '<input type="radio"' in exam_interface_html
    assert 'name="q1"' in exam_interface_html


@pytest.mark.asyncio
async def test_modal_keyboard_interaction(kb_tester, modal_dialog_html):
    """
    Test: Modal klavye etkileşimi
    Modal açıkken odak modal içinde kalmalı, Escape ile kapatılabilmeli
    """
    result = kb_tester.test_modal_keyboard_interaction(modal_dialog_html)

    assert result["passed"], "Modal klavye ile tam erişilebilir olmalı"
    assert 'role="dialog"' in modal_dialog_html
    assert 'aria-modal="true"' in modal_dialog_html


@pytest.mark.asyncio
async def test_custom_controls_keyboard_support(kb_tester, custom_controls_html):
    """
    Test: Özel kontrollerin klavye desteği
    Slider, tabs gibi özel kontroller klavye ile kullanılabilmeli
    """
    result = kb_tester.test_custom_controls_keyboard_support(custom_controls_html)

    assert result["passed"], "Özel kontroller klavye desteği içermeli"
    assert 'role="slider"' in custom_controls_html
    assert 'role="tablist"' in custom_controls_html


@pytest.mark.asyncio
async def test_button_elements_used(kb_tester, exam_interface_html):
    """
    Test: Button elementleri kullanımı
    Tıklanabilir elementler için <button> veya uygun ARIA rolleri kullanılmalı
    """
    # Button elementleri mevcut olmalı
    assert "<button" in exam_interface_html

    # onclick ile div kullanımı olmamalı
    assert not re.search(r"<div[^>]*onclick", exam_interface_html, re.IGNORECASE)


@pytest.mark.asyncio
async def test_radio_button_group_navigation(kb_tester, exam_interface_html):
    """
    Test: Radio button grup navigasyonu
    Aynı gruptaki radio buttonlar arrow key ile navigasyon yapılabilmeli
    """
    # Radio buttonlar aynı name attribute'a sahip olmalı
    radio_names = re.findall(r'name="([^"]+)"', exam_interface_html)
    assert len(set(radio_names)) > 0, "Radio buttonlar name attribute içermeli"

    # Fieldset ve legend kullanımı
    assert "<fieldset>" in exam_interface_html
    assert "<legend>" in exam_interface_html


@pytest.mark.asyncio
async def test_generate_full_keyboard_navigation_report(
    kb_tester, exam_interface_html, modal_dialog_html, custom_controls_html, sample_css
):
    """
    Test: Tam klavye navigasyon raporu
    """
    # Tüm testleri çalıştır
    kb_tester.test_tab_order(exam_interface_html)
    kb_tester.test_keyboard_trap(modal_dialog_html)
    kb_tester.test_focus_indicators(sample_css)
    kb_tester.test_skip_links(exam_interface_html)
    kb_tester.test_interactive_elements_keyboard_accessible(exam_interface_html)
    kb_tester.test_form_keyboard_navigation(exam_interface_html)
    kb_tester.test_modal_keyboard_interaction(modal_dialog_html)
    kb_tester.test_custom_controls_keyboard_support(custom_controls_html)

    # Rapor oluştur
    report = kb_tester.generate_keyboard_navigation_report()

    assert "total_tests" in report
    assert "passed" in report
    assert "keyboard_accessible_percentage" in report
    assert "fully_keyboard_accessible" in report
    assert "supported_shortcuts" in report

    # En az %90 uyumluluk bekliyoruz
    assert report["keyboard_accessible_percentage"] >= 90.0

    print("\n=== Klavye Navigasyon Raporu ===")
    print(f"Toplam Test: {report['total_tests']}")
    print(f"Başarılı: {report['passed']}")
    print(f"Başarısız: {report['failed']}")
    print(
        f"Klavye Erişilebilirlik Yüzdesi: {report['keyboard_accessible_percentage']:.1f}%"
    )
    print(
        f"Tam Klavye Erişilebilir: {'Evet' if report['fully_keyboard_accessible'] else 'Hayır'}"
    )
    print("\nDesteklenen Klavye Kısayolları:")
    for shortcut, description in report["supported_shortcuts"].items():
        print(f"  {shortcut}: {description}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
