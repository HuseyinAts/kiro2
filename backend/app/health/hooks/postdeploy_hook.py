"""
PostDeploy Hook

Bu modul, deployment sonrası otomatik doğrulama ve smoke test
işlemlerini gerçekleştirir.

Requirements:
    REQ-7.1: Deploy sonrası otomatik tetikleme
    REQ-7.2: Kritik endpoint'lere smoke test
    REQ-7.3: Başarısız smoke test -> rollback
    REQ-7.4: Başarılı smoke test -> full health check
    REQ-7.5: Deployment sonuç raporu
    REQ-7.6: Başarısız deployment -> incident ticket
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Callable

import httpx

from ..models import EndpointMetadata

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment durumu enum'u."""
    PENDING = "pending"
    SMOKE_TESTING = "smoke_testing"
    HEALTH_CHECKING = "health_checking"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class SmokeTestResult:
    """Smoke test sonucu."""
    endpoint: str
    method: str
    success: bool
    status_code: int
    response_time_ms: float
    error_message: Optional[str] = None


@dataclass
class DeploymentReport:
    """Deployment raporu."""
    deployment_id: str
    version: str
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    smoke_test_results: List[SmokeTestResult] = field(default_factory=list)
    health_check_passed: bool = False
    rollback_performed: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Dict'e dönüştürür."""
        return {
            "deployment_id": self.deployment_id,
            "version": self.version,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "smoke_test_results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time_ms": r.response_time_ms,
                    "error_message": r.error_message
                }
                for r in self.smoke_test_results
            ],
            "health_check_passed": self.health_check_passed,
            "rollback_performed": self.rollback_performed,
            "error_message": self.error_message
        }


class PostDeployHook:
    """
    Deployment sonrası doğrulama hook'u.

    Bu sınıf, yeni bir deployment tamamlandığında otomatik olarak
    tetiklenir ve kritik endpoint'lere smoke test yaparak
    deployment'ın başarılı olduğunu doğrular.

    Attributes:
        base_url: API base URL
        redis_client: Redis client
        timeout: Request timeout (saniye)
        critical_endpoints: Kritik endpoint listesi
    """

    def __init__(
        self,
        base_url: str,
        redis_client=None,
        timeout: int = 10,
        critical_endpoints: Optional[List[EndpointMetadata]] = None
    ):
        """
        PostDeployHook sınıfını başlatır.

        Args:
            base_url: API base URL
            redis_client: Redis client
            timeout: Smoke test timeout (saniye)
            critical_endpoints: Kritik endpoint listesi
        """
        self.base_url = base_url.rstrip("/")
        self.redis_client = redis_client
        self.timeout = timeout
        self.critical_endpoints = critical_endpoints or []

        # Callbacks
        self._on_success_callbacks: List[Callable] = []
        self._on_failure_callbacks: List[Callable] = []
        self._rollback_callback: Optional[Callable] = None

        logger.info(f"PostDeployHook başlatıldı: {base_url}")

    async def trigger(
        self,
        deployment_id: str,
        version: str
    ) -> DeploymentReport:
        """
        Deployment sonrası hook'u tetikler.

        Args:
            deployment_id: Deployment ID
            version: Yeni versiyon

        Returns:
            DeploymentReport instance

        Requirements:
            REQ-7.1: Deploy sonrası otomatik tetikleme
        """
        logger.info(f"PostDeploy hook tetiklendi: {deployment_id} (v{version})")

        report = DeploymentReport(
            deployment_id=deployment_id,
            version=version,
            status=DeploymentStatus.PENDING,
            started_at=datetime.now(UTC)
        )

        try:
            # 1. Smoke test yap
            report.status = DeploymentStatus.SMOKE_TESTING
            smoke_results = await self._run_smoke_tests()
            report.smoke_test_results = smoke_results

            # Smoke test başarılı mı?
            all_passed = all(r.success for r in smoke_results)

            if not all_passed:
                # Smoke test başarısız, rollback yap
                logger.error(f"Smoke test başarısız: {deployment_id}")
                report.status = DeploymentStatus.FAILED
                report.error_message = "Smoke test failed"

                await self._perform_rollback(report)
                await self._create_incident(report)

                report.completed_at = datetime.now(UTC)
                await self._store_report(report)
                await self._notify_failure(report)

                return report

            # 2. Full health check başlat
            report.status = DeploymentStatus.HEALTH_CHECKING
            health_passed = await self._run_full_health_check()
            report.health_check_passed = health_passed

            if not health_passed:
                logger.warning(
                    f"Health check başarısız ama devam ediliyor: {deployment_id}"
                )

            # 3. Başarılı
            report.status = DeploymentStatus.SUCCESS
            report.completed_at = datetime.now(UTC)

            await self._store_report(report)
            await self._notify_success(report)

            logger.info(f"Deployment başarılı: {deployment_id}")

            return report

        except Exception as e:
            logger.error(f"PostDeploy hook hatası: {e}")

            report.status = DeploymentStatus.FAILED
            report.error_message = str(e)
            report.completed_at = datetime.now(UTC)

            await self._perform_rollback(report)
            await self._create_incident(report)
            await self._store_report(report)
            await self._notify_failure(report)

            return report

    async def _run_smoke_tests(self) -> List[SmokeTestResult]:
        """
        Kritik endpoint'lere smoke test yapar.

        Returns:
            SmokeTestResult listesi

        Requirements:
            REQ-7.2: Kritik endpoint'lere smoke test
        """
        logger.info(f"Smoke test başlıyor: {len(self.critical_endpoints)} endpoint")

        results = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for endpoint in self.critical_endpoints:
                result = await self._test_endpoint(client, endpoint)
                results.append(result)

                if not result.success:
                    logger.error(
                        f"Smoke test başarısız: {endpoint.method} {endpoint.path} - "
                        f"{result.error_message}"
                    )

        passed = sum(1 for r in results if r.success)
        logger.info(f"Smoke test tamamlandı: {passed}/{len(results)} başarılı")

        return results

    async def _test_endpoint(
        self,
        client: httpx.AsyncClient,
        endpoint: EndpointMetadata
    ) -> SmokeTestResult:
        """
        Tek bir endpoint'i test eder.

        Args:
            client: HTTP client
            endpoint: Endpoint metadata

        Returns:
            SmokeTestResult
        """
        import time

        url = f"{self.base_url}{endpoint.path}"
        start_time = time.time()

        try:
            if endpoint.method == "GET":
                response = await client.get(url)
            elif endpoint.method == "POST":
                response = await client.post(url, json={})
            elif endpoint.method == "PUT":
                response = await client.put(url, json={})
            elif endpoint.method == "DELETE":
                response = await client.delete(url)
            else:
                response = await client.request(endpoint.method, url)

            response_time_ms = (time.time() - start_time) * 1000

            # Status code kontrolü
            success = response.status_code in endpoint.expected_status_codes

            return SmokeTestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                success=success,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                error_message=None if success else f"Unexpected status: {response.status_code}"
            )

        except httpx.TimeoutException:
            return SmokeTestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                success=False,
                status_code=0,
                response_time_ms=self.timeout * 1000,
                error_message=f"Timeout after {self.timeout}s"
            )

        except Exception as e:
            return SmokeTestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                success=False,
                status_code=0,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )

    async def _run_full_health_check(self) -> bool:
        """
        Full health check başlatır.

        Returns:
            True ise health check başarılı

        Requirements:
            REQ-7.4: Başarılı smoke test -> full health check
        """
        logger.info("Full health check başlatılıyor")

        # Bu method, HealthChecker ile entegre edilecek
        # Şimdilik basit bir kontrol yapıyoruz

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check hatası: {e}")
            return False

    async def _perform_rollback(self, report: DeploymentReport) -> None:
        """
        Deployment'ı rollback eder.

        Args:
            report: Deployment raporu

        Requirements:
            REQ-7.3: Başarısız smoke test -> rollback
        """
        logger.warning(f"Rollback başlatılıyor: {report.deployment_id}")

        if self._rollback_callback:
            try:
                await self._rollback_callback(report.deployment_id, report.version)
                report.rollback_performed = True
                report.status = DeploymentStatus.ROLLED_BACK
                logger.info(f"Rollback tamamlandı: {report.deployment_id}")
            except Exception as e:
                logger.error(f"Rollback hatası: {e}")
        else:
            logger.warning("Rollback callback tanımlanmamış")

    async def _create_incident(self, report: DeploymentReport) -> None:
        """
        Deployment hatası için incident oluşturur.

        Args:
            report: Deployment raporu

        Requirements:
            REQ-7.6: Başarısız deployment -> incident ticket
        """
        incident = {
            "type": "deployment_failure",
            "deployment_id": report.deployment_id,
            "version": report.version,
            "error_message": report.error_message,
            "timestamp": datetime.now(UTC).isoformat(),
            "failed_tests": [
                {"endpoint": r.endpoint, "error": r.error_message}
                for r in report.smoke_test_results
                if not r.success
            ],
            "severity": "critical"
        }

        logger.critical(
            f"🚨 DEPLOYMENT INCIDENT!\n"
            f"ID: {report.deployment_id}\n"
            f"Version: {report.version}\n"
            f"Error: {report.error_message}"
        )

        # Redis'e kaydet
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    "kiro2:health:incidents:deployment",
                    str(incident)
                )
                await self.redis_client.ltrim(
                    "kiro2:health:incidents:deployment",
                    0, 99
                )
            except Exception as e:
                logger.error(f"Incident kaydedilemedi: {e}")

    async def _store_report(self, report: DeploymentReport) -> None:
        """
        Deployment raporunu kaydeder.

        Args:
            report: Deployment raporu

        Requirements:
            REQ-7.5: Deployment sonuç raporu
        """
        if not self.redis_client:
            return

        try:
            redis_key = f"kiro2:health:deployments:{report.deployment_id}"

            await self.redis_client.set(
                redis_key,
                str(report.to_dict()),
                ex=86400 * 30  # 30 gün
            )

            # Son deployment'ı da kaydet
            await self.redis_client.set(
                "kiro2:health:deployments:latest",
                str(report.to_dict()),
                ex=86400 * 7  # 7 gün
            )

            logger.debug(f"Deployment raporu kaydedildi: {report.deployment_id}")

        except Exception as e:
            logger.error(f"Deployment raporu kaydedilemedi: {e}")

    async def _notify_success(self, report: DeploymentReport) -> None:
        """Başarılı deployment bildirimi gönderir."""
        for callback in self._on_success_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(report)
                else:
                    callback(report)
            except Exception as e:
                logger.error(f"Success callback hatası: {e}")

    async def _notify_failure(self, report: DeploymentReport) -> None:
        """Başarısız deployment bildirimi gönderir."""
        for callback in self._on_failure_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(report)
                else:
                    callback(report)
            except Exception as e:
                logger.error(f"Failure callback hatası: {e}")

    def on_success(self, callback: Callable) -> None:
        """Başarılı deployment callback'i ekler."""
        self._on_success_callbacks.append(callback)

    def on_failure(self, callback: Callable) -> None:
        """Başarısız deployment callback'i ekler."""
        self._on_failure_callbacks.append(callback)

    def set_rollback_callback(self, callback: Callable) -> None:
        """Rollback callback'ini ayarlar."""
        self._rollback_callback = callback

    def add_critical_endpoint(self, endpoint: EndpointMetadata) -> None:
        """Kritik endpoint ekler."""
        self.critical_endpoints.append(endpoint)
