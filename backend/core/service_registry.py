"""
KIRO2 Service Registry
Mikroservisler için service discovery ve health check sistemi
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

from core.events import ServiceName


class ServiceStatus(Enum):
    """Servis durumları"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInstance:
    """Bir servis instance'ı"""
    service_name: ServiceName
    host: str
    port: int
    health_endpoint: str = "/health"
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    weight: int = 100  # Load balancing için ağırlık
    zone: str = "default"

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}{self.health_endpoint}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name.value,
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "health_endpoint": self.health_endpoint,
            "version": self.version,
            "status": self.status.value,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "metadata": self.metadata,
            "weight": self.weight,
            "zone": self.zone,
        }


@dataclass
class ServiceConfig:
    """Servis konfigürasyonu"""
    name: ServiceName
    default_port: int
    health_endpoint: str = "/health"
    critical: bool = True  # Platform için kritik mi?
    dependencies: list[ServiceName] = field(default_factory=list)


# Servis konfigürasyonları
SERVICE_CONFIGS: dict[ServiceName, ServiceConfig] = {
    ServiceName.GATEWAY: ServiceConfig(
        name=ServiceName.GATEWAY,
        default_port=8000,
        critical=True,
        dependencies=[],
    ),
    ServiceName.EXAM: ServiceConfig(
        name=ServiceName.EXAM,
        default_port=8001,
        critical=True,
        dependencies=[ServiceName.GATEWAY],
    ),
    ServiceName.QUESTION: ServiceConfig(
        name=ServiceName.QUESTION,
        default_port=8002,
        critical=True,
        dependencies=[ServiceName.GATEWAY],
    ),
    ServiceName.IRT: ServiceConfig(
        name=ServiceName.IRT,
        default_port=8003,
        critical=True,
        dependencies=[ServiceName.EXAM, ServiceName.QUESTION],
    ),
    ServiceName.AI: ServiceConfig(
        name=ServiceName.AI,
        default_port=8004,
        critical=False,
        dependencies=[ServiceName.GATEWAY],
    ),
    ServiceName.LEARNING_PATH: ServiceConfig(
        name=ServiceName.LEARNING_PATH,
        default_port=8005,
        critical=True,
        dependencies=[ServiceName.IRT, ServiceName.QUESTION],
    ),
    ServiceName.MONOLITH: ServiceConfig(
        name=ServiceName.MONOLITH,
        default_port=8000,
        critical=True,
        dependencies=[],
    ),
}


class ServiceRegistry:
    """Merkezi servis kayıt ve discovery sistemi"""

    def __init__(self):
        self.services: dict[ServiceName, list[ServiceInstance]] = {}
        self.health_check_interval = 30  # saniye
        self._running = False
        self._health_check_task: asyncio.Task | None = None
        self._http_client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Registry'yi başlat"""
        self._running = True
        self._http_client = httpx.AsyncClient(timeout=5.0)

        # Varsayılan servisleri kaydet
        await self._register_default_services()

        # Health check döngüsünü başlat
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        print("[ServiceRegistry] Started")

    async def stop(self) -> None:
        """Registry'yi durdur"""
        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()

        if self._http_client:
            await self._http_client.aclose()

        print("[ServiceRegistry] Stopped")

    async def _register_default_services(self) -> None:
        """Varsayılan servisleri kaydet (environment'tan)"""
        for service_name, config in SERVICE_CONFIGS.items():
            # Environment'tan host/port al
            env_prefix = service_name.value.upper().replace("-", "_")
            host = os.getenv(f"{env_prefix}_HOST", "localhost")
            port = int(os.getenv(f"{env_prefix}_PORT", str(config.default_port)))

            instance = ServiceInstance(
                service_name=service_name,
                host=host,
                port=port,
                health_endpoint=config.health_endpoint,
            )

            await self.register(instance)

    async def register(self, instance: ServiceInstance) -> bool:
        """Servis instance'ı kaydet"""
        if instance.service_name not in self.services:
            self.services[instance.service_name] = []

        # Aynı host:port kombinasyonu var mı kontrol et
        for existing in self.services[instance.service_name]:
            if existing.host == instance.host and existing.port == instance.port:
                # Güncelle
                existing.status = instance.status
                existing.metadata = instance.metadata
                existing.version = instance.version
                print(f"[ServiceRegistry] Updated: {instance.service_name.value} at {instance.base_url}")
                return True

        # Yeni kayıt
        self.services[instance.service_name].append(instance)
        print(f"[ServiceRegistry] Registered: {instance.service_name.value} at {instance.base_url}")
        return True

    async def deregister(self, service_name: ServiceName, host: str, port: int) -> bool:
        """Servis instance'ını kaldır"""
        if service_name not in self.services:
            return False

        self.services[service_name] = [
            s for s in self.services[service_name]
            if not (s.host == host and s.port == port)
        ]

        print(f"[ServiceRegistry] Deregistered: {service_name.value} at {host}:{port}")
        return True

    async def get_service(self, service_name: ServiceName) -> ServiceInstance | None:
        """Sağlıklı bir servis instance'ı al (round-robin)"""
        if service_name not in self.services:
            return None

        healthy_instances = [
            s for s in self.services[service_name]
            if s.status == ServiceStatus.HEALTHY
        ]

        if not healthy_instances:
            # Degraded olanları da kabul et
            healthy_instances = [
                s for s in self.services[service_name]
                if s.status in (ServiceStatus.HEALTHY, ServiceStatus.DEGRADED)
            ]

        if not healthy_instances:
            return None

        # Ağırlıklı random seçim (basit implementasyon)
        import random
        total_weight = sum(s.weight for s in healthy_instances)
        if total_weight == 0:
            return random.choice(healthy_instances)

        r = random.randint(0, total_weight - 1)
        cumulative = 0
        for instance in healthy_instances:
            cumulative += instance.weight
            if r < cumulative:
                return instance

        return healthy_instances[0]

    async def get_all_instances(self, service_name: ServiceName) -> list[ServiceInstance]:
        """Bir servisin tüm instance'larını al"""
        return self.services.get(service_name, [])

    async def _health_check_loop(self) -> None:
        """Periyodik health check döngüsü"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ServiceRegistry] Health check error: {e}")
                await asyncio.sleep(5)

    async def _check_all_services(self) -> None:
        """Tüm servislerin sağlığını kontrol et"""
        tasks = []
        for service_name, instances in self.services.items():
            for instance in instances:
                tasks.append(self._check_service_health(instance))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_service_health(self, instance: ServiceInstance) -> None:
        """Tek bir servisin sağlığını kontrol et"""
        try:
            response = await self._http_client.get(instance.health_url)
            instance.last_health_check = datetime.now(UTC)

            if response.status_code == 200:
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                instance.status = ServiceStatus.HEALTHY
                instance.metadata["last_response"] = data

                # Versiyon bilgisini güncelle
                if "version" in data:
                    instance.version = data["version"]

            elif response.status_code == 503:
                instance.status = ServiceStatus.DEGRADED
            else:
                instance.status = ServiceStatus.UNHEALTHY

        except httpx.ConnectError:
            instance.status = ServiceStatus.UNHEALTHY
            instance.last_health_check = datetime.now(UTC)
        except Exception as e:
            instance.status = ServiceStatus.UNKNOWN
            instance.metadata["error"] = str(e)

    def get_status_summary(self) -> dict[str, Any]:
        """Tüm servislerin durum özeti"""
        summary = {
            "total_services": len(self.services),
            "total_instances": sum(len(instances) for instances in self.services.values()),
            "services": {},
        }

        for service_name, instances in self.services.items():
            healthy = sum(1 for i in instances if i.status == ServiceStatus.HEALTHY)
            unhealthy = sum(1 for i in instances if i.status == ServiceStatus.UNHEALTHY)
            degraded = sum(1 for i in instances if i.status == ServiceStatus.DEGRADED)

            summary["services"][service_name.value] = {
                "instances": len(instances),
                "healthy": healthy,
                "unhealthy": unhealthy,
                "degraded": degraded,
                "status": "healthy" if healthy > 0 else ("degraded" if degraded > 0 else "unhealthy"),
            }

        return summary

    async def get_service_url(self, service_name: ServiceName, path: str = "") -> str | None:
        """Servis URL'i al"""
        instance = await self.get_service(service_name)
        if not instance:
            return None
        return f"{instance.base_url}{path}"


# Global registry instance
_registry: ServiceRegistry | None = None


async def get_service_registry() -> ServiceRegistry:
    """Global service registry instance al"""
    global _registry

    if _registry is None:
        _registry = ServiceRegistry()
        await _registry.start()

    return _registry


# Service discovery yardımcı fonksiyonları
async def discover_service(service_name: ServiceName) -> str | None:
    """Servis URL'ini keşfet"""
    registry = await get_service_registry()
    instance = await registry.get_service(service_name)
    return instance.base_url if instance else None


async def call_service(
    service_name: ServiceName,
    method: str,
    path: str,
    **kwargs,
) -> httpx.Response | None:
    """Servise HTTP çağrısı yap"""
    registry = await get_service_registry()
    instance = await registry.get_service(service_name)

    if not instance:
        print(f"[ServiceRegistry] No healthy instance for {service_name.value}")
        return None

    url = f"{instance.base_url}{path}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"[ServiceRegistry] Call failed to {service_name.value}: {e}")
            # Instance'ı unhealthy olarak işaretle
            instance.status = ServiceStatus.UNHEALTHY
            return None


# Circuit breaker pattern için basit implementasyon
class CircuitBreaker:
    """Basit circuit breaker implementasyonu"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures: dict[str, int] = {}
        self.last_failure_time: dict[str, datetime] = {}
        self.state: dict[str, str] = {}  # closed, open, half-open

    def is_open(self, service: str) -> bool:
        """Circuit açık mı?"""
        if service not in self.state or self.state[service] == "closed":
            return False

        if self.state[service] == "open":
            # Recovery timeout geçti mi?
            last_failure = self.last_failure_time.get(service)
            if last_failure:
                elapsed = (datetime.now(UTC) - last_failure).total_seconds()
                if elapsed > self.recovery_timeout:
                    self.state[service] = "half-open"
                    return False
            return True

        return False  # half-open

    def record_success(self, service: str) -> None:
        """Başarılı çağrı kaydet"""
        self.failures[service] = 0
        self.state[service] = "closed"

    def record_failure(self, service: str) -> None:
        """Başarısız çağrı kaydet"""
        self.failures[service] = self.failures.get(service, 0) + 1
        self.last_failure_time[service] = datetime.now(UTC)

        if self.failures[service] >= self.failure_threshold:
            self.state[service] = "open"
            print(f"[CircuitBreaker] Circuit opened for {service}")


# Global circuit breaker
circuit_breaker = CircuitBreaker()


async def call_service_with_circuit_breaker(
    service_name: ServiceName,
    method: str,
    path: str,
    **kwargs,
) -> httpx.Response | None:
    """Circuit breaker ile servise çağrı yap"""
    service_key = service_name.value

    if circuit_breaker.is_open(service_key):
        print(f"[CircuitBreaker] Circuit open for {service_key}, skipping call")
        return None

    response = await call_service(service_name, method, path, **kwargs)

    if response and response.status_code < 500:
        circuit_breaker.record_success(service_key)
    else:
        circuit_breaker.record_failure(service_key)

    return response
