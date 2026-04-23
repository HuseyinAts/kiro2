"""
Video API Diagnostic ve Fix Script
Task 1: Backend Servis Durumunu Doğrula ve İlk Düzeltmeleri Yap
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VideoAPIDiagnostic:
    """Video API diagnostic ve fix tool"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "fixes_applied": [],
            "recommendations": [],
        }
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3001"

    async def run_all_checks(self):
        """Tüm kontrolleri çalıştır"""
        logger.info("=" * 60)
        logger.info("VIDEO API DİAGNOSTİC BAŞLATILIYOR")
        logger.info("=" * 60)

        # 1. Backend servis kontrolü
        await self.check_backend_service()

        # 2. Test endpoint kontrolü
        await self.check_test_endpoint()

        # 3. Recommendations endpoint kontrolü
        await self.check_recommendations_endpoint()

        # 4. CORS kontrolü
        await self.check_cors_configuration()

        # 5. Frontend konfigürasyon kontrolü
        self.check_frontend_configuration()

        # 6. Backend logs kontrolü
        self.check_backend_logs()

        # Sonuçları raporla
        self.generate_report()

        return self.results

    async def check_backend_service(self):
        """Backend servisinin çalışıp çalışmadığını kontrol et"""
        logger.info("\n[1/6] Backend Servis Kontrolü")
        logger.info("-" * 60)

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session, session.get(
                f"{self.backend_url}/health", timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Backend servisi çalışıyor")
                    logger.info(f"   Status: {data.get('status', 'unknown')}")
                    self.results["checks"]["backend_service"] = {
                        "status": "OK",
                        "details": data,
                    }
                else:
                    logger.error(f"❌ Backend servisi hata döndü: {response.status}")
                    self.results["checks"]["backend_service"] = {
                        "status": "ERROR",
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            logger.error(f"❌ Backend servisine bağlanılamadı: {e}")
            self.results["checks"]["backend_service"] = {
                "status": "ERROR",
                "error": str(e),
            }
            self.results["recommendations"].append(
                "Backend servisini başlatın: cd backend && python main.py"
            )

    async def check_test_endpoint(self):
        """Test endpoint'ini kontrol et"""
        logger.info("\n[2/6] Test Endpoint Kontrolü")
        logger.info("-" * 60)

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session, session.get(
                f"{self.backend_url}/api/youtube/test", timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Test endpoint çalışıyor")
                    logger.info(f"   Response: {data}")
                    self.results["checks"]["test_endpoint"] = {
                        "status": "OK",
                        "response": data,
                    }
                else:
                    logger.error(f"❌ Test endpoint hata döndü: {response.status}")
                    self.results["checks"]["test_endpoint"] = {
                        "status": "ERROR",
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            logger.error(f"❌ Test endpoint'e erişilemedi: {e}")
            self.results["checks"]["test_endpoint"] = {
                "status": "ERROR",
                "error": str(e),
            }

    async def check_recommendations_endpoint(self):
        """Recommendations endpoint'ini test et"""
        logger.info("\n[3/6] Recommendations Endpoint Kontrolü")
        logger.info("-" * 60)

        try:
            import aiohttp

            # Test payload
            test_payload = {
                "goals": ["TYT"],
                "currentLevel": {"matematik": 5, "fizik": 4},
                "learningStyle": "visual",
                "preferences": {},
            }

            logger.info(f"   Test payload: {json.dumps(test_payload, indent=2)}")

            async with aiohttp.ClientSession() as session, session.post(
                f"{self.backend_url}/api/youtube/recommendations",
                json=test_payload,
                timeout=30,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    video_count = sum(len(rec.get("videos", [])) for rec in data)
                    logger.info("✅ Recommendations endpoint çalışıyor")
                    logger.info(f"   Toplam video: {video_count}")
                    self.results["checks"]["recommendations_endpoint"] = {
                        "status": "OK",
                        "video_count": video_count,
                        "response_sample": data[:1] if data else [],
                    }
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Recommendations endpoint hata döndü: {response.status}"
                    )
                    logger.error(f"   Error: {error_text}")
                    self.results["checks"]["recommendations_endpoint"] = {
                        "status": "ERROR",
                        "error": f"HTTP {response.status}",
                        "details": error_text,
                    }
        except TimeoutError:
            logger.error("❌ Recommendations endpoint timeout (30s)")
            self.results["checks"]["recommendations_endpoint"] = {
                "status": "ERROR",
                "error": "Timeout after 30 seconds",
            }
            self.results["recommendations"].append(
                "Recommendations endpoint çok yavaş - performance optimization gerekli"
            )
        except Exception as e:
            logger.error(f"❌ Recommendations endpoint hatası: {e}")
            self.results["checks"]["recommendations_endpoint"] = {
                "status": "ERROR",
                "error": str(e),
            }

    async def check_cors_configuration(self):
        """CORS konfigürasyonunu kontrol et"""
        logger.info("\n[4/6] CORS Konfigürasyon Kontrolü")
        logger.info("-" * 60)

        try:
            import aiohttp

            # Preflight request simülasyonu
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }

            async with aiohttp.ClientSession() as session:
                async with session.options(
                    f"{self.backend_url}/api/youtube/recommendations",
                    headers=headers,
                    timeout=5,
                ) as response:
                    cors_headers = {
                        "Access-Control-Allow-Origin": response.headers.get(
                            "Access-Control-Allow-Origin"
                        ),
                        "Access-Control-Allow-Methods": response.headers.get(
                            "Access-Control-Allow-Methods"
                        ),
                        "Access-Control-Allow-Headers": response.headers.get(
                            "Access-Control-Allow-Headers"
                        ),
                        "Access-Control-Allow-Credentials": response.headers.get(
                            "Access-Control-Allow-Credentials"
                        ),
                    }

                    logger.info("✅ CORS headers:")
                    for key, value in cors_headers.items():
                        logger.info(f"   {key}: {value}")

                    # Frontend origin kontrolü
                    allowed_origin = cors_headers.get("Access-Control-Allow-Origin")
                    if allowed_origin and (
                        allowed_origin == "*" or self.frontend_url in allowed_origin
                    ):
                        logger.info(
                            f"✅ Frontend origin ({self.frontend_url}) whitelist'te"
                        )
                        self.results["checks"]["cors"] = {
                            "status": "OK",
                            "headers": cors_headers,
                        }
                    else:
                        logger.warning(
                            f"⚠️  Frontend origin ({self.frontend_url}) whitelist'te değil"
                        )
                        self.results["checks"]["cors"] = {
                            "status": "WARNING",
                            "headers": cors_headers,
                            "issue": f"Frontend origin {self.frontend_url} not in whitelist",
                        }
                        self.results["recommendations"].append(
                            f"Backend main.py'de CORS origins'e {self.frontend_url} ekleyin"
                        )
        except Exception as e:
            logger.error(f"❌ CORS kontrolü hatası: {e}")
            self.results["checks"]["cors"] = {"status": "ERROR", "error": str(e)}

    def check_frontend_configuration(self):
        """Frontend konfigürasyonunu kontrol et"""
        logger.info("\n[5/6] Frontend Konfigürasyon Kontrolü")
        logger.info("-" * 60)

        try:
            # main.tsx dosyasını oku
            main_tsx_path = Path("frontend/src/main.tsx")

            if not main_tsx_path.exists():
                logger.error("❌ frontend/src/main.tsx bulunamadı")
                self.results["checks"]["frontend_config"] = {
                    "status": "ERROR",
                    "error": "main.tsx not found",
                }
                return

            with open(main_tsx_path, encoding="utf-8") as f:
                content = f.read()

            # API_BASE_URL kontrolü
            if "API_BASE_URL" in content:
                logger.info("✅ API_BASE_URL tanımlı")

                # URL değerini bul
                import re

                url_match = re.search(
                    r"API_BASE_URL\s*=\s*['\"]([^'\"]+)['\"]", content
                )
                if url_match:
                    api_url = url_match.group(1)
                    logger.info(f"   Configured URL: {api_url}")

                    if (
                        api_url == self.backend_url
                        or "localhost:8000" in api_url
                        or "localhost:8001" in api_url
                    ):
                        logger.info("✅ API_BASE_URL doğru yapılandırılmış")
                        self.results["checks"]["frontend_config"] = {
                            "status": "OK",
                            "api_url": api_url,
                        }
                    else:
                        logger.warning(f"⚠️  API_BASE_URL yanlış: {api_url}")
                        self.results["checks"]["frontend_config"] = {
                            "status": "WARNING",
                            "api_url": api_url,
                            "expected": self.backend_url,
                        }
                        self.results["recommendations"].append(
                            f"Frontend main.tsx'de API_BASE_URL'i {self.backend_url} olarak güncelleyin"
                        )
            else:
                logger.error("❌ API_BASE_URL tanımlı değil")
                self.results["checks"]["frontend_config"] = {
                    "status": "ERROR",
                    "error": "API_BASE_URL not defined",
                }
                self.results["recommendations"].append(
                    "Frontend main.tsx'de API_BASE_URL tanımlayın"
                )

            # Timeout kontrolü
            if "timeout" in content.lower():
                timeout_match = re.search(r"setTimeout.*?(\d+)", content)
                if timeout_match:
                    timeout_ms = int(timeout_match.group(1))
                    logger.info(f"   Timeout: {timeout_ms}ms")

                    if timeout_ms < 20000:
                        logger.warning(
                            f"⚠️  Timeout çok kısa: {timeout_ms}ms (önerilen: 20000ms)"
                        )
                        self.results["recommendations"].append(
                            "Frontend timeout'u 20 saniyeye çıkarın"
                        )

        except Exception as e:
            logger.error(f"❌ Frontend konfigürasyon kontrolü hatası: {e}")
            self.results["checks"]["frontend_config"] = {
                "status": "ERROR",
                "error": str(e),
            }

    def check_backend_logs(self):
        """Backend loglarını kontrol et"""
        logger.info("\n[6/6] Backend Logs Kontrolü")
        logger.info("-" * 60)

        try:
            log_file = Path("backend/app.log")

            if not log_file.exists():
                logger.warning("⚠️  backend/app.log bulunamadı")
                self.results["checks"]["backend_logs"] = {
                    "status": "WARNING",
                    "message": "Log file not found",
                }
                return

            # Son 50 satırı oku
            with open(log_file, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines

            # Error ve warning sayısı
            errors = [line for line in recent_lines if "ERROR" in line]
            warnings = [
                line for line in recent_lines if "WARNING" in line or "WARN" in line
            ]

            logger.info(
                f"   Son 50 satırda {len(errors)} error, {len(warnings)} warning"
            )

            # YouTube API ile ilgili loglar
            youtube_logs = [
                line
                for line in recent_lines
                if "youtube" in line.lower() or "video" in line.lower()
            ]

            if youtube_logs:
                logger.info(
                    f"   YouTube/Video ile ilgili {len(youtube_logs)} log bulundu"
                )
                logger.info("   Son 3 YouTube log:")
                for log in youtube_logs[-3:]:
                    logger.info(f"     {log.strip()}")

            self.results["checks"]["backend_logs"] = {
                "status": "OK",
                "error_count": len(errors),
                "warning_count": len(warnings),
                "youtube_log_count": len(youtube_logs),
                "recent_errors": [e.strip() for e in errors[-3:]],
            }

        except Exception as e:
            logger.error(f"❌ Backend logs kontrolü hatası: {e}")
            self.results["checks"]["backend_logs"] = {
                "status": "ERROR",
                "error": str(e),
            }

    def generate_report(self):
        """Diagnostic raporu oluştur"""
        logger.info("\n" + "=" * 60)
        logger.info("DİAGNOSTİC RAPORU")
        logger.info("=" * 60)

        # Özet
        total_checks = len(self.results["checks"])
        ok_checks = sum(
            1
            for check in self.results["checks"].values()
            if check.get("status") == "OK"
        )
        error_checks = sum(
            1
            for check in self.results["checks"].values()
            if check.get("status") == "ERROR"
        )
        warning_checks = sum(
            1
            for check in self.results["checks"].values()
            if check.get("status") == "WARNING"
        )

        logger.info(f"\nToplam Kontrol: {total_checks}")
        logger.info(f"✅ Başarılı: {ok_checks}")
        logger.info(f"⚠️  Uyarı: {warning_checks}")
        logger.info(f"❌ Hata: {error_checks}")

        # Öneriler
        if self.results["recommendations"]:
            logger.info("\n📋 ÖNERİLER:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                logger.info(f"   {i}. {rec}")

        # Raporu dosyaya kaydet
        report_file = Path("backend/diagnostic_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"\n📄 Detaylı rapor kaydedildi: {report_file}")
        logger.info("=" * 60)


async def main():
    """Ana fonksiyon"""
    diagnostic = VideoAPIDiagnostic()
    await diagnostic.run_all_checks()


if __name__ == "__main__":
    asyncio.run(main())
