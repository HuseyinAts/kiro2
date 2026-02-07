"""
Health Score Calculator

Bu modul, endpoint'lerin sağlık skorunu hesaplar.
Skor 0-100 arası bir değerdir ve şu ağırlıklarla hesaplanır:
- Response Time: %40
- Error Rate: %30
- Uptime: %20
- Dependency Health: %10

Requirements:
    REQ-8.1: Health score hesaplama (0-100 arası)
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Optional

from typing import List
from .models import HealthCheckResult, HealthScore, HealthStatus

logger = logging.getLogger(__name__)


class HealthScoreCalculator:
    """
    Endpoint sağlık skoru hesaplayan sınıf.

    Health score, endpoint'in genel sağlık durumunu tek bir
    sayısal değerle ifade eder. Bu skor, response time,
    error rate, uptime ve dependency health metriklerinin
    ağırlıklı ortalamasıdır.

    Score Interpretation:
    - 90-100: Excellent (Mükemmel)
    - 70-89: Good (İyi)
    - 50-69: Fair (Orta)
    - 30-49: Poor (Zayıf)
    - 0-29: Critical (Kritik)

    Attributes:
        redis_client: Redis client instance
        response_time_weight: Response time ağırlığı
        error_rate_weight: Error rate ağırlığı
        uptime_weight: Uptime ağırlığı
        dependency_weight: Dependency health ağırlığı
    """

    # Ağırlıklar (toplam: 1.0)
    DEFAULT_WEIGHTS = {
        "response_time": 0.40,
        "error_rate": 0.30,
        "uptime": 0.20,
        "dependency": 0.10
    }

    # Response time thresholds (ms)
    RESPONSE_TIME_EXCELLENT = 50.0   # < 50ms = 100 puan
    RESPONSE_TIME_GOOD = 100.0       # < 100ms = 90 puan
    RESPONSE_TIME_FAIR = 200.0       # < 200ms = 70 puan
    RESPONSE_TIME_POOR = 500.0       # < 500ms = 40 puan
    RESPONSE_TIME_CRITICAL = 1000.0  # >= 1000ms = 0 puan

    def __init__(
        self,
        redis_client=None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        HealthScoreCalculator sınıfını başlatır.

        Args:
            redis_client: Redis client instance
            weights: Özel ağırlık değerleri (opsiyonel)
        """
        self.redis_client = redis_client
        self.weights = weights or self.DEFAULT_WEIGHTS

        # Ağırlıkların toplamını doğrula
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(
                f"Ağırlıkların toplamı 1.0 değil: {total_weight}. Normalize ediliyor."
            )
            self.weights = {k: v / total_weight for k, v in self.weights.items()}

        logger.info(f"HealthScoreCalculator başlatıldı: weights={self.weights}")

    def calculate_score(
        self,
        endpoint: str,
        response_time_ms: float,
        error_rate: float,
        uptime_percentage: float,
        dependency_health: float = 100.0
    ) -> HealthScore:
        """
        Endpoint için sağlık skoru hesaplar.

        Args:
            endpoint: Endpoint path
            response_time_ms: Ortalama response time (P95 önerilir)
            error_rate: Hata oranı (0.0-1.0 arası, örn: 0.05 = %5)
            uptime_percentage: Uptime yüzdesi (0.0-100.0)
            dependency_health: Dependency sağlık skoru (0.0-100.0)

        Returns:
            HealthScore instance

        Requirements:
            REQ-8.1: Health score hesaplama (0-100 arası)
        """
        # Her metrik için skor hesapla
        response_time_score = self._calculate_response_time_score(response_time_ms)
        error_rate_score = self._calculate_error_rate_score(error_rate)
        uptime_score = self._calculate_uptime_score(uptime_percentage)
        dependency_score = min(max(dependency_health, 0.0), 100.0)

        # Ağırlıklı ortalama
        weighted_score = (
            response_time_score * self.weights["response_time"] +
            error_rate_score * self.weights["error_rate"] +
            uptime_score * self.weights["uptime"] +
            dependency_score * self.weights["dependency"]
        )

        # 0-100 arası sınırla ve yuvarla
        final_score = int(min(max(weighted_score, 0), 100))

        health_score = HealthScore(
            endpoint=endpoint,
            score=final_score,
            response_time_score=response_time_score,
            error_rate_score=error_rate_score,
            uptime_score=uptime_score,
            dependency_score=dependency_score
        )

        logger.debug(
            f"Health score hesaplandı: {endpoint} = {final_score} "
            f"(rt:{response_time_score:.1f}, er:{error_rate_score:.1f}, "
            f"up:{uptime_score:.1f}, dep:{dependency_score:.1f})"
        )

        return health_score

    def _calculate_response_time_score(self, response_time_ms: float) -> float:
        """
        Response time skorunu hesaplar.

        Daha düşük response time = daha yüksek skor.

        Args:
            response_time_ms: Response time (milisaniye)

        Returns:
            Skor (0.0-100.0)
        """
        if response_time_ms <= 0:
            return 100.0

        if response_time_ms < self.RESPONSE_TIME_EXCELLENT:
            return 100.0
        elif response_time_ms < self.RESPONSE_TIME_GOOD:
            # 50-100ms: 90-100 arası linear
            ratio = (response_time_ms - self.RESPONSE_TIME_EXCELLENT) / \
                    (self.RESPONSE_TIME_GOOD - self.RESPONSE_TIME_EXCELLENT)
            return 100.0 - (ratio * 10.0)
        elif response_time_ms < self.RESPONSE_TIME_FAIR:
            # 100-200ms: 70-90 arası linear
            ratio = (response_time_ms - self.RESPONSE_TIME_GOOD) / \
                    (self.RESPONSE_TIME_FAIR - self.RESPONSE_TIME_GOOD)
            return 90.0 - (ratio * 20.0)
        elif response_time_ms < self.RESPONSE_TIME_POOR:
            # 200-500ms: 40-70 arası linear
            ratio = (response_time_ms - self.RESPONSE_TIME_FAIR) / \
                    (self.RESPONSE_TIME_POOR - self.RESPONSE_TIME_FAIR)
            return 70.0 - (ratio * 30.0)
        elif response_time_ms < self.RESPONSE_TIME_CRITICAL:
            # 500-1000ms: 0-40 arası linear
            ratio = (response_time_ms - self.RESPONSE_TIME_POOR) / \
                    (self.RESPONSE_TIME_CRITICAL - self.RESPONSE_TIME_POOR)
            return 40.0 - (ratio * 40.0)
        else:
            return 0.0

    def _calculate_error_rate_score(self, error_rate: float) -> float:
        """
        Error rate skorunu hesaplar.

        Daha düşük error rate = daha yüksek skor.

        Args:
            error_rate: Hata oranı (0.0-1.0)

        Returns:
            Skor (0.0-100.0)
        """
        # Error rate'i yüzdeye çevir
        error_percentage = error_rate * 100.0

        if error_percentage <= 0.0:
            return 100.0
        elif error_percentage < 0.1:
            # < 0.1%: 95-100
            return 100.0 - (error_percentage * 50.0)
        elif error_percentage < 0.5:
            # 0.1-0.5%: 85-95
            ratio = (error_percentage - 0.1) / 0.4
            return 95.0 - (ratio * 10.0)
        elif error_percentage < 1.0:
            # 0.5-1%: 70-85
            ratio = (error_percentage - 0.5) / 0.5
            return 85.0 - (ratio * 15.0)
        elif error_percentage < 2.0:
            # 1-2%: 50-70
            ratio = (error_percentage - 1.0) / 1.0
            return 70.0 - (ratio * 20.0)
        elif error_percentage < 5.0:
            # 2-5%: 20-50
            ratio = (error_percentage - 2.0) / 3.0
            return 50.0 - (ratio * 30.0)
        elif error_percentage < 10.0:
            # 5-10%: 0-20
            ratio = (error_percentage - 5.0) / 5.0
            return 20.0 - (ratio * 20.0)
        else:
            return 0.0

    def _calculate_uptime_score(self, uptime_percentage: float) -> float:
        """
        Uptime skorunu hesaplar.

        Args:
            uptime_percentage: Uptime yüzdesi (0.0-100.0)

        Returns:
            Skor (0.0-100.0)
        """
        if uptime_percentage >= 99.99:
            return 100.0
        elif uptime_percentage >= 99.9:
            # 99.9-99.99%: 95-100
            ratio = (uptime_percentage - 99.9) / 0.09
            return 95.0 + (ratio * 5.0)
        elif uptime_percentage >= 99.5:
            # 99.5-99.9%: 85-95
            ratio = (uptime_percentage - 99.5) / 0.4
            return 85.0 + (ratio * 10.0)
        elif uptime_percentage >= 99.0:
            # 99.0-99.5%: 70-85
            ratio = (uptime_percentage - 99.0) / 0.5
            return 70.0 + (ratio * 15.0)
        elif uptime_percentage >= 95.0:
            # 95-99%: 40-70
            ratio = (uptime_percentage - 95.0) / 4.0
            return 40.0 + (ratio * 30.0)
        elif uptime_percentage >= 90.0:
            # 90-95%: 20-40
            ratio = (uptime_percentage - 90.0) / 5.0
            return 20.0 + (ratio * 20.0)
        else:
            # < 90%: 0-20
            ratio = uptime_percentage / 90.0
            return ratio * 20.0

    def get_status_from_score(self, score: int) -> HealthStatus:
        """
        Skordan HealthStatus belirler.

        Args:
            score: Sağlık skoru (0-100)

        Returns:
            HealthStatus enum değeri
        """
        if score >= 70:
            return HealthStatus.HEALTHY
        elif score >= 50:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def get_score_label(self, score: int) -> str:
        """
        Skor için insan okunabilir etiket döndürür.

        Args:
            score: Sağlık skoru (0-100)

        Returns:
            Etiket string'i
        """
        if score >= 90:
            return "Excellent (Mükemmel)"
        elif score >= 70:
            return "Good (İyi)"
        elif score >= 50:
            return "Fair (Orta)"
        elif score >= 30:
            return "Poor (Zayıf)"
        else:
            return "Critical (Kritik)"

    async def calculate_and_store(
        self,
        endpoint: str,
        response_time_ms: float,
        error_rate: float,
        uptime_percentage: float,
        dependency_health: float = 100.0
    ) -> HealthScore:
        """
        Skor hesaplar ve Redis'e kaydeder.

        Args:
            endpoint: Endpoint path
            response_time_ms: Response time (ms)
            error_rate: Hata oranı (0.0-1.0)
            uptime_percentage: Uptime yüzdesi
            dependency_health: Dependency sağlık skoru

        Returns:
            HealthScore instance
        """
        score = self.calculate_score(
            endpoint=endpoint,
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            uptime_percentage=uptime_percentage,
            dependency_health=dependency_health
        )

        # Redis'e kaydet
        if self.redis_client:
            try:
                redis_key = f"kiro2:health:scores:{endpoint}"

                await self.redis_client.hset(
                    redis_key,
                    mapping={
                        "score": str(score.score),
                        "response_time_score": str(score.response_time_score),
                        "error_rate_score": str(score.error_rate_score),
                        "uptime_score": str(score.uptime_score),
                        "dependency_score": str(score.dependency_score),
                        "timestamp": score.timestamp.isoformat(),
                        "status": self.get_status_from_score(score.score).value,
                        "label": self.get_score_label(score.score)
                    }
                )

                await self.redis_client.expire(redis_key, 300)  # 5 dakika

                logger.debug(f"Health score Redis'e kaydedildi: {endpoint}")
            except Exception as e:
                logger.error(f"Health score kaydedilemedi: {e}")

        return score

    async def get_stored_score(self, endpoint: str) -> Optional[HealthScore]:
        """
        Redis'ten kaydedilmiş skoru getirir.

        Args:
            endpoint: Endpoint path

        Returns:
            HealthScore veya None
        """
        if not self.redis_client:
            return None

        try:
            redis_key = f"kiro2:health:scores:{endpoint}"
            data = await self.redis_client.hgetall(redis_key)

            if not data:
                return None

            return HealthScore(
                endpoint=endpoint,
                score=int(data.get(b"score", b"0").decode()),
                response_time_score=float(data.get(b"response_time_score", b"0").decode()),
                error_rate_score=float(data.get(b"error_rate_score", b"0").decode()),
                uptime_score=float(data.get(b"uptime_score", b"0").decode()),
                dependency_score=float(data.get(b"dependency_score", b"0").decode()),
                timestamp=datetime.fromisoformat(
                    data.get(b"timestamp", b"").decode()
                ) if data.get(b"timestamp") else datetime.now(UTC)
            )
        except Exception as e:
            logger.error(f"Health score getirilemedi: {e}")
            return None

    async def calculate_from_results(
        self,
        results: List[HealthCheckResult],
        dependency_health: float = 100.0
    ) -> float:
        """
        Health check sonuçlarından genel sağlık skoru hesaplar.

        Args:
            results: Health check sonuçları listesi
            dependency_health: Dependency sağlık skoru (0.0-1.0 veya 0.0-100.0)

        Returns:
            Genel sağlık skoru (0-100)
        """
        if not results:
            return 100.0

        # Dependency health'i normalize et (0-100 arasına)
        if dependency_health <= 1.0:
            dependency_health = dependency_health * 100.0

        # Response time ortalaması
        avg_response_time = sum(r.response_time_ms for r in results) / len(results)

        # Error rate (unhealthy oranı)
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        error_rate = unhealthy_count / len(results)

        # Uptime (healthy + degraded oranı)
        healthy_count = sum(1 for r in results if r.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED])
        uptime_percentage = (healthy_count / len(results)) * 100.0

        # Tek bir skor hesapla
        score = self.calculate_score(
            endpoint="aggregate",
            response_time_ms=avg_response_time,
            error_rate=error_rate,
            uptime_percentage=uptime_percentage,
            dependency_health=dependency_health
        )

        return float(score.score)
