"""
Accessibility Test Suite Runner
Task 45: Accessibility and Compliance Testing

Bu script, tüm erişilebilirlik testlerini çalıştırır ve kapsamlı bir rapor oluşturur.

Kullanım:
    python run_accessibility_tests.py
    python run_accessibility_tests.py --verbose
    python run_accessibility_tests.py --report-format json
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Test modüllerini import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AccessibilityTestRunner:
    """Erişilebilirlik test suite çalıştırıcı"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_modules = [
            "test_wcag_compliance.py",
            "test_screen_reader_compatibility.py",
            "test_keyboard_navigation.py",
            "test_turkish_encoding.py",
        ]
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "modules": {},
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Tüm erişilebilirlik testlerini çalıştır"""
        print("=" * 80)
        print("ACCESSIBILITY AND COMPLIANCE TEST SUITE")
        print("Task 45: Accessibility and Compliance Testing")
        print("=" * 80)
        print()

        test_dir = os.path.dirname(os.path.abspath(__file__))

        for module in self.test_modules:
            print(f"\n{'=' * 80}")
            print(f"Running: {module}")
            print(f"{'=' * 80}\n")

            module_path = os.path.join(test_dir, module)

            # pytest ile testi çalıştır
            cmd = [
                "pytest",
                module_path,
                "-v",
                "--tb=short",
                "--color=yes" if self.verbose else "--color=no",
                "-x",  # İlk hatada dur
            ]

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=test_dir
                )

                # Sonuçları parse et
                module_result = self._parse_pytest_output(result.stdout, result.stderr)
                self.results["modules"][module] = module_result

                # Toplam istatistikleri güncelle
                self.results["total_tests"] += module_result["total"]
                self.results["passed"] += module_result["passed"]
                self.results["failed"] += module_result["failed"]
                self.results["skipped"] += module_result["skipped"]

                # Çıktıyı göster
                if self.verbose or module_result["failed"] > 0:
                    print(result.stdout)
                    if result.stderr:
                        print("STDERR:", result.stderr)

                # Özet
                print(f"\n{module} Özeti:")
                print(f"  Toplam: {module_result['total']}")
                print(f"  Başarılı: {module_result['passed']}")
                print(f"  Başarısız: {module_result['failed']}")
                print(f"  Atlanan: {module_result['skipped']}")

            except Exception as e:
                print(f"HATA: {module} çalıştırılırken hata oluştu: {str(e)}")
                self.results["modules"][module] = {
                    "error": str(e),
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                }

        return self.results

    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """pytest çıktısını parse et"""
        result = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0.0}

        # pytest özet satırını bul
        for line in stdout.split("\n"):
            if "passed" in line.lower() or "failed" in line.lower():
                # Örnek: "5 passed, 1 failed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        count = int(part)
                        if i + 1 < len(parts):
                            status = parts[i + 1].lower()
                            if "passed" in status:
                                result["passed"] = count
                            elif "failed" in status:
                                result["failed"] = count
                            elif "skipped" in status:
                                result["skipped"] = count

        result["total"] = result["passed"] + result["failed"] + result["skipped"]

        return result

    def generate_summary_report(self) -> str:
        """Özet rapor oluştur"""
        report = []
        report.append("\n" + "=" * 80)
        report.append("ACCESSIBILITY TEST SUITE - FINAL REPORT")
        report.append("=" * 80)
        report.append(f"\nTest Tarihi: {self.results['timestamp']}")
        report.append(f"\nToplam Test: {self.results['total_tests']}")
        report.append(f"Başarılı: {self.results['passed']} ✓")
        report.append(f"Başarısız: {self.results['failed']} ✗")
        report.append(f"Atlanan: {self.results['skipped']} ⊘")

        if self.results["total_tests"] > 0:
            success_rate = (self.results["passed"] / self.results["total_tests"]) * 100
            report.append(f"\nBaşarı Oranı: {success_rate:.1f}%")

        report.append("\n" + "-" * 80)
        report.append("Modül Bazında Sonuçlar:")
        report.append("-" * 80)

        for module, result in self.results["modules"].items():
            if "error" in result:
                report.append(f"\n{module}: HATA - {result['error']}")
            else:
                status = "✓ BAŞARILI" if result["failed"] == 0 else "✗ BAŞARISIZ"
                report.append(f"\n{module}: {status}")
                report.append(
                    f"  Toplam: {result['total']}, Başarılı: {result['passed']}, Başarısız: {result['failed']}"
                )

        report.append("\n" + "=" * 80)
        report.append("WCAG 2.1 Level AA Uyumluluk Durumu")
        report.append("=" * 80)

        wcag_module = self.results["modules"].get("test_wcag_compliance.py", {})
        if wcag_module.get("failed", 0) == 0 and wcag_module.get("total", 0) > 0:
            report.append("\n✓ Platform WCAG 2.1 Level AA standartlarına UYUMLU")
        else:
            report.append(
                "\n✗ Platform WCAG 2.1 Level AA standartlarına tam uyumlu değil"
            )
            report.append("  Lütfen başarısız testleri inceleyin ve düzeltmeler yapın.")

        report.append("\n" + "=" * 80)
        report.append("Ekran Okuyucu Uyumluluğu")
        report.append("=" * 80)

        sr_module = self.results["modules"].get(
            "test_screen_reader_compatibility.py", {}
        )
        if sr_module.get("failed", 0) == 0 and sr_module.get("total", 0) > 0:
            report.append("\n✓ Platform ekran okuyucular ile TAM UYUMLU")
            report.append("  Desteklenen: NVDA, JAWS, VoiceOver, TalkBack")
        else:
            report.append("\n✗ Ekran okuyucu uyumluluğunda sorunlar var")

        report.append("\n" + "=" * 80)
        report.append("Klavye Erişilebilirliği")
        report.append("=" * 80)

        kb_module = self.results["modules"].get("test_keyboard_navigation.py", {})
        if kb_module.get("failed", 0) == 0 and kb_module.get("total", 0) > 0:
            report.append("\n✓ Tüm özellikler klavye ile ERİŞİLEBİLİR")
        else:
            report.append("\n✗ Klavye erişilebilirliğinde sorunlar var")

        report.append("\n" + "=" * 80)
        report.append("Türkçe Karakter Desteği")
        report.append("=" * 80)

        tr_module = self.results["modules"].get("test_turkish_encoding.py", {})
        if tr_module.get("failed", 0) == 0 and tr_module.get("total", 0) > 0:
            report.append("\n✓ Türkçe karakterler (ç, ğ, ı, ö, ş, ü) TAM DESTEK")
            report.append("  UTF-8 encoding tüm platformda doğru çalışıyor")
        else:
            report.append("\n✗ Türkçe karakter desteğinde sorunlar var")

        report.append("\n" + "=" * 80)

        # Genel değerlendirme
        all_passed = self.results["failed"] == 0 and self.results["total_tests"] > 0

        if all_passed:
            report.append(
                "\n🎉 TEBRİKLER! Platform tüm erişilebilirlik testlerini geçti!"
            )
            report.append("\nPlatform şu standartlara uyumludur:")
            report.append("  ✓ WCAG 2.1 Level AA")
            report.append("  ✓ Ekran Okuyucu Uyumluluğu")
            report.append("  ✓ Tam Klavye Erişilebilirliği")
            report.append("  ✓ Türkçe Dil Desteği (UTF-8)")
        else:
            report.append("\n⚠️  UYARI: Bazı erişilebilirlik testleri başarısız oldu.")
            report.append(
                "\nLütfen başarısız testleri inceleyin ve gerekli düzeltmeleri yapın."
            )
            report.append(
                "Erişilebilirlik, tüm kullanıcılar için kritik öneme sahiptir."
            )

        report.append("\n" + "=" * 80)

        return "\n".join(report)

    def save_report(self, format: str = "txt") -> str:
        """Raporu dosyaya kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            filename = f"accessibility_report_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        else:
            filename = f"accessibility_report_{timestamp}.txt"
            report = self.generate_summary_report()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

        return filename


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(
        description="Accessibility and Compliance Test Suite Runner"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--report-format",
        choices=["txt", "json"],
        default="txt",
        help="Report format (default: txt)",
    )

    args = parser.parse_args()

    # Test runner'ı oluştur ve çalıştır
    runner = AccessibilityTestRunner(verbose=args.verbose)
    results = runner.run_all_tests()

    # Özet raporu göster
    summary = runner.generate_summary_report()
    print(summary)

    # Raporu kaydet
    report_file = runner.save_report(format=args.report_format)
    print(f"\nRapor kaydedildi: {report_file}")

    # Exit code
    exit_code = 0 if results["failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
