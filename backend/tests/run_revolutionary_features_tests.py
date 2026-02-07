"""
Revolutionary Features Test Suite Runner
7 Devrimsel AI Özelliği Kapsamlı Test Çalıştırıcısı

Bu script, tüm devrimsel özelliklerin testlerini koordineli şekilde çalıştırır
ve detaylı raporlama yapar.

Requirements: 10.1-10.7, 11.1-11.6, 12.1-12.6
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict

# Test modüllerini import et


class RevolutionaryFeaturesTestRunner:
    """Devrimsel özellikler test çalıştırıcısı"""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

    def run_all_tests(self) -> Dict[str, Any]:
        """Tüm testleri çalıştır"""

        print("[ROCKET] Revolutionary Features Test Suite Başlatılıyor...")
        print("=" * 80)

        self.start_time = datetime.now()

        # Test modülleri
        test_modules = [
            {
                "name": "VARK + Felder-Silverman Hibrit Sistem",
                "file": "test_vark_felder_hybrid_system.py",
                "description": "64 farklı öğrenme profili kombinasyonu testleri",
            },
            {
                "name": "Türk FSRS Sistemi",
                "file": "test_turkish_fsrs_system.py",
                "description": "17 parametreli Türk öğrenci davranışları optimizasyonu",
            },
            {
                "name": "Multi-Agent Blackboard Sistemi",
                "file": "test_multi_agent_blackboard_integration.py",
                "description": "Gerçek zamanlı agent koordinasyonu ve sinerji",
            },
            {
                "name": "Türkçe Morfoloji IRT Sistemi",
                "file": "test_turkish_morphology_irt_comprehensive.py",
                "description": "ÖSYM/ETS standartlarını aşan morfolojik analiz",
            },
            {
                "name": "Ana Revolutionary Features Entegrasyonu",
                "file": "test_revolutionary_features.py",
                "description": "Tüm devrimsel özelliklerin entegrasyon testleri",
            },
        ]

        # Her modülü çalıştır
        for module in test_modules:
            print(f"\n[CLIPBOARD] {module['name']} Testleri Çalıştırılıyor...")
            print(f"   {module['description']}")
            print("-" * 60)

            result = self._run_test_module(module["file"])
            self.test_results[module["name"]] = result

            # Sonuçları göster
            self._display_module_results(module["name"], result)

        self.end_time = datetime.now()

        # Genel rapor
        self._generate_final_report()

        return self.test_results

    def _run_test_module(self, test_file: str) -> Dict[str, Any]:
        """Tek test modülünü çalıştır"""

        try:
            # pytest ile test çalıştır
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file=reports/{test_file}_report.json",
            ]

            # Reports klasörünü oluştur
            os.makedirs("reports", exist_ok=True)

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__)
            )

            # JSON raporu oku
            report_file = f"reports/{test_file}_report.json"
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    json_report = json.load(f)
            else:
                json_report = {}

            return {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "json_report": json_report,
                "success": result.returncode == 0,
            }

        except Exception as e:
            return {
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "json_report": {},
                "success": False,
                "error": str(e),
            }

    def _display_module_results(self, module_name: str, result: Dict[str, Any]):
        """Modül sonuçlarını göster"""

        if result["success"]:
            print(f"[CHECK] {module_name}: BAŞARILI")

            # JSON raporundan detayları al
            json_report = result.get("json_report", {})
            summary = json_report.get("summary", {})

            if summary:
                total = summary.get("total", 0)
                passed = summary.get("passed", 0)
                failed = summary.get("failed", 0)
                skipped = summary.get("skipped", 0)

                print(
                    f"   [CHART] Toplam: {total}, Başarılı: {passed}, Başarısız: {failed}, Atlandı: {skipped}"
                )

                # Genel istatistikleri güncelle
                self.total_tests += total
                self.passed_tests += passed
                self.failed_tests += failed
                self.skipped_tests += skipped

        else:
            print(f"[X] {module_name}: BAŞARISIZ")
            print(f"   Hata: {result.get('stderr', 'Bilinmeyen hata')}")

    def _generate_final_report(self):
        """Final raporu oluştur"""

        duration = (self.end_time - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print("[TARGET] REVOLUTIONARY FEATURES TEST SUITE RAPORU")
        print("=" * 80)

        print(f"⏱️  Toplam Süre: {duration:.2f} saniye")
        print("[CHART] Test İstatistikleri:")
        print(f"   • Toplam Test: {self.total_tests}")
        print(f"   • Başarılı: {self.passed_tests} [CHECK]")
        print(f"   • Başarısız: {self.failed_tests} [X]")
        print(f"   • Atlandı: {self.skipped_tests} ⏭️")

        if self.total_tests > 0:
            success_rate = (self.passed_tests / self.total_tests) * 100
            print(f"   • Başarı Oranı: {success_rate:.1f}%")

        print("\n[CLIPBOARD] Modül Sonuçları:")
        for module_name, result in self.test_results.items():
            status = "[CHECK] BAŞARILI" if result["success"] else "[X] BAŞARISIZ"
            print(f"   • {module_name}: {status}")

        # Detaylı rapor dosyası oluştur
        self._save_detailed_report()

        print(
            "\n[PAGE] Detaylı rapor: reports/revolutionary_features_final_report.json"
        )
        print("=" * 80)

    def _save_detailed_report(self):
        """Detaylı raporu kaydet"""

        report = {
            "test_suite": "Revolutionary Features Test Suite",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "skipped_tests": self.skipped_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100)
                if self.total_tests > 0
                else 0,
            },
            "modules": self.test_results,
            "revolutionary_features": {
                "1": "VARK + Felder-Silverman Hibrit Öğrenme Stili Sistemi (64 profil)",
                "2": "Türk ZPD + MEB Maarif Modeli",
                "3": "Türkçe Morfoloji IRT Sistemi",
                "4": "Türk FSRS Sistemi (17 parametre)",
                "5": "3 Seviyeli Türkçe Metin Basitleştirme",
                "6": "Türkçe Bionic Reading (Disleksi desteği)",
                "7": "Multi-Agent Blackboard Sistemi",
            },
        }

        os.makedirs("reports", exist_ok=True)
        with open(
            "reports/revolutionary_features_final_report.json", "w", encoding="utf-8"
        ) as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def run_specific_feature_tests(self, feature_name: str) -> Dict[str, Any]:
        """Belirli bir özelliğin testlerini çalıştır"""

        feature_map = {
            "vark_felder": "test_vark_felder_hybrid_system.py",
            "fsrs": "test_turkish_fsrs_system.py",
            "blackboard": "test_multi_agent_blackboard_integration.py",
            "morphology_irt": "test_turkish_morphology_irt_comprehensive.py",
            "integration": "test_revolutionary_features.py",
        }

        if feature_name not in feature_map:
            raise ValueError(f"Geçersiz özellik adı: {feature_name}")

        print(f"[TARGET] {feature_name} özelliği testleri çalıştırılıyor...")

        result = self._run_test_module(feature_map[feature_name])
        self._display_module_results(feature_name, result)

        return result

    def run_performance_tests_only(self) -> Dict[str, Any]:
        """Sadece performans testlerini çalıştır"""

        print("[LIGHTNING] Performans testleri çalıştırılıyor...")

        performance_tests = [
            "test_revolutionary_features.py::TestRevolutionaryFeaturesPerformance",
            "test_vark_felder_hybrid_system.py::TestPerformanceAndScalability",
            "test_turkish_fsrs_system.py::TestFSRSPerformanceOptimization",
            "test_multi_agent_blackboard_integration.py::TestPerformanceAndScalability",
            "test_turkish_morphology_irt_comprehensive.py::TestPerformanceOptimization",
        ]

        results = {}
        for test_class in performance_tests:
            print(f"🏃‍♂️ {test_class} çalıştırılıyor...")

            cmd = [sys.executable, "-m", "pytest", test_class, "-v", "--tb=short"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            results[test_class] = {
                "success": result.returncode == 0,
                "output": result.stdout,
            }

            status = "[CHECK]" if result.returncode == 0 else "[X]"
            print(f"   {status} {test_class}")

        return results


def main():
    """Ana fonksiyon"""

    if len(sys.argv) > 1:
        command = sys.argv[1]

        runner = RevolutionaryFeaturesTestRunner()

        if command == "all":
            runner.run_all_tests()
        elif command == "performance":
            runner.run_performance_tests_only()
        elif command in [
            "vark_felder",
            "fsrs",
            "blackboard",
            "morphology_irt",
            "integration",
        ]:
            runner.run_specific_feature_tests(command)
        else:
            print(f"[X] Geçersiz komut: {command}")
            print(
                "Kullanım: python run_revolutionary_features_tests.py [all|performance|vark_felder|fsrs|blackboard|morphology_irt|integration]"
            )
            sys.exit(1)
    else:
        # Varsayılan: tüm testleri çalıştır
        runner = RevolutionaryFeaturesTestRunner()
        runner.run_all_tests()


if __name__ == "__main__":
    main()
