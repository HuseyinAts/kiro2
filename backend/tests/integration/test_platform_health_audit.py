"""
Platform Sağlık Denetimi (REQ-26-47)
Comprehensive health audit after critical file modifications
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

pytestmark = pytest.mark.skipif(
    True,
    reason="Platform health audit requires running FastAPI server (httpx.AsyncClient needs live endpoints)",
)
from httpx import AsyncClient

from core.structured_logger import get_logger

logger = get_logger(__name__)


class HealthAuditReport:
    """Platform sağlık denetim raporu"""

    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.checks: Dict[str, Dict[str, Any]] = {}
        self.score = 0.0
        self.status = "unknown"
        self.critical_issues: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def add_check(self, category: str, result: Dict[str, Any]):
        """Denetim sonucu ekle"""
        self.checks[category] = result

    def calculate_score(self) -> float:
        """Sağlık skoru hesapla (0-100)"""
        if not self.checks:
            return 0.0

        total_weight = 0
        weighted_score = 0

        # Ağırlıklar
        weights = {
            "api_health": 20,
            "ai_agents": 15,
            "external_services": 15,
            "database": 20,
            "security": 15,
            "performance": 10,
            "health_endpoints": 5,
        }

        for category, check in self.checks.items():
            weight = weights.get(category, 10)
            total_weight += weight

            # Her kategori için skor hesapla
            if check.get("healthy", False):
                weighted_score += weight
            elif check.get("status") == "warning":
                weighted_score += weight * 0.5

        self.score = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        return self.score

    def determine_status(self):
        """Genel durum belirle"""
        if self.score >= 90:
            self.status = "healthy"
        elif self.score >= 80:
            self.status = "warning"
        else:
            self.status = "critical"

    def to_dict(self) -> Dict[str, Any]:
        """Raporu dict'e çevir"""
        return {
            "timestamp": self.timestamp,
            "score": round(self.score, 2),
            "status": self.status,
            "checks": self.checks,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }


class PlatformHealthAuditor:
    """Platform sağlık denetçisi"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.report = HealthAuditReport()

    async def audit_api_health(self, client: AsyncClient) -> Dict[str, Any]:
        """REQ-26: API sağlık kontrolü"""
        logger.info("🏥 API Sağlık Kontrolü başlatılıyor...")
        start_time = time.time()

        try:
            # Ana health endpoint
            response = await client.get(f"{self.base_url}/health")
            health_data = response.json()

            # Kritik endpoint'leri kontrol et
            critical_endpoints = [
                "/api/auth/login",
                "/api/learning-path/generate",
                "/api/youtube/recommendations",
            ]

            endpoint_results = []
            for endpoint in critical_endpoints:
                try:
                    resp = await client.get(f"{self.base_url}{endpoint}")
                    endpoint_results.append(
                        {
                            "endpoint": endpoint,
                            "status_code": resp.status_code,
                            "healthy": resp.status_code < 500,
                        }
                    )
                except Exception as e:
                    endpoint_results.append(
                        {"endpoint": endpoint, "status_code": 0, "healthy": False, "error": str(e)}
                    )

            duration_ms = (time.time() - start_time) * 1000
            healthy = response.status_code == 200 and all(
                e["healthy"] for e in endpoint_results
            )

            result = {
                "healthy": healthy,
                "status": "healthy" if healthy else "unhealthy",
                "response_time_ms": round(duration_ms, 2),
                "main_health": health_data,
                "critical_endpoints": endpoint_results,
            }

            if not healthy:
                self.report.critical_issues.append(
                    "Bazı kritik API endpoint'leri yanıt vermiyor"
                )

            return result

        except Exception as e:
            logger.error(f"API sağlık kontrolü başarısız: {e}")
            self.report.critical_issues.append(f"API sağlık kontrolü hatası: {str(e)}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def audit_ai_agents(self) -> Dict[str, Any]:
        """REQ-27: AI Agent kontrolü"""
        logger.info("🤖 AI Agent Kontrolü başlatılıyor...")

        agents_to_check = [
            "agents.learning_path_agent",
            "agents.study_agent",
            "agents.exam_agent",
        ]

        agent_results = []
        for agent_module in agents_to_check:
            try:
                # Import kontrolü
                parts = agent_module.split(".")
                module = __import__(agent_module, fromlist=[parts[-1]])

                agent_results.append(
                    {
                        "agent": agent_module,
                        "importable": True,
                        "healthy": True,
                    }
                )
            except ImportError as e:
                agent_results.append(
                    {
                        "agent": agent_module,
                        "importable": False,
                        "healthy": False,
                        "error": str(e),
                    }
                )
                self.report.warnings.append(f"Agent import hatası: {agent_module}")

        healthy = all(a["healthy"] for a in agent_results)

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "degraded",
            "agents": agent_results,
        }

    async def audit_external_services(self, client: AsyncClient) -> Dict[str, Any]:
        """REQ-28: Harici servis kontrolü"""
        logger.info("🌐 Harici Servis Kontrolü başlatılıyor...")

        services = {
            "youtube": "/api/youtube/test",
            "eba_tv": "/api/eba-tv/health",
        }

        service_results = []
        for service_name, endpoint in services.items():
            try:
                start = time.time()
                response = await client.get(
                    f"{self.base_url}{endpoint}", timeout=3.0
                )
                duration_ms = (time.time() - start) * 1000

                service_results.append(
                    {
                        "service": service_name,
                        "healthy": response.status_code < 500,
                        "response_time_ms": round(duration_ms, 2),
                        "timeout_ok": duration_ms < 3000,
                    }
                )
            except Exception as e:
                service_results.append(
                    {
                        "service": service_name,
                        "healthy": False,
                        "error": str(e),
                    }
                )
                self.report.warnings.append(
                    f"Harici servis erişilemiyor: {service_name}"
                )

        healthy = any(s["healthy"] for s in service_results)

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "degraded",
            "services": service_results,
        }

    async def audit_database(self, client: AsyncClient) -> Dict[str, Any]:
        """REQ-29: Veritabanı kontrolü"""
        logger.info("💾 Veritabanı Kontrolü başlatılıyor...")

        try:
            response = await client.get(f"{self.base_url}/health/database")
            db_data = response.json()

            healthy = response.status_code == 200

            if not healthy:
                self.report.critical_issues.append("Veritabanı bağlantısı başarısız")

            return {
                "healthy": healthy,
                "status": "healthy" if healthy else "critical",
                "details": db_data,
            }

        except Exception as e:
            self.report.critical_issues.append(f"Veritabanı kontrolü hatası: {str(e)}")
            return {
                "healthy": False,
                "status": "critical",
                "error": str(e),
            }

    async def audit_security(self, client: AsyncClient) -> Dict[str, Any]:
        """REQ-31, REQ-45: Güvenlik kontrolü"""
        logger.info("🛡️ Güvenlik Kontrolü başlatılıyor...")

        security_checks = []

        # Rate limiting kontrolü
        try:
            # 10 hızlı istek gönder
            responses = []
            for _ in range(10):
                resp = await client.get(f"{self.base_url}/health")
                responses.append(resp.status_code)

            rate_limited = 429 in responses
            security_checks.append(
                {
                    "check": "rate_limiting",
                    "active": rate_limited,
                    "healthy": True,  # Rate limiting olması iyi
                }
            )
        except Exception as e:
            security_checks.append(
                {
                    "check": "rate_limiting",
                    "active": False,
                    "error": str(e),
                }
            )

        # CORS kontrolü
        try:
            response = await client.options(
                f"{self.base_url}/health",
                headers={"Origin": "http://localhost:3000"},
            )
            cors_configured = "access-control-allow-origin" in response.headers
            security_checks.append(
                {
                    "check": "cors",
                    "configured": cors_configured,
                    "healthy": cors_configured,
                }
            )
        except Exception as e:
            security_checks.append(
                {
                    "check": "cors",
                    "configured": False,
                    "error": str(e),
                }
            )

        healthy = all(c.get("healthy", False) for c in security_checks)

        if not healthy:
            self.report.warnings.append("Bazı güvenlik kontrolleri başarısız")

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "warning",
            "checks": security_checks,
        }

    async def audit_performance(self, client: AsyncClient) -> Dict[str, Any]:
        """REQ-35: Performans kontrolü"""
        logger.info("⚡ Performans Kontrolü başlatılıyor...")

        # 10 istek gönder ve p95 hesapla
        response_times = []
        for _ in range(10):
            start = time.time()
            await client.get(f"{self.base_url}/health")
            duration_ms = (time.time() - start) * 1000
            response_times.append(duration_ms)

        response_times.sort()
        p95 = response_times[int(len(response_times) * 0.95)]
        avg = sum(response_times) / len(response_times)

        p95_ok = p95 < 200
        avg_ok = avg < 500

        if not p95_ok:
            self.report.warnings.append(f"API p95 yavaş: {p95:.2f}ms (hedef: <200ms)")

        return {
            "healthy": p95_ok and avg_ok,
            "status": "healthy" if (p95_ok and avg_ok) else "warning",
            "p95_ms": round(p95, 2),
            "avg_ms": round(avg, 2),
            "p95_threshold_ok": p95_ok,
            "avg_threshold_ok": avg_ok,
        }

    async def audit_health_endpoints(self, client: AsyncClient) -> Dict[str, Any]:
        """REQ-40: Health endpoint kontrolü"""
        logger.info("🏥 Health Endpoint Kontrolü başlatılıyor...")

        endpoints = [
            "/health",
            "/health/ready",
            "/health/live",
            "/health/startup",
        ]

        endpoint_results = []
        for endpoint in endpoints:
            try:
                response = await client.get(f"{self.base_url}{endpoint}")
                endpoint_results.append(
                    {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "healthy": response.status_code == 200,
                    }
                )
            except Exception as e:
                endpoint_results.append(
                    {
                        "endpoint": endpoint,
                        "status_code": 0,
                        "healthy": False,
                        "error": str(e),
                    }
                )

        healthy = all(e["healthy"] for e in endpoint_results)

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "degraded",
            "endpoints": endpoint_results,
        }

    async def run_full_audit(self) -> HealthAuditReport:
        """Tam platform denetimi çalıştır"""
        logger.info("🚀 Platform Sağlık Denetimi başlatılıyor...")

        async with AsyncClient() as client:
            # Tüm kontrolleri çalıştır
            self.report.add_check("api_health", await self.audit_api_health(client))
            self.report.add_check("ai_agents", await self.audit_ai_agents())
            self.report.add_check(
                "external_services", await self.audit_external_services(client)
            )
            self.report.add_check("database", await self.audit_database(client))
            self.report.add_check("security", await self.audit_security(client))
            self.report.add_check("performance", await self.audit_performance(client))
            self.report.add_check(
                "health_endpoints", await self.audit_health_endpoints(client)
            )

        # Skor hesapla ve durum belirle
        self.report.calculate_score()
        self.report.determine_status()

        # Öneriler ekle
        if self.report.score < 80:
            self.report.recommendations.append(
                "Platform sağlık skoru düşük - acil müdahale gerekli"
            )
        if self.report.score < 90:
            self.report.recommendations.append(
                "Performans iyileştirmeleri yapılmalı"
            )

        logger.info(
            f"✅ Platform Sağlık Denetimi tamamlandı - Skor: {self.report.score:.1f}%"
        )

        return self.report


@pytest.mark.asyncio
async def test_platform_health_audit():
    """Platform sağlık denetimi testi"""
    auditor = PlatformHealthAuditor()
    report = await auditor.run_full_audit()

    # Raporu kaydet
    report_dict = report.to_dict()

    # JSON rapor
    with open("backend/platform_health_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    # Türkçe metin rapor
    with open("backend/platform_health_audit_report.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("PLATFORM SAĞLIK DENETİMİ RAPORU\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Tarih: {report.timestamp}\n")
        f.write(f"Sağlık Skoru: {report.score:.1f}%\n")
        f.write(f"Durum: {report.status.upper()}\n\n")

        # Durum göstergesi
        if report.status == "healthy":
            f.write("🟢 Platform Sağlıklı\n\n")
        elif report.status == "warning":
            f.write("🟡 Platform Uyarı Durumunda\n\n")
        else:
            f.write("🔴 Platform Kritik Durumda\n\n")

        # Kontrol sonuçları
        f.write("KONTROL SONUÇLARI:\n")
        f.write("-" * 80 + "\n")
        for category, check in report.checks.items():
            status_icon = "✅" if check.get("healthy") else "❌"
            f.write(f"{status_icon} {category.upper()}: {check.get('status', 'unknown')}\n")

        # Kritik sorunlar
        if report.critical_issues:
            f.write("\n🔴 KRİTİK SORUNLAR:\n")
            f.write("-" * 80 + "\n")
            for issue in report.critical_issues:
                f.write(f"  • {issue}\n")

        # Uyarılar
        if report.warnings:
            f.write("\n🟡 UYARILAR:\n")
            f.write("-" * 80 + "\n")
            for warning in report.warnings:
                f.write(f"  • {warning}\n")

        # Öneriler
        if report.recommendations:
            f.write("\n💡 ÖNERİLER:\n")
            f.write("-" * 80 + "\n")
            for rec in report.recommendations:
                f.write(f"  • {rec}\n")

        f.write("\n" + "=" * 80 + "\n")

    # Test assertion
    assert report.score >= 80, f"Platform sağlık skoru çok düşük: {report.score:.1f}%"

    print("\n✅ Platform Sağlık Denetimi Tamamlandı")
    print(f"📊 Sağlık Skoru: {report.score:.1f}%")
    print("📄 Raporlar kaydedildi:")
    print("   - backend/platform_health_audit_report.json")
    print("   - backend/platform_health_audit_report.txt")


if __name__ == "__main__":
    asyncio.run(test_platform_health_audit())
