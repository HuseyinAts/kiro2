"""
Health Check System

Bu modül, endpoint'lere test request'leri göndererek sağlık kontrolü yapar.
"""

import asyncio
import logging
import time
from collections import deque

import httpx

from .models import CircuitState, EndpointMetadata, HealthCheckResult, HealthStatus

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Endpoint'lere health check yapan sınıf.
    
    Bu sınıf, endpoint'lere periyodik olarak test request'leri gönderir,
    response time'ları ölçer ve sonuçları Redis'e kaydeder.
    
    Attributes:
        base_url: API base URL'i
        redis_client: Redis client instance'ı
        timeout: Request timeout süresi (saniye)
        response_times: Endpoint'lerin response time geçmişi
    """

    def __init__(
        self,
        base_url: str,
        redis_client=None,
        timeout: int = 30
    ):
        """
        HealthChecker sınıfını başlatır.
        
        Args:
            base_url: API base URL'i (örn: http://localhost:8000)
            redis_client: Redis client instance'ı
            timeout: Request timeout süresi (saniye)
        """
        self.base_url = base_url.rstrip("/")
        self.redis_client = redis_client
        self.timeout = timeout

        # Her endpoint için response time geçmişi (sliding window)
        # Key: "method:path", Value: deque of response times
        self.response_times: dict[str, deque[float]] = {}

        # Sliding window size (son 100 request)
        self.window_size = 100

        logger.info(f"HealthChecker başlatıldı: {base_url}")

    async def check_endpoint(
        self,
        metadata: EndpointMetadata,
        circuit_state: CircuitState = CircuitState.CLOSED
    ) -> HealthCheckResult:
        """
        Tek bir endpoint'e health check yapar.
        
        Args:
            metadata: Endpoint metadata bilgileri
            circuit_state: Mevcut circuit breaker durumu
            
        Returns:
            HealthCheckResult instance'ı
            
        Requirements:
            REQ-2.1: Her endpoint'e test request gönderir
            REQ-2.2: 30 saniye timeout uygular
            REQ-2.3: Status code'u kontrol eder (200-299 başarılı)
        """
        endpoint_key = f"{metadata.method}:{metadata.path}"

        # Circuit OPEN ise request gönderme
        if circuit_state == CircuitState.OPEN:
            logger.warning(f"Circuit OPEN: {endpoint_key}")
            return HealthCheckResult(
                endpoint=metadata.path,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0.0,
                status_code=503,
                error_message="Circuit breaker is OPEN",
                circuit_state=circuit_state
            )

        # Test request gönder
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}{metadata.path}"

                # HTTP method'a göre request gönder
                if metadata.method == "GET":
                    response = await client.get(url)
                elif metadata.method == "POST":
                    response = await client.post(url, json={})
                elif metadata.method == "PUT":
                    response = await client.put(url, json={})
                elif metadata.method == "DELETE":
                    response = await client.delete(url)
                else:
                    response = await client.request(metadata.method, url)

                # Response time hesapla (milisaniye)
                response_time_ms = (time.time() - start_time) * 1000

                # Response time'ı kaydet
                self._record_response_time(endpoint_key, response_time_ms)

                # Status code kontrolü
                is_success = response.status_code in metadata.expected_status_codes

                # Health status belirle
                if is_success:
                    status = HealthStatus.HEALTHY
                    error_message = None
                else:
                    status = HealthStatus.UNHEALTHY
                    error_message = f"Unexpected status code: {response.status_code}"

                result = HealthCheckResult(
                    endpoint=metadata.path,
                    status=status,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    error_message=error_message,
                    circuit_state=circuit_state
                )

                # Redis'e kaydet
                if self.redis_client:
                    await self._store_result(result)

                logger.debug(
                    f"Health check tamamlandı: {endpoint_key} - "
                    f"{response_time_ms:.2f}ms - {response.status_code}"
                )

                return result

        except httpx.TimeoutException:
            response_time_ms = self.timeout * 1000
            logger.warning(f"Timeout: {endpoint_key}")

            result = HealthCheckResult(
                endpoint=metadata.path,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                status_code=0,
                error_message=f"Request timeout after {self.timeout}s",
                circuit_state=circuit_state
            )

            if self.redis_client:
                await self._store_result(result)

            return result

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check hatası: {endpoint_key} - {e}")

            result = HealthCheckResult(
                endpoint=metadata.path,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                status_code=0,
                error_message=str(e),
                circuit_state=circuit_state
            )

            if self.redis_client:
                await self._store_result(result)

            return result

    async def check_multiple_endpoints(
        self,
        endpoints: list[EndpointMetadata],
        circuit_states: dict[str, CircuitState] | None = None
    ) -> list[HealthCheckResult]:
        """
        Birden fazla endpoint'e paralel health check yapar.
        
        Args:
            endpoints: Endpoint metadata listesi
            circuit_states: Endpoint'lerin circuit breaker durumları
            
        Returns:
            HealthCheckResult listesi
        """
        if circuit_states is None:
            circuit_states = {}

        # Paralel olarak tüm endpoint'leri kontrol et
        tasks = []
        for metadata in endpoints:
            endpoint_key = f"{metadata.method}:{metadata.path}"
            circuit_state = circuit_states.get(endpoint_key, CircuitState.CLOSED)
            tasks.append(self.check_endpoint(metadata, circuit_state))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Exception'ları handle et
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Health check exception: {endpoints[i].path} - {result}")
                # Exception durumunda unhealthy result oluştur
                valid_results.append(
                    HealthCheckResult(
                        endpoint=endpoints[i].path,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0.0,
                        status_code=0,
                        error_message=str(result),
                        circuit_state=CircuitState.CLOSED
                    )
                )
            else:
                valid_results.append(result)

        return valid_results

    def _record_response_time(self, endpoint_key: str, response_time_ms: float) -> None:
        """
        Response time'ı sliding window'a kaydeder.
        
        Args:
            endpoint_key: Endpoint key (method:path)
            response_time_ms: Response time (milisaniye)
        """
        if endpoint_key not in self.response_times:
            self.response_times[endpoint_key] = deque(maxlen=self.window_size)

        self.response_times[endpoint_key].append(response_time_ms)

    def calculate_percentiles(self, endpoint_key: str) -> dict[str, float]:
        """
        Endpoint için P50, P95, P99 metriklerini hesaplar.
        
        Args:
            endpoint_key: Endpoint key (method:path)
            
        Returns:
            Percentile değerleri dict'i
            
        Requirements:
            REQ-2.4: P50, P95, P99 metriklerini hesaplar
        """
        if endpoint_key not in self.response_times:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        times = sorted(self.response_times[endpoint_key])

        if not times:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        n = len(times)

        # Percentile hesaplama
        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        return {
            "p50": times[p50_idx] if p50_idx < n else times[-1],
            "p95": times[p95_idx] if p95_idx < n else times[-1],
            "p99": times[p99_idx] if p99_idx < n else times[-1]
        }

    async def _store_result(self, result: HealthCheckResult) -> None:
        """
        Health check sonucunu Redis'e kaydeder.
        
        Args:
            result: HealthCheckResult instance'ı
            
        Requirements:
            REQ-2.5: Sonuçları Redis'e yazar
        """
        if not self.redis_client:
            return

        try:
            # Redis key formatı: kiro2:health:results:{endpoint}
            redis_key = f"kiro2:health:results:{result.endpoint}"

            # Sonucu JSON olarak kaydet
            await self.redis_client.hset(
                redis_key,
                mapping={
                    "status": result.status.value,
                    "response_time_ms": str(result.response_time_ms),
                    "status_code": str(result.status_code),
                    "error_message": result.error_message or "",
                    "timestamp": result.timestamp.isoformat(),
                    "circuit_state": result.circuit_state.value
                }
            )

            # TTL ayarla (1 saat)
            await self.redis_client.expire(redis_key, 3600)

            logger.debug(f"Result Redis'e kaydedildi: {redis_key}")
        except Exception as e:
            logger.error(f"Result Redis'e kaydedilemedi: {e}")

    async def send_critical_alert(
        self,
        metadata: EndpointMetadata,
        result: HealthCheckResult
    ) -> None:
        """
        Kritik endpoint başarısız olduğunda alert gönderir.
        
        Args:
            metadata: Endpoint metadata
            result: Health check sonucu
            
        Requirements:
            REQ-2.6: Kritik endpoint başarısız olduğunda anında alert gönderir
        """
        if not metadata.is_critical:
            return

        if result.status != HealthStatus.UNHEALTHY:
            return

        # Alert mesajı oluştur
        alert_message = (
            f"🚨 KRİTİK ENDPOINT BAŞARISIZ!\n"
            f"Endpoint: {result.endpoint}\n"
            f"Status Code: {result.status_code}\n"
            f"Response Time: {result.response_time_ms:.2f}ms\n"
            f"Error: {result.error_message}\n"
            f"Timestamp: {result.timestamp.isoformat()}"
        )

        logger.critical(alert_message)

        # TODO: Slack/Email/SMS alert gönderme
        # Bu kısım alerting modülü implement edildikten sonra eklenecek

        # Redis'e alert kaydı
        if self.redis_client:
            try:
                alert_key = f"kiro2:health:alerts:{result.endpoint}"
                await self.redis_client.lpush(alert_key, alert_message)
                await self.redis_client.ltrim(alert_key, 0, 99)  # Son 100 alert
                await self.redis_client.expire(alert_key, 86400)  # 24 saat
            except Exception as e:
                logger.error(f"Alert Redis'e kaydedilemedi: {e}")
