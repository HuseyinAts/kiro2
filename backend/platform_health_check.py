"""
Platform Sağlık Kontrolü - Hızlı Durum Raporu
Teknofest 2025 - Eğitim Eylemci Projesi

Backend çalışmadan da çalıştırılabilir - dosya bazlı kontroller
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class QuickHealthCheck:
    """Hızlı platform sağlık kontrolü"""

    def __init__(self):
        self.backend_path = Path(__file__).parent
        self.results = []

    def check_api_files(self) -> Dict[str, Any]:
        """API dosyalarının varlığını kontrol et"""
        api_dir = self.backend_path / "api"

        critical_apis = [
            "health.py",
            "auth.py",
            "sinav.py",
            "exam_performance.py",
            "monitoring.py",
            "analytics.py",
            "learning_style.py",
            "learning_path.py",
            "zpd_maarif.py",
            "irt_morfoloji.py",
            "student_dashboard.py",
            "cache.py",
            "agents.py",
            "soru_bankasi.py",
            "question_crud_api.py",
            "content_management.py",
            "admin.py",
            "text_simplification.py",
            "ogretmen.py",
            "advanced_reports.py",
            "performance.py",
            "fsrs.py",
            "zemberek.py",
            "monitoring_routes.py",
            "osym_routes.py",
            "berturk_api.py",
            "rag.py",
            "enhanced_chat.py",
            "cultural_adaptation_api.py",
            "bionic_reading.py",
            "turkish_nlp.py",
            "curriculum_compliance.py",
            "multi_agent.py",
            "elasticsearch.py",
            "veli.py",
            "parent.py",
            "ebatv.py",
            "turkish_nlp_chat.py",
            "math_solution_steps.py",
            "video_solution.py",
            "manipulatives_api.py",  # TASK 87 - YENİ!
        ]

        existing = []
        missing = []

        for api_file in critical_apis:
            file_path = api_dir / api_file
            if file_path.exists():
                existing.append(api_file)
            else:
                missing.append(api_file)

        return {
            "category": "API Files",
            "total": len(critical_apis),
            "existing": len(existing),
            "missing": len(missing),
            "missing_files": missing,
            "status": "PASS" if len(missing) == 0 else "WARNING",
            "score": int((len(existing) / len(critical_apis)) * 100),
        }

    def check_core_services(self) -> Dict[str, Any]:
        """Core servis dosyalarını kontrol et"""
        core_dir = self.backend_path / "core"

        critical_services = [
            "database.py",
            "cache.py",
            "multi_layer_cache.py",  # TASK 7 - YENİ!
            "structured_logger.py",  # TASK 10 - YENİ!
            "metrics_collector.py",  # TASK 11 - YENİ!
            "error_handler.py",  # TASK 9 - YENİ!
            "circuit_breaker.py",  # TASK 9 - YENİ!
            "osym_exam_engine.py",
            "jwt_auth.py",
            "rbac_system.py",
            "kvkk_compliance.py",
            "encryption_service.py",
            "rate_limiting.py",
            "auth_rate_limiting.py",
            "cors_config.py",
            "ddos_protection.py",
            "structured_logging.py",
            "logging_config.py",
            "logging_middleware.py",
            "performance_middleware.py",
            "monitoring.py",
            "production_health_monitor.py",
            "elasticsearch_config.py",
            "elasticsearch_logger.py",
            "analytics_monitoring.py",
        ]

        existing = []
        missing = []

        for service_file in critical_services:
            file_path = core_dir / service_file
            if file_path.exists():
                existing.append(service_file)
            else:
                missing.append(service_file)

        return {
            "category": "Core Services",
            "total": len(critical_services),
            "existing": len(existing),
            "missing": len(missing),
            "missing_files": missing,
            "status": "PASS" if len(missing) == 0 else "WARNING",
            "score": int((len(existing) / len(critical_services)) * 100),
        }

    def check_ai_agents(self) -> Dict[str, Any]:
        """AI agent dosyalarını kontrol et"""
        agents_dir = self.backend_path / "agents"

        critical_agents = [
            "learning_path_agent.py",
            "study_agent.py",
            "exam_agent.py",
            "blackboard_coordinator.py",
        ]

        existing = []
        missing = []

        if agents_dir.exists():
            for agent_file in critical_agents:
                file_path = agents_dir / agent_file
                if file_path.exists():
                    existing.append(agent_file)
                else:
                    missing.append(agent_file)
        else:
            missing = critical_agents

        return {
            "category": "AI Agents",
            "total": len(critical_agents),
            "existing": len(existing),
            "missing": len(missing),
            "missing_files": missing,
            "status": "PASS" if len(missing) == 0 else "WARNING",
            "score": int((len(existing) / len(critical_agents)) * 100)
            if len(critical_agents) > 0
            else 0,
        }

    def check_services(self) -> Dict[str, Any]:
        """Servis dosyalarını kontrol et"""
        services_dir = self.backend_path / "services"

        critical_services = [
            "video_recommendation_service.py",  # TASK 2 - YENİ!
            "turkish_content_filter.py",  # TASK 3 - YENİ!
            "health_check_service.py",  # TASK 4 - YENİ!
        ]

        existing = []
        missing = []

        if services_dir.exists():
            for service_file in critical_services:
                file_path = services_dir / service_file
                if file_path.exists():
                    existing.append(service_file)
                else:
                    missing.append(service_file)
        else:
            missing = critical_services

        return {
            "category": "Video Services",
            "total": len(critical_services),
            "existing": len(existing),
            "missing": len(missing),
            "missing_files": missing,
            "status": "PASS" if len(missing) == 0 else "WARNING",
            "score": int((len(existing) / len(critical_services)) * 100)
            if len(critical_services) > 0
            else 0,
        }

    def check_integrations(self) -> Dict[str, Any]:
        """Entegrasyon dosyalarını kontrol et"""
        integrations_dir = self.backend_path / "integrations"

        critical_integrations = [
            "youtube_service.py",
            "ebatv_service.py",
            "wikipedia_service.py",
        ]

        existing = []
        missing = []

        if integrations_dir.exists():
            for integration_file in critical_integrations:
                file_path = integrations_dir / integration_file
                if file_path.exists():
                    existing.append(integration_file)
                else:
                    missing.append(integration_file)
        else:
            missing = critical_integrations

        return {
            "category": "Integrations",
            "total": len(critical_integrations),
            "existing": len(existing),
            "missing": len(missing),
            "missing_files": missing,
            "status": "PASS" if len(missing) == 0 else "WARNING",
            "score": int((len(existing) / len(critical_integrations)) * 100)
            if len(critical_integrations) > 0
            else 0,
        }

    def check_environment_config(self) -> Dict[str, Any]:
        """Environment konfigürasyonunu kontrol et"""
        env_file = self.backend_path / ".env"

        critical_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET_KEY",
            "ENCRYPTION_KEY",
            "YOUTUBE_API_KEY",
        ]

        configured = []
        missing = []

        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                env_content = f.read()

            for var in critical_vars:
                if (
                    var in env_content
                    and not env_content.split(var)[1].split("\n")[0].strip() == "="
                ):
                    configured.append(var)
                else:
                    missing.append(var)
        else:
            missing = critical_vars

        return {
            "category": "Environment Config",
            "total": len(critical_vars),
            "configured": len(configured),
            "missing": len(missing),
            "missing_vars": missing,
            "status": "PASS" if len(missing) == 0 else "WARNING",
            "score": int((len(configured) / len(critical_vars)) * 100),
        }

    def check_test_coverage(self) -> Dict[str, Any]:
        """Test coverage durumunu kontrol et"""
        coverage_files = [
            self.backend_path / "coverage.json",
            self.backend_path / "coverage_week7_final.json",
        ]

        latest_coverage = None
        for coverage_file in coverage_files:
            if coverage_file.exists():
                try:
                    with open(coverage_file, "r", encoding="utf-8") as f:
                        latest_coverage = json.load(f)
                    break
                except:
                    continue

        if latest_coverage and "totals" in latest_coverage:
            coverage_percent = latest_coverage["totals"].get("percent_covered", 0)

            return {
                "category": "Test Coverage",
                "coverage_percent": coverage_percent,
                "status": "PASS" if coverage_percent >= 80 else "WARNING",
                "score": int(coverage_percent),
                "message": f"Test coverage: {coverage_percent:.1f}%",
            }
        else:
            return {
                "category": "Test Coverage",
                "coverage_percent": 0,
                "status": "WARNING",
                "score": 0,
                "message": "Coverage data not found",
            }

    def check_documentation(self) -> Dict[str, Any]:
        """Dokümantasyon dosyalarını kontrol et"""
        docs_dir = self.backend_path / "docs"

        critical_docs = [
            "API_DOCUMENTATION.md",
            "DEPLOYMENT_GUIDE.md",
            "SECURITY_GUIDE.md",
        ]

        existing = []
        missing = []

        if docs_dir.exists():
            for doc_file in critical_docs:
                file_path = docs_dir / doc_file
                if file_path.exists():
                    existing.append(doc_file)
                else:
                    missing.append(doc_file)
        else:
            missing = critical_docs

        return {
            "category": "Documentation",
            "total": len(critical_docs),
            "existing": len(existing),
            "missing": len(missing),
            "missing_files": missing,
            "status": "PASS" if len(missing) <= 1 else "WARNING",
            "score": int((len(existing) / len(critical_docs)) * 100)
            if len(critical_docs) > 0
            else 0,
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """Tüm kontrolleri çalıştır"""
        print("\n" + "=" * 80)
        print("🏥 PLATFORM SAĞLIK KONTROLÜ")
        print("=" * 80)
        print(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")

        checks = [
            self.check_api_files(),
            self.check_core_services(),
            self.check_services(),  # YENİ!
            self.check_ai_agents(),
            self.check_integrations(),
            self.check_environment_config(),
            self.check_test_coverage(),
            self.check_documentation(),
        ]

        # Genel skor hesapla
        total_score = sum(check["score"] for check in checks)
        avg_score = total_score / len(checks)

        # Durum emoji
        if avg_score >= 90:
            status_emoji = "🟢"
            status_text = "SAĞLIKLI"
        elif avg_score >= 80:
            status_emoji = "🟡"
            status_text = "UYARI"
        else:
            status_emoji = "🔴"
            status_text = "KRİTİK"

        # Sonuçları yazdır
        for check in checks:
            status_symbol = "✅" if check["status"] == "PASS" else "⚠️"
            print(f"{status_symbol} {check['category']}: {check['score']}%")

            if check.get("missing_files"):
                print(f"   Eksik dosyalar: {', '.join(check['missing_files'][:3])}")
                if len(check["missing_files"]) > 3:
                    print(f"   ... ve {len(check['missing_files']) - 3} dosya daha")

            if check.get("missing_vars"):
                print(f"   Eksik değişkenler: {', '.join(check['missing_vars'])}")

            if check.get("message"):
                print(f"   {check['message']}")

            print()

        print("=" * 80)
        print(f"{status_emoji} GENEL SAĞLIK SKORU: {avg_score:.1f}% - {status_text}")
        print("=" * 80)

        # Rapor oluştur
        report = {
            "timestamp": datetime.now().isoformat(),
            "health_score": avg_score,
            "status": status_text,
            "status_emoji": status_emoji,
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "passed": sum(1 for c in checks if c["status"] == "PASS"),
                "warnings": sum(1 for c in checks if c["status"] == "WARNING"),
                "failed": sum(1 for c in checks if c["status"] == "FAIL"),
            },
        }

        # Raporu kaydet
        report_dir = self.backend_path / "reports"
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"quick_health_check_{timestamp}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Rapor kaydedildi: {report_file}")

        # Aksiyon önerileri
        if avg_score < 90:
            print("\n📋 ÖNERİLEN AKSİYONLAR:")

            for check in checks:
                if check["status"] != "PASS":
                    print(f"\n{check['category']}:")

                    if check.get("missing_files"):
                        print(
                            f"  - Eksik dosyaları oluştur: {', '.join(check['missing_files'][:3])}"
                        )

                    if check.get("missing_vars"):
                        print(
                            f"  - Environment değişkenlerini ayarla: {', '.join(check['missing_vars'])}"
                        )

                    if check["category"] == "Test Coverage" and check["score"] < 80:
                        print(f"  - Test coverage'ı artır (hedef: 80%+)")

        return report


if __name__ == "__main__":
    checker = QuickHealthCheck()
    report = checker.run_all_checks()
