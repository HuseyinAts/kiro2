#!/usr/bin/env python3
"""
Teknofest 2025 Eğitim Eylemci Platformu
Comprehensive Test Runner

Bu script tüm testleri çalıştırır ve kapsamlı test raporu oluşturur.
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import argparse


class TestRunner:
    """Kapsamlı test çalıştırıcı sınıfı"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "backend": {},
            "frontend": {},
            "integration": {},
            "performance": {},
            "security": {},
            "accessibility": {}
        }
        self.start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        """Log mesajı yazdır"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "SUCCESS"]:
            print(f"[{timestamp}] {level}: {message}")

    def run_command(self, command: str, cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
        """Komut çalıştır ve sonucu döndür"""
        self.log(f"Running: {command}", "DEBUG")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }

    def run_backend_tests(self) -> bool:
        """Backend testlerini çalıştır"""
        self.log("🐍 Running backend tests...", "INFO")

        backend_dir = Path("backend")
        if not backend_dir.exists():
            self.log("Backend directory not found", "ERROR")
            return False

        # Unit tests
        self.log("Running backend unit tests...")
        unit_result = self.run_command(
            "python -m pytest tests/ -v --tb=short --cov=. --cov-report=html:htmlcov --cov-report=term-missing --cov-fail-under=80",
            cwd=str(backend_dir)
        )

        self.results["backend"]["unit_tests"] = {
            "success": unit_result["success"],
            "output": unit_result["stdout"],
            "errors": unit_result["stderr"]
        }

        # Integration tests
        self.log("Running backend integration tests...")
        integration_result = self.run_command(
            "python -m pytest tests/test_api_integration_comprehensive.py -v",
            cwd=str(backend_dir)
        )

        self.results["backend"]["integration_tests"] = {
            "success": integration_result["success"],
            "output": integration_result["stdout"],
            "errors": integration_result["stderr"]
        }

        # Service tests
        self.log("Running backend service tests...")
        service_result = self.run_command(
            "python -m pytest tests/test_services_comprehensive.py -v",
            cwd=str(backend_dir)
        )

        self.results["backend"]["service_tests"] = {
            "success": service_result["success"],
            "output": service_result["stdout"],
            "errors": service_result["stderr"]
        }

        # Revolutionary features tests
        self.log("Running revolutionary features tests...")
        revolutionary_result = self.run_command(
            "python -m pytest tests/test_revolutionary_features.py -v",
            cwd=str(backend_dir)
        )

        self.results["backend"]["revolutionary_tests"] = {
            "success": revolutionary_result["success"],
            "output": revolutionary_result["stdout"],
            "errors": revolutionary_result["stderr"]
        }

        backend_success = all([
            unit_result["success"],
            integration_result["success"],
            service_result["success"],
            revolutionary_result["success"]
        ])

        if backend_success:
            self.log("[CHECK] Backend tests passed", "SUCCESS")
        else:
            self.log("[X] Backend tests failed", "ERROR")

        return backend_success

    def run_frontend_tests(self) -> bool:
        """Frontend testlerini çalıştır"""
        self.log("⚛️ Running frontend tests...", "INFO")

        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            self.log("Frontend directory not found", "ERROR")
            return False

        # Install dependencies
        self.log("Installing frontend dependencies...")
        install_result = self.run_command("npm ci", cwd=str(frontend_dir))
        if not install_result["success"]:
            self.log("Failed to install frontend dependencies", "ERROR")
            return False

        # Type checking
        self.log("Running TypeScript type checking...")
        type_result = self.run_command("npm run type-check", cwd=str(frontend_dir))

        self.results["frontend"]["type_check"] = {
            "success": type_result["success"],
            "output": type_result["stdout"],
            "errors": type_result["stderr"]
        }

        # Linting
        self.log("Running ESLint...")
        lint_result = self.run_command("npm run lint", cwd=str(frontend_dir))

        self.results["frontend"]["lint"] = {
            "success": lint_result["success"],
            "output": lint_result["stdout"],
            "errors": lint_result["stderr"]
        }

        # Unit tests with coverage
        self.log("Running frontend unit tests with coverage...")
        test_result = self.run_command("npm run test:coverage", cwd=str(frontend_dir))

        self.results["frontend"]["unit_tests"] = {
            "success": test_result["success"],
            "output": test_result["stdout"],
            "errors": test_result["stderr"]
        }

        # Build test
        self.log("Testing frontend build...")
        build_result = self.run_command("npm run build", cwd=str(frontend_dir))

        self.results["frontend"]["build"] = {
            "success": build_result["success"],
            "output": build_result["stdout"],
            "errors": build_result["stderr"]
        }

        frontend_success = all([
            type_result["success"],
            lint_result["success"],
            test_result["success"],
            build_result["success"]
        ])

        if frontend_success:
            self.log("[CHECK] Frontend tests passed", "SUCCESS")
        else:
            self.log("[X] Frontend tests failed", "ERROR")

        return frontend_success

    def run_performance_tests(self) -> bool:
        """Performance testlerini çalıştır"""
        self.log("[ROCKET] Running performance tests...", "INFO")

        # Backend performance tests
        backend_perf_result = self.run_command(
            "python -m pytest tests/test_performance_optimization.py --benchmark-only",
            cwd="backend"
        )

        self.results["performance"]["backend"] = {
            "success": backend_perf_result["success"],
            "output": backend_perf_result["stdout"],
            "errors": backend_perf_result["stderr"]
        }

        if backend_perf_result["success"]:
            self.log("[CHECK] Performance tests passed", "SUCCESS")
        else:
            self.log("[X] Performance tests failed", "ERROR")

        return backend_perf_result["success"]

    def run_security_tests(self) -> bool:
        """Security testlerini çalıştır"""
        self.log("[LOCKED] Running security tests...", "INFO")

        # Backend security scan
        safety_result = self.run_command("pip install safety && safety check", cwd="backend")
        bandit_result = self.run_command("pip install bandit && bandit -r . -f json", cwd="backend")

        # Frontend security scan
        audit_result = self.run_command("npm audit --audit-level=high", cwd="frontend")

        self.results["security"]["backend_safety"] = {
            "success": safety_result["success"],
            "output": safety_result["stdout"],
            "errors": safety_result["stderr"]
        }

        self.results["security"]["backend_bandit"] = {
            "success": bandit_result["success"],
            "output": bandit_result["stdout"],
            "errors": bandit_result["stderr"]
        }

        self.results["security"]["frontend_audit"] = {
            "success": audit_result["success"],
            "output": audit_result["stdout"],
            "errors": audit_result["stderr"]
        }

        # Security tests are informational, don't fail the build
        self.log("[CHECK] Security scans completed", "SUCCESS")
        return True

    def generate_report(self) -> str:
        """Test raporu oluştur"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""
# Teknofest 2025 Eğitim Eylemci Platformu - Test Raporu

**Tarih:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Süre:** {duration.total_seconds():.2f} saniye

## [CHART] Test Sonuçları Özeti

### Backend Tests
"""

        # Backend results
        backend_results = self.results["backend"]
        for test_type, result in backend_results.items():
            status = "[CHECK] PASSED" if result["success"] else "[X] FAILED"
            report += f"- {test_type.replace('_', ' ').title()}: {status}\n"

        report += "\n### Frontend Tests\n"

        # Frontend results
        frontend_results = self.results["frontend"]
        for test_type, result in frontend_results.items():
            status = "[CHECK] PASSED" if result["success"] else "[X] FAILED"
            report += f"- {test_type.replace('_', ' ').title()}: {status}\n"

        report += "\n### Performance Tests\n"

        # Performance results
        performance_results = self.results["performance"]
        for test_type, result in performance_results.items():
            status = "[CHECK] PASSED" if result["success"] else "[X] FAILED"
            report += f"- {test_type.replace('_', ' ').title()}: {status}\n"

        report += "\n### Security Scans\n"

        # Security results
        security_results = self.results["security"]
        for test_type, result in security_results.items():
            status = "[CHECK] COMPLETED" if result["success"] else "⚠️ ISSUES FOUND"
            report += f"- {test_type.replace('_', ' ').title()}: {status}\n"

        # Overall status
        backend_success = all(r["success"] for r in backend_results.values())
        frontend_success = all(r["success"] for r in frontend_results.values())
        performance_success = all(r["success"] for r in performance_results.values())

        overall_success = backend_success and frontend_success and performance_success

        report += f"\n## [TARGET] Genel Durum\n"
        report += f"**Sonuç:** {'[CHECK] TÜM TESTLER BAŞARILI' if overall_success else '[X] BAZI TESTLER BAŞARISIZ'}\n"

        # Coverage information
        report += f"\n## [TRENDING_UP] Test Coverage\n"
        report += f"- Backend Coverage: >80% (hedef)\n"
        report += f"- Frontend Coverage: >80% (hedef)\n"

        # Recommendations
        if not overall_success:
            report += f"\n## [TOOL] Öneriler\n"
            if not backend_success:
                report += f"- Backend testlerini gözden geçirin\n"
            if not frontend_success:
                report += f"- Frontend testlerini gözden geçirin\n"
            if not performance_success:
                report += f"- Performance sorunlarını çözün\n"

        return report

    def save_results(self):
        """Test sonuçlarını dosyaya kaydet"""
        results_file = Path("test_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

        report = self.generate_report()
        report_file = Path("TEST_REPORT.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        self.log(f"Test results saved to {results_file}", "INFO")
        self.log(f"Test report saved to {report_file}", "INFO")

    def run_all_tests(self) -> bool:
        """Tüm testleri çalıştır"""
        self.log("[ROCKET] Starting comprehensive test suite...", "INFO")

        success = True

        # Backend tests
        if not self.run_backend_tests():
            success = False

        # Frontend tests
        if not self.run_frontend_tests():
            success = False

        # Performance tests
        if not self.run_performance_tests():
            success = False

        # Security tests (informational)
        self.run_security_tests()

        # Save results
        self.save_results()

        # Final report
        end_time = datetime.now()
        duration = end_time - self.start_time

        if success:
            self.log(f"[PARTY] All tests completed successfully in {duration.total_seconds():.2f}s", "SUCCESS")
        else:
            self.log(f"💥 Some tests failed. Duration: {duration.total_seconds():.2f}s", "ERROR")

        return success


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for Teknofest 2025 platform")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--security-only", action="store_true", help="Run only security tests")

    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose)

    success = True

    if args.backend_only:
        success = runner.run_backend_tests()
    elif args.frontend_only:
        success = runner.run_frontend_tests()
    elif args.performance_only:
        success = runner.run_performance_tests()
    elif args.security_only:
        success = runner.run_security_tests()
    else:
        success = runner.run_all_tests()

    # Save results regardless of success
    runner.save_results()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
