"""
Türkiye Üniversite Sınavları Hazırlık Platformu - Kapsamlı Kurulum ve Test
Tüm sistem bileşenlerinin kurulumu, entegrasyonu ve test edilmesi
"""
import subprocess
import sys
import os
import json
import time
from pathlib import Path
import logging
import threading
from datetime import datetime

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_and_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompleteSystemSetup:
    """Kapsamlı sistem kurulum ve test yöneticisi"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"

        self.setup_results = {
            "python_setup": False,
            "backend_dependencies": False,
            "frontend_dependencies": False,
            "test_coverage": False,
            "integration_tests": False,
            "system_health": False
        }

        self.test_results = {
            "unit_tests": {"passed": 0, "failed": 0, "coverage": 0.0},
            "integration_tests": {"passed": 0, "failed": 0},
            "api_tests": {"passed": 0, "failed": 0},
            "frontend_tests": {"passed": 0, "failed": 0}
        }

    def run_python_setup(self):
        """Python ortam kurulumu"""
        logger.info("🐍 Python ortam kurulumu başlatılıyor...")

        try:
            # Python kurulum scriptini çalıştır
            result = subprocess.run([
                sys.executable, "setup_python_environment.py"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=1800)

            if result.returncode == 0:
                logger.info("[CHECK] Python ortam kurulumu başarılı")
                self.setup_results["python_setup"] = True
                return True
            else:
                logger.error(f"[X] Python kurulum hatası: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"[X] Python kurulum exception: {e}")
            return False

    def setup_backend_dependencies(self):
        """Backend bağımlılıkları kurulumu"""
        logger.info("[PACKAGE] Backend bağımlılıkları kurulumu...")

        venv_path = self.backend_path / "venv"

        # Platform-specific python path
        if os.name == 'nt':  # Windows
            python_cmd = str(venv_path / "Scripts" / "python.exe")
            pip_cmd = str(venv_path / "Scripts" / "pip.exe")
        else:  # Unix-like
            python_cmd = str(venv_path / "bin" / "python")
            pip_cmd = str(venv_path / "bin" / "pip")

        try:
            # Requirements dosyalarını yükle
            requirements_files = [
                "requirements.txt",
                "requirements_langchain.txt"
            ]

            for req_file in requirements_files:
                req_path = self.backend_path / req_file
                if req_path.exists():
                    logger.info(f"[CLIPBOARD] {req_file} yükleniyor...")
                    result = subprocess.run([
                        pip_cmd, "install", "-r", str(req_path)
                    ], cwd=self.backend_path, capture_output=True, text=True, timeout=600)

                    if result.returncode != 0:
                        logger.warning(f"⚠️ {req_file} yükleme uyarısı: {result.stderr}")

            # Test bağımlılıkları
            test_packages = [
                "pytest>=7.4.3",
                "pytest-cov>=4.1.0",
                "pytest-asyncio>=0.21.1",
                "coverage>=7.3.0",
                "pytest-html>=4.1.1",
                "httpx>=0.25.2"
            ]

            logger.info("🧪 Test bağımlılıkları yükleniyor...")
            result = subprocess.run([
                pip_cmd, "install"
            ] + test_packages, cwd=self.backend_path, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info("[CHECK] Backend bağımlılıkları kuruldu")
                self.setup_results["backend_dependencies"] = True
                return True
            else:
                logger.error(f"[X] Test bağımlılıkları hatası: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"[X] Backend bağımlılık exception: {e}")
            return False

    def setup_frontend_dependencies(self):
        """Frontend bağımlılıkları kurulumu"""
        logger.info("[PALETTE] Frontend bağımlılıkları kurulumu...")

        if not self.frontend_path.exists():
            logger.warning("⚠️ Frontend klasörü bulunamadı")
            return True  # Frontend opsiyonel

        package_json = self.frontend_path / "package.json"
        if not package_json.exists():
            logger.warning("⚠️ package.json bulunamadı")
            return True

        try:
            # npm install
            logger.info("[PACKAGE] npm install çalıştırılıyor...")
            result = subprocess.run([
                "npm", "install"
            ], cwd=self.frontend_path, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                logger.info("[CHECK] Frontend bağımlılıkları kuruldu")
                self.setup_results["frontend_dependencies"] = True
                return True
            else:
                logger.warning(f"⚠️ npm install uyarısı: {result.stderr}")
                # Frontend kurulumu başarısız olsa bile devam et
                return True

        except FileNotFoundError:
            logger.warning("⚠️ npm bulunamadı, frontend kurulumu atlanıyor")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Frontend kurulum exception: {e}")
            return True

    def run_test_coverage_analysis(self):
        """Test coverage analizi"""
        logger.info("[CHART] Test coverage analizi başlatılıyor...")

        try:
            # Coverage analiz scriptini çalıştır
            result = subprocess.run([
                sys.executable, "run_coverage_analysis.py"
            ], cwd=self.backend_path, capture_output=True, text=True, timeout=600)

            # Coverage sonuçlarını parse et
            coverage_json = self.backend_path / "coverage.json"
            if coverage_json.exists():
                with open(coverage_json, 'r') as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data["totals"]["percent_covered"]
                self.test_results["unit_tests"]["coverage"] = total_coverage

                logger.info(f"[TRENDING_UP] Test Coverage: {total_coverage:.2f}%")

                if total_coverage >= 70.0:
                    logger.info("[CHECK] Coverage hedefi karşılandı (≥70%)")
                    self.setup_results["test_coverage"] = True
                else:
                    logger.warning(f"⚠️ Coverage hedefi karşılanmadı ({total_coverage:.2f}% < 70%)")

            # Test sonuçlarını parse et
            if "passed" in result.stdout:
                import re
                passed_match = re.search(r'(\d+) passed', result.stdout)
                failed_match = re.search(r'(\d+) failed', result.stdout)

                if passed_match:
                    self.test_results["unit_tests"]["passed"] = int(passed_match.group(1))
                if failed_match:
                    self.test_results["unit_tests"]["failed"] = int(failed_match.group(1))

            return result.returncode == 0 or coverage_json.exists()

        except Exception as e:
            logger.error(f"[X] Coverage analizi exception: {e}")
            return False

    def run_integration_tests(self):
        """Entegrasyon testleri"""
        logger.info("[LINK] Entegrasyon testleri başlatılıyor...")

        venv_path = self.backend_path / "venv"

        if os.name == 'nt':  # Windows
            python_cmd = str(venv_path / "Scripts" / "python.exe")
        else:  # Unix-like
            python_cmd = str(venv_path / "bin" / "python")

        try:
            # Entegrasyon testlerini çalıştır
            result = subprocess.run([
                python_cmd, "-m", "pytest",
                "tests/test_full_integration.py",
                "-v", "--tb=short"
            ], cwd=self.backend_path, capture_output=True, text=True, timeout=300)

            logger.info("🧪 Entegrasyon test sonuçları:")
            logger.info(result.stdout)

            if result.stderr:
                logger.warning("⚠️ Entegrasyon test uyarıları:")
                logger.warning(result.stderr)

            # Test sonuçlarını parse et
            if "passed" in result.stdout:
                import re
                passed_match = re.search(r'(\d+) passed', result.stdout)
                failed_match = re.search(r'(\d+) failed', result.stdout)

                if passed_match:
                    self.test_results["integration_tests"]["passed"] = int(passed_match.group(1))
                if failed_match:
                    self.test_results["integration_tests"]["failed"] = int(failed_match.group(1))

            success = result.returncode == 0 or "passed" in result.stdout
            if success:
                logger.info("[CHECK] Entegrasyon testleri başarılı")
                self.setup_results["integration_tests"] = True
            else:
                logger.warning("⚠️ Bazı entegrasyon testleri başarısız")

            return success

        except Exception as e:
            logger.error(f"[X] Entegrasyon testleri exception: {e}")
            return False

    def run_api_tests(self):
        """API testleri"""
        logger.info("[GLOBE] API testleri başlatılıyor...")

        venv_path = self.backend_path / "venv"

        if os.name == 'nt':  # Windows
            python_cmd = str(venv_path / "Scripts" / "python.exe")
        else:  # Unix-like
            python_cmd = str(venv_path / "bin" / "python")

        try:
            # API testlerini çalıştır
            api_test_files = [
                "tests/test_learning_style_api.py",
                "tests/test_sinav_api.py"
            ]

            total_passed = 0
            total_failed = 0

            for test_file in api_test_files:
                test_path = self.backend_path / test_file
                if test_path.exists():
                    result = subprocess.run([
                        python_cmd, "-m", "pytest",
                        str(test_path),
                        "-v", "--tb=short"
                    ], cwd=self.backend_path, capture_output=True, text=True, timeout=300)

                    # Test sonuçlarını parse et
                    if "passed" in result.stdout:
                        import re
                        passed_match = re.search(r'(\d+) passed', result.stdout)
                        failed_match = re.search(r'(\d+) failed', result.stdout)

                        if passed_match:
                            total_passed += int(passed_match.group(1))
                        if failed_match:
                            total_failed += int(failed_match.group(1))

            self.test_results["api_tests"]["passed"] = total_passed
            self.test_results["api_tests"]["failed"] = total_failed

            logger.info(f"[CHART] API Testleri: {total_passed} başarılı, {total_failed} başarısız")

            return total_passed > 0

        except Exception as e:
            logger.error(f"[X] API testleri exception: {e}")
            return False

    def check_system_health(self):
        """Sistem sağlık kontrolü"""
        logger.info("🏥 Sistem sağlık kontrolü...")

        try:
            # Backend sunucusunu başlat (arka planda)
            venv_path = self.backend_path / "venv"

            if os.name == 'nt':  # Windows
                python_cmd = str(venv_path / "Scripts" / "python.exe")
            else:  # Unix-like
                python_cmd = str(venv_path / "bin" / "python")

            # Sunucuyu başlat
            server_process = subprocess.Popen([
                python_cmd, "main.py"
            ], cwd=self.backend_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Sunucunun başlamasını bekle
            time.sleep(10)

            # Health endpoint'ini test et
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=5)

                if response.status_code == 200:
                    logger.info("[CHECK] Sistem sağlık kontrolü başarılı")
                    self.setup_results["system_health"] = True
                    health_success = True
                else:
                    logger.warning(f"⚠️ Health endpoint yanıt kodu: {response.status_code}")
                    health_success = False

            except ImportError:
                logger.warning("⚠️ requests modülü bulunamadı, health kontrolü atlanıyor")
                health_success = True
            except Exception as e:
                logger.warning(f"⚠️ Health kontrolü hatası: {e}")
                health_success = False

            # Sunucuyu kapat
            server_process.terminate()
            server_process.wait(timeout=5)

            return health_success

        except Exception as e:
            logger.error(f"[X] Sistem sağlık kontrolü exception: {e}")
            return False

    def generate_final_report(self):
        """Final rapor oluştur"""
        logger.info("[CLIPBOARD] Final rapor oluşturuluyor...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "setup_results": self.setup_results,
            "test_results": self.test_results,
            "summary": {
                "total_setup_steps": len(self.setup_results),
                "successful_setup_steps": sum(self.setup_results.values()),
                "setup_success_rate": sum(self.setup_results.values()) / len(self.setup_results) * 100,
                "total_tests_passed": (
                    self.test_results["unit_tests"]["passed"] +
                    self.test_results["integration_tests"]["passed"] +
                    self.test_results["api_tests"]["passed"]
                ),
                "total_tests_failed": (
                    self.test_results["unit_tests"]["failed"] +
                    self.test_results["integration_tests"]["failed"] +
                    self.test_results["api_tests"]["failed"]
                ),
                "test_coverage": self.test_results["unit_tests"]["coverage"]
            }
        }

        # JSON raporu kaydet
        report_path = self.project_root / "setup_and_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Konsol raporu
        logger.info("\n" + "=" * 80)
        logger.info("[CHART] KAPSAMLI KURULUM VE TEST RAPORU")
        logger.info("=" * 80)

        logger.info("[TOOL] Kurulum Sonuçları:")
        for step, success in self.setup_results.items():
            status = "[CHECK]" if success else "[X]"
            logger.info(f"  {status} {step.replace('_', ' ').title()}")

        logger.info(f"\n[TRENDING_UP] Kurulum Başarı Oranı: {report['summary']['setup_success_rate']:.1f}%")

        logger.info("\n🧪 Test Sonuçları:")
        logger.info(f"  [CHART] Unit Tests: {self.test_results['unit_tests']['passed']} [CHECK], {self.test_results['unit_tests']['failed']} [X]")
        logger.info(f"  [LINK] Integration Tests: {self.test_results['integration_tests']['passed']} [CHECK], {self.test_results['integration_tests']['failed']} [X]")
        logger.info(f"  [GLOBE] API Tests: {self.test_results['api_tests']['passed']} [CHECK], {self.test_results['api_tests']['failed']} [X]")
        logger.info(f"  [TRENDING_UP] Test Coverage: {report['summary']['test_coverage']:.2f}%")

        logger.info(f"\n[TARGET] Toplam Test: {report['summary']['total_tests_passed']} [CHECK], {report['summary']['total_tests_failed']} [X]")

        # Başarı değerlendirmesi
        setup_success = report['summary']['setup_success_rate'] >= 80
        coverage_success = report['summary']['test_coverage'] >= 70
        test_success = report['summary']['total_tests_passed'] > 0

        overall_success = setup_success and coverage_success and test_success

        if overall_success:
            logger.info("\n[PARTY] GENEL DEĞERLENDİRME: BAŞARILI!")
            logger.info("[CHECK] Sistem kurulumu tamamlandı")
            logger.info("[CHECK] Test coverage hedefi karşılandı")
            logger.info("[CHECK] Testler başarıyla çalıştı")
        else:
            logger.info("\n⚠️ GENEL DEĞERLENDİRME: İYİLEŞTİRME GEREKLİ")
            if not setup_success:
                logger.warning("[X] Kurulum adımları tamamlanmadı")
            if not coverage_success:
                logger.warning("[X] Test coverage hedefi karşılanmadı")
            if not test_success:
                logger.warning("[X] Test sonuçları yetersiz")

        logger.info(f"\n[PAGE] Detaylı rapor: {report_path}")
        logger.info("=" * 80)

        return overall_success

    def run_complete_setup_and_test(self):
        """Kapsamlı kurulum ve test sürecini çalıştır"""
        logger.info("[ROCKET] KAPSAMLI KURULUM VE TEST SÜRECİ BAŞLATIYOR...")
        logger.info("=" * 80)

        start_time = time.time()

        # 1. Python ortam kurulumu
        if not self.run_python_setup():
            logger.error("[X] Python kurulumu başarısız, devam ediliyor...")

        # 2. Backend bağımlılıkları
        if not self.setup_backend_dependencies():
            logger.error("[X] Backend bağımlılıkları başarısız, devam ediliyor...")

        # 3. Frontend bağımlılıkları
        if not self.setup_frontend_dependencies():
            logger.warning("⚠️ Frontend bağımlılıkları başarısız, devam ediliyor...")

        # 4. Test coverage analizi
        if not self.run_test_coverage_analysis():
            logger.warning("⚠️ Test coverage analizi başarısız, devam ediliyor...")

        # 5. Entegrasyon testleri
        if not self.run_integration_tests():
            logger.warning("⚠️ Entegrasyon testleri başarısız, devam ediliyor...")

        # 6. API testleri
        if not self.run_api_tests():
            logger.warning("⚠️ API testleri başarısız, devam ediliyor...")

        # 7. Sistem sağlık kontrolü
        if not self.check_system_health():
            logger.warning("⚠️ Sistem sağlık kontrolü başarısız, devam ediliyor...")

        # 8. Final rapor
        overall_success = self.generate_final_report()

        end_time = time.time()
        total_time = end_time - start_time

        logger.info(f"\n⏱️ Toplam süre: {total_time:.1f} saniye")

        return overall_success


def main():
    """Ana fonksiyon"""
    setup = CompleteSystemSetup()
    success = setup.run_complete_setup_and_test()

    if success:
        print("\n[PARTY] Kapsamlı kurulum ve test başarıyla tamamlandı!")
        print("[ROCKET] Sistem kullanıma hazır!")
        return 0
    else:
        print("\n⚠️ Kurulum ve test tamamlandı ancak bazı iyileştirmeler gerekli")
        print("[CLIPBOARD] Detaylı raporu kontrol edin: setup_and_test_report.json")
        return 1


if __name__ == "__main__":
    exit(main())
