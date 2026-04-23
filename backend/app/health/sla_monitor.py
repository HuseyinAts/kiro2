"""
SLA Monitor

Bu modül, endpoint'lerin SLA (Service Level Agreement) uyumluluğunu
izler ve P95 response time metriklerine göre sağlık durumu belirler.
"""

import logging
from datetime import UTC, datetime, timedelta

from .models import (
    HealthCheckResult,
    HealthStatus,
    SLAComplianceReport,
    SLAMetrics,
    SLATarget,
)

logger = logging.getLogger(__name__)


class SLAMonitor:
    """
    SLA monitoring ve compliance kontrolü yapan sınıf.
    
    Bu sınıf, endpoint'lerin P95 response time'larını kontrol eder
    ve SLA threshold'larına göre sağlık durumu belirler.
    
    SLA Thresholds:
    - P95 < 200ms: HEALTHY
    - P95 200-500ms: DEGRADED
    - P95 > 500ms: UNHEALTHY
    
    Attributes:
        redis_client: Redis client instance'ı
        healthy_threshold: Healthy threshold (ms)
        degraded_threshold: Degraded threshold (ms)
        violation_window: SLA ihlali penceresi (dakika)
    """

    def __init__(
        self,
        redis_client=None,
        healthy_threshold: float = 200.0,
        degraded_threshold: float = 500.0,
        violation_window: int = 5
    ):
        """
        SLAMonitor sınıfını başlatır.
        
        Args:
            redis_client: Redis client instance'ı
            healthy_threshold: Healthy threshold (ms)
            degraded_threshold: Degraded threshold (ms)
            violation_window: SLA ihlali penceresi (dakika)
        """
        self.redis_client = redis_client
        self.healthy_threshold = healthy_threshold
        self.degraded_threshold = degraded_threshold
        self.violation_window = violation_window

        # SLA ihlali takibi
        self.violations: dict[str, datetime] = {}

        # SLA hedefleri ve check kayıtları
        self.targets: dict[str, SLATarget] = {}
        self.check_records: dict[str, list] = {}

        logger.info(
            f"SLAMonitor başlatıldı: "
            f"healthy<{healthy_threshold}ms, "
            f"degraded<{degraded_threshold}ms"
        )

    def classify_health_status(self, p95_ms: float) -> HealthStatus:
        """
        P95 response time'a göre sağlık durumu belirler.
        
        Args:
            p95_ms: P95 response time (milisaniye)
            
        Returns:
            HealthStatus enum değeri
            
        Requirements:
            REQ-3.1: P95 metriğini kontrol eder
            REQ-3.2: P95 < 200ms → "healthy"
            REQ-3.3: P95 200-500ms → "degraded"
            REQ-3.4: P95 > 500ms → "unhealthy"
        """
        if p95_ms < self.healthy_threshold:
            return HealthStatus.HEALTHY
        if p95_ms < self.degraded_threshold:
            return HealthStatus.DEGRADED
        return HealthStatus.UNHEALTHY

    async def check_sla_compliance(
        self,
        endpoint: str,
        metrics: SLAMetrics
    ) -> bool:
        """
        Endpoint'in SLA'ya uygun olup olmadığını kontrol eder.
        
        Args:
            endpoint: Endpoint path'i
            metrics: SLA metrikleri
            
        Returns:
            True ise SLA'ya uygun, False değilse
        """
        # P95 threshold kontrolü
        p95_compliant = metrics.p95_ms < self.healthy_threshold

        # Error rate kontrolü (< %1)
        error_rate_compliant = metrics.error_rate < 0.01

        # Uptime kontrolü (> %99.9)
        uptime_compliant = metrics.uptime_percentage > 99.9

        # Tüm kriterler sağlanmalı
        is_compliant = p95_compliant and error_rate_compliant and uptime_compliant

        # SLA ihlali varsa kaydet
        if not is_compliant:
            await self._record_violation(endpoint, metrics)
        # SLA'ya uygunsa, ihlal kaydını temizle
        elif endpoint in self.violations:
            del self.violations[endpoint]

        return is_compliant

    async def _record_violation(
        self,
        endpoint: str,
        metrics: SLAMetrics
    ) -> None:
        """
        SLA ihlalini kaydeder.
        
        Args:
            endpoint: Endpoint path'i
            metrics: SLA metrikleri
            
        Requirements:
            REQ-3.5: SLA ihlali tespit edildiğinde root cause analysis başlatır
        """
        now = datetime.now(UTC)

        # İlk ihlal mi?
        if endpoint not in self.violations:
            self.violations[endpoint] = now
            logger.warning(
                f"SLA ihlali başladı: {endpoint} - "
                f"P95: {metrics.p95_ms:.2f}ms, "
                f"Error Rate: {metrics.error_rate:.2%}, "
                f"Uptime: {metrics.uptime_percentage:.2f}%"
            )

            # Root cause analysis başlat
            await self._start_root_cause_analysis(endpoint, metrics)
        else:
            # İhlal süresi
            violation_duration = now - self.violations[endpoint]

            # 5 dakikadan uzun sürüyorsa incident oluştur
            if violation_duration > timedelta(minutes=self.violation_window):
                await self._create_incident(endpoint, metrics, violation_duration)

    async def _start_root_cause_analysis(
        self,
        endpoint: str,
        metrics: SLAMetrics
    ) -> None:
        """
        Root cause analysis başlatır.
        
        Args:
            endpoint: Endpoint path'i
            metrics: SLA metrikleri
            
        Requirements:
            REQ-3.5: Root cause analysis başlatır
        """
        logger.info(f"Root cause analysis başlatılıyor: {endpoint}")

        # Analiz sonuçları
        analysis = {
            "endpoint": endpoint,
            "timestamp": datetime.now(UTC).isoformat(),
            "metrics": {
                "p95_ms": metrics.p95_ms,
                "error_rate": metrics.error_rate,
                "uptime_percentage": metrics.uptime_percentage
            },
            "possible_causes": []
        }

        # Yüksek response time
        if metrics.p95_ms > self.degraded_threshold:
            analysis["possible_causes"].append({
                "issue": "High response time",
                "value": f"{metrics.p95_ms:.2f}ms",
                "suggestions": [
                    "Check database query performance",
                    "Review external API calls",
                    "Check server resource usage (CPU, Memory)"
                ]
            })

        # Yüksek error rate
        if metrics.error_rate > 0.01:
            analysis["possible_causes"].append({
                "issue": "High error rate",
                "value": f"{metrics.error_rate:.2%}",
                "suggestions": [
                    "Check application logs for errors",
                    "Review recent code deployments",
                    "Check dependency health (DB, Redis, etc.)"
                ]
            })

        # Düşük uptime
        if metrics.uptime_percentage < 99.9:
            analysis["possible_causes"].append({
                "issue": "Low uptime",
                "value": f"{metrics.uptime_percentage:.2f}%",
                "suggestions": [
                    "Check for service restarts",
                    "Review infrastructure health",
                    "Check for network issues"
                ]
            })

        # Redis'e kaydet
        if self.redis_client:
            try:
                redis_key = f"kiro2:health:rca:{endpoint}"
                await self.redis_client.set(
                    redis_key,
                    str(analysis),
                    ex=3600  # 1 saat
                )
                logger.info(f"Root cause analysis kaydedildi: {redis_key}")
            except Exception as e:
                logger.error(f"Root cause analysis kaydedilemedi: {e}")

    async def _create_incident(
        self,
        endpoint: str,
        metrics: SLAMetrics,
        duration: timedelta
    ) -> None:
        """
        SLA ihlali için incident oluşturur.
        
        Args:
            endpoint: Endpoint path'i
            metrics: SLA metrikleri
            duration: İhlal süresi
            
        Requirements:
            REQ-3.6: SLA ihlali 5 dakikadan uzun sürerse incident oluşturur
        """
        logger.critical(
            f"🚨 SLA İHLALİ - INCIDENT OLUŞTURULDU!\n"
            f"Endpoint: {endpoint}\n"
            f"Duration: {duration.total_seconds():.0f} seconds\n"
            f"P95: {metrics.p95_ms:.2f}ms (threshold: {self.healthy_threshold}ms)\n"
            f"Error Rate: {metrics.error_rate:.2%} (threshold: 1%)\n"
            f"Uptime: {metrics.uptime_percentage:.2f}% (threshold: 99.9%)"
        )

        # Incident bilgileri
        incident = {
            "endpoint": endpoint,
            "severity": "critical",
            "started_at": self.violations[endpoint].isoformat(),
            "duration_seconds": duration.total_seconds(),
            "metrics": {
                "p95_ms": metrics.p95_ms,
                "error_rate": metrics.error_rate,
                "uptime_percentage": metrics.uptime_percentage
            },
            "status": "open"
        }

        # Redis'e kaydet
        if self.redis_client:
            try:
                incident_key = f"kiro2:health:incidents:{endpoint}"
                await self.redis_client.lpush(incident_key, str(incident))
                await self.redis_client.ltrim(incident_key, 0, 99)  # Son 100 incident
                await self.redis_client.expire(incident_key, 86400 * 30)  # 30 gün
                logger.info(f"Incident kaydedildi: {incident_key}")
            except Exception as e:
                logger.error(f"Incident kaydedilemedi: {e}")

        # TODO: Incident ticket oluşturma (Jira, PagerDuty, vb.)
        # Bu kısım alerting modülü implement edildikten sonra eklenecek

    async def update_endpoint_status(
        self,
        endpoint: str,
        status: HealthStatus
    ) -> None:
        """
        Endpoint'in sağlık durumunu Redis'te günceller.
        
        Args:
            endpoint: Endpoint path'i
            status: Yeni sağlık durumu
            
        Requirements:
            REQ-3.2, REQ-3.3, REQ-3.4: Endpoint status'unu günceller
        """
        if not self.redis_client:
            return

        try:
            redis_key = f"kiro2:health:status:{endpoint}"
            await self.redis_client.set(
                redis_key,
                status.value,
                ex=3600  # 1 saat
            )
            logger.debug(f"Endpoint status güncellendi: {endpoint} -> {status.value}")
        except Exception as e:
            logger.error(f"Endpoint status güncellenemedi: {e}")

    async def get_endpoint_status(self, endpoint: str) -> HealthStatus | None:
        """
        Endpoint'in mevcut sağlık durumunu getirir.
        
        Args:
            endpoint: Endpoint path'i
            
        Returns:
            HealthStatus veya None
        """
        if not self.redis_client:
            return None

        try:
            redis_key = f"kiro2:health:status:{endpoint}"
            status_str = await self.redis_client.get(redis_key)

            if status_str:
                return HealthStatus(status_str.decode() if isinstance(status_str, bytes) else status_str)
            return None
        except Exception as e:
            logger.error(f"Endpoint status getirilemedi: {e}")
            return None

    def set_target(self, endpoint_key: str, target: SLATarget) -> None:
        """
        Endpoint için SLA hedefi belirler.

        Args:
            endpoint_key: Endpoint key (örn: GET:/api/v1/users)
            target: SLA hedef değerleri
        """
        self.targets[endpoint_key] = target
        logger.info(f"SLA hedefi belirlendi: {endpoint_key} -> {target}")

    async def record_check(self, endpoint_key: str, result: HealthCheckResult) -> None:
        """
        Health check sonucunu kaydeder.

        Args:
            endpoint_key: Endpoint key (örn: GET:/api/v1/users)
            result: Health check sonucu
        """
        if endpoint_key not in self.check_records:
            self.check_records[endpoint_key] = []

        self.check_records[endpoint_key].append(result)

        # Son 1000 kayıt tut
        if len(self.check_records[endpoint_key]) > 1000:
            self.check_records[endpoint_key] = self.check_records[endpoint_key][-1000:]

    async def get_compliance_report(self, endpoint_key: str) -> SLAComplianceReport:
        """
        Endpoint için SLA uyumluluk raporu oluşturur.

        Args:
            endpoint_key: Endpoint key (örn: GET:/api/v1/users)

        Returns:
            SLA uyumluluk raporu
        """
        records = self.check_records.get(endpoint_key, [])

        if not records:
            return SLAComplianceReport(
                endpoint=endpoint_key,
                uptime_percentage=100.0,
                p95_response_time_ms=0.0,
                error_rate=0.0,
                is_compliant=True
            )

        # Uptime hesapla
        healthy_count = sum(1 for r in records if r.status == HealthStatus.HEALTHY)
        uptime = (healthy_count / len(records)) * 100.0

        # Response time P95 hesapla
        response_times = sorted([r.response_time_ms for r in records])
        p95_index = int(len(response_times) * 0.95)
        p95_response_time = response_times[min(p95_index, len(response_times) - 1)]

        # Error rate hesapla
        error_count = sum(1 for r in records if r.status == HealthStatus.UNHEALTHY)
        error_rate = (error_count / len(records)) * 100.0

        # SLA uyumluluk kontrolü
        target = self.targets.get(endpoint_key, SLATarget())
        is_compliant = (
            uptime >= target.target_uptime and
            p95_response_time <= target.target_response_time_ms and
            error_rate <= target.target_error_rate
        )

        return SLAComplianceReport(
            endpoint=endpoint_key,
            uptime_percentage=uptime,
            p95_response_time_ms=p95_response_time,
            error_rate=error_rate,
            is_compliant=is_compliant
        )
