"""
Hızlı Platform Sağlık Denetimi
Backend servisi çalışmadan yapılabilecek kontroller
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Backend path ekle
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


class QuickHealthAuditor:
    """Hızlı sağlık denetçisi"""

    def __init__(self):
        self.report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "score": 0.0,
            "status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
        }

    def check_critical_files(self) -> Dict[str, Any]:
        """Kritik dosyaların varlığını kontrol et"""
        print("📁 Kritik dosya kontrolü...")

        critical_files = [
            "backend/main.py",
            "backend/core/database.py",
            "backend/core/cache.py",
            "backend/api/health.py",
            "backend/services/health_check_service.py",
            ".env",
        ]

        results = []
        for file_path in critical_files:
            exists = os.path.exists(file_path)
            results.append({"file": file_path, "exists": exists})

            if not exists and file_path != ".env":
                self.report["critical_issues"].append(f"Kritik dosya eksik: {file_path}")

        healthy = all(r["exists"] for r in results if r["file"] != ".env")

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "critical",
            "files": results,
        }

    def check_sensitive_data_filter(self) -> Dict[str, Any]:
        """Hassas veri filtreleme ayarını kontrol et"""
        print("🔒 Hassas veri filtreleme kontrolü...")

        try:
            with open("backend/main.py", "r", encoding="utf-8") as f:
                content = f.read()

            # Hassas veri filtreleme satırını bul
            if "setup_global_sensitive_data_filter" in content:
                if "redact_email=False" in content or "redact_phone=False" in content:
                    self.report["warnings"].append(
                        "⚠️ KVKK UYARISI: Hassas veri filtreleme devre dışı! "
                        "Production ortamında email ve telefon redaction aktif olmalı."
                    )
                    self.report["recommendations"].append(
                        "setup_global_sensitive_data_filter(redact_email=True, redact_phone=True) "
                        "olarak değiştirin"
                    )
                    return {
                        "healthy": False,
                        "status": "warning",
                        "redact_email": False,
                        "redact_phone": False,
                        "message": "Hassas veri filtreleme devre dışı",
                    }
                else:
                    return {
                        "healthy": True,
                        "status": "healthy",
                        "redact_email": True,
                        "redact_phone": True,
                        "message": "Hassas veri filtreleme aktif",
                    }
            else:
                self.report["warnings"].append(
                    "Hassas veri filtreleme yapılandırması bulunamadı"
                )
                return {
                    "healthy": False,
                    "status": "warning",
                    "message": "Filtreleme yapılandırması bulunamadı",
                }

        except Exception as e:
            self.report["critical_issues"].append(
                f"Hassas veri filtreleme kontrolü hatası: {str(e)}"
            )
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    def check_security_middleware(self) -> Dict[str, Any]:
        """Güvenlik middleware kontrolü"""
        print("🛡️ Güvenlik middleware kontrolü...")

        try:
            with open("backend/main.py", "r", encoding="utf-8") as f:
                content = f.read()

            security_features = {
                "csrf_protection": "CSRFProtectionMiddleware" in content,
                "rate_limiting": "RateLimitMiddleware" in content,
                "cors": "CORSMiddleware" in content,
                "security_headers": "ComprehensiveSecurityMiddleware" in content,
                "ddos_protection": "ddos_protection" in content,
            }

            active_count = sum(1 for v in security_features.values() if v)
            total_count = len(security_features)

            healthy = active_count >= 4  # En az 4/5 aktif olmalı

            if not healthy:
                self.report["warnings"].append(
                    f"Güvenlik middleware'leri eksik: {active_count}/{total_count} aktif"
                )

            return {
                "healthy": healthy,
                "status": "healthy" if healthy else "warning",
                "features": security_features,
                "active_count": active_count,
                "total_count": total_count,
            }

        except Exception as e:
            self.report["critical_issues"].append(
                f"Güvenlik middleware kontrolü hatası: {str(e)}"
            )
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    def check_api_routers(self) -> Dict[str, Any]:
        """API router'ların yüklendiğini kontrol et"""
        print("🔌 API Router kontrolü...")

        try:
            with open("backend/main.py", "r", encoding="utf-8") as f:
                content = f.read()

            routers = {
                "health": "health_router" in content,
                "auth": "auth_router" in content,
                "2fa": "two_factor_auth_router" in content,
                "kvkk_consent": "kvkk_consent_router" in content,
                "kvkk_privacy": "kvkk_privacy_router" in content,
                "rate_limit": "rate_limit_router" in content,
            }

            active_count = sum(1 for v in routers.values() if v)
            total_count = len(routers)

            healthy = active_count >= 5  # En az 5/6 aktif olmalı

            if not healthy:
                self.report["warnings"].append(
                    f"API router'ları eksik: {active_count}/{total_count} yüklü"
                )

            return {
                "healthy": healthy,
                "status": "healthy" if healthy else "warning",
                "routers": routers,
                "active_count": active_count,
                "total_count": total_count,
            }

        except Exception as e:
            self.report["critical_issues"].append(
                f"API router kontrolü hatası: {str(e)}"
            )
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    def check_environment_config(self) -> Dict[str, Any]:
        """Environment yapılandırması kontrolü"""
        print("⚙️ Environment yapılandırma kontrolü...")

        env_file = ".env"
        if not os.path.exists(env_file):
            env_file = "backend/.env"

        if not os.path.exists(env_file):
            self.report["warnings"].append(".env dosyası bulunamadı")
            return {
                "healthy": False,
                "status": "warning",
                "message": ".env dosyası bulunamadı",
            }

        try:
            with open(env_file, "r", encoding="utf-8") as f:
                content = f.read()

            required_vars = [
                "DATABASE_URL",
                "SECRET_KEY",
                "ENVIRONMENT",
            ]

            found_vars = {}
            for var in required_vars:
                found_vars[var] = var in content

            missing = [var for var, found in found_vars.items() if not found]

            if missing:
                self.report["warnings"].append(
                    f"Eksik environment değişkenleri: {', '.join(missing)}"
                )

            healthy = len(missing) == 0

            return {
                "healthy": healthy,
                "status": "healthy" if healthy else "warning",
                "required_vars": found_vars,
                "missing_vars": missing,
            }

        except Exception as e:
            self.report["warnings"].append(f"Environment kontrolü hatası: {str(e)}")
            return {
                "healthy": False,
                "status": "warning",
                "error": str(e),
            }

    def check_database_files(self) -> Dict[str, Any]:
        """Veritabanı dosyalarını kontrol et"""
        print("💾 Veritabanı dosya kontrolü...")

        db_files = [
            "backend/turkiye_sinav.db",
            "backend/kiro2.db",
            "turkiye_sinav.db",
            "kiro2.db",
        ]

        found_dbs = [db for db in db_files if os.path.exists(db)]

        if not found_dbs:
            self.report["warnings"].append(
                "SQLite veritabanı dosyası bulunamadı (PostgreSQL kullanılıyor olabilir)"
            )

        return {
            "healthy": True,  # Non-critical
            "status": "info",
            "found_databases": found_dbs,
            "message": f"{len(found_dbs)} veritabanı dosyası bulundu"
            if found_dbs
            else "SQLite DB bulunamadı",
        }

    def check_agent_files(self) -> Dict[str, Any]:
        """AI Agent dosyalarını kontrol et"""
        print("🤖 AI Agent dosya kontrolü...")

        agent_files = [
            "backend/agents/__init__.py",
            "backend/agents/learning_path_agent.py",
            "backend/agents/study_agent.py",
            "backend/agents/exam_agent.py",
        ]

        results = []
        for file_path in agent_files:
            exists = os.path.exists(file_path)
            results.append({"file": file_path, "exists": exists})

            if not exists:
                self.report["warnings"].append(f"Agent dosyası eksik: {file_path}")

        healthy = all(r["exists"] for r in results)

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "warning",
            "agents": results,
        }

    def calculate_score(self):
        """Sağlık skoru hesapla"""
        weights = {
            "critical_files": 25,
            "sensitive_data_filter": 15,
            "security_middleware": 20,
            "api_routers": 15,
            "environment_config": 15,
            "database_files": 5,
            "agent_files": 5,
        }

        total_weight = sum(weights.values())
        weighted_score = 0

        for category, check in self.report["checks"].items():
            weight = weights.get(category, 10)

            if check.get("healthy", False):
                weighted_score += weight
            elif check.get("status") == "warning":
                weighted_score += weight * 0.5
            elif check.get("status") == "info":
                weighted_score += weight  # Info checks don't reduce score

        self.report["score"] = (weighted_score / total_weight * 100) if total_weight > 0 else 0

    def determine_status(self):
        """Genel durum belirle"""
        if self.report["score"] >= 90:
            self.report["status"] = "healthy"
        elif self.report["score"] >= 80:
            self.report["status"] = "warning"
        else:
            self.report["status"] = "critical"

    def run_audit(self):
        """Denetimi çalıştır"""
        print("\n" + "=" * 80)
        print("🏥 PLATFORM SAĞLIK DENETİMİ")
        print("=" * 80 + "\n")

        # Tüm kontrolleri çalıştır
        self.report["checks"]["critical_files"] = self.check_critical_files()
        self.report["checks"]["sensitive_data_filter"] = (
            self.check_sensitive_data_filter()
        )
        self.report["checks"]["security_middleware"] = self.check_security_middleware()
        self.report["checks"]["api_routers"] = self.check_api_routers()
        self.report["checks"]["environment_config"] = self.check_environment_config()
        self.report["checks"]["database_files"] = self.check_database_files()
        self.report["checks"]["agent_files"] = self.check_agent_files()

        # Skor hesapla
        self.calculate_score()
        self.determine_status()

        # Öneriler ekle
        if self.report["score"] < 80:
            self.report["recommendations"].append(
                "Platform sağlık skoru düşük - acil müdahale gerekli"
            )
        if self.report["score"] < 90:
            self.report["recommendations"].append(
                "Güvenlik ve yapılandırma iyileştirmeleri yapılmalı"
            )

        # Raporu kaydet
        self.save_report()

        # Özet yazdır
        self.print_summary()

        return self.report

    def save_report(self):
        """Raporu kaydet"""
        # JSON rapor
        json_path = "backend/platform_health_audit_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        # Türkçe metin rapor
        txt_path = "backend/platform_health_audit_report.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("PLATFORM SAĞLIK DENETİMİ RAPORU\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Tarih: {self.report['timestamp']}\n")
            f.write(f"Sağlık Skoru: {self.report['score']:.1f}%\n")
            f.write(f"Durum: {self.report['status'].upper()}\n\n")

            # Durum göstergesi
            if self.report["status"] == "healthy":
                f.write("🟢 Platform Sağlıklı\n\n")
            elif self.report["status"] == "warning":
                f.write("🟡 Platform Uyarı Durumunda\n\n")
            else:
                f.write("🔴 Platform Kritik Durumda\n\n")

            # Kontrol sonuçları
            f.write("KONTROL SONUÇLARI:\n")
            f.write("-" * 80 + "\n")
            for category, check in self.report["checks"].items():
                status_icon = "✅" if check.get("healthy") else "❌"
                if check.get("status") == "info":
                    status_icon = "ℹ️"
                f.write(
                    f"{status_icon} {category.upper()}: {check.get('status', 'unknown')}\n"
                )

            # Kritik sorunlar
            if self.report["critical_issues"]:
                f.write("\n🔴 KRİTİK SORUNLAR:\n")
                f.write("-" * 80 + "\n")
                for issue in self.report["critical_issues"]:
                    f.write(f"  • {issue}\n")

            # Uyarılar
            if self.report["warnings"]:
                f.write("\n🟡 UYARILAR:\n")
                f.write("-" * 80 + "\n")
                for warning in self.report["warnings"]:
                    f.write(f"  • {warning}\n")

            # Öneriler
            if self.report["recommendations"]:
                f.write("\n💡 ÖNERİLER:\n")
                f.write("-" * 80 + "\n")
                for rec in self.report["recommendations"]:
                    f.write(f"  • {rec}\n")

            f.write("\n" + "=" * 80 + "\n")

        print(f"\n📄 Raporlar kaydedildi:")
        print(f"   - {json_path}")
        print(f"   - {txt_path}")

    def print_summary(self):
        """Özet yazdır"""
        print("\n" + "=" * 80)
        print("📊 SAĞLIK DENETİMİ ÖZETİ")
        print("=" * 80)

        # Skor ve durum
        score = self.report["score"]
        status = self.report["status"]

        if status == "healthy":
            status_icon = "🟢"
            status_text = "SAĞLIKLI"
        elif status == "warning":
            status_icon = "🟡"
            status_text = "UYARI"
        else:
            status_icon = "🔴"
            status_text = "KRİTİK"

        print(f"\n{status_icon} Durum: {status_text}")
        print(f"📈 Sağlık Skoru: {score:.1f}%")

        # Kontrol özeti
        print(f"\n📋 Kontrol Sonuçları:")
        healthy_count = sum(
            1 for c in self.report["checks"].values() if c.get("healthy", False)
        )
        total_count = len(self.report["checks"])
        print(f"   ✅ Başarılı: {healthy_count}/{total_count}")

        # Sorunlar
        if self.report["critical_issues"]:
            print(f"\n🔴 Kritik Sorunlar: {len(self.report['critical_issues'])}")
            for issue in self.report["critical_issues"][:3]:
                print(f"   • {issue}")

        if self.report["warnings"]:
            print(f"\n🟡 Uyarılar: {len(self.report['warnings'])}")
            for warning in self.report["warnings"][:3]:
                print(f"   • {warning}")

        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    auditor = QuickHealthAuditor()
    report = auditor.run_audit()

    # Exit code
    if report["status"] == "critical":
        sys.exit(1)
    elif report["status"] == "warning":
        sys.exit(0)  # Warning is acceptable
    else:
        sys.exit(0)
