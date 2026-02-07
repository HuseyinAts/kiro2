"""
Agent Health Checker - Background Health Monitoring (REQ-3.5, REQ-3.6)
Teknofest 2025 - KIRO2 YKS Platformu

Agent saglik izleme:
- 30 saniyede bir ping (REQ-3.5)
- 60s yanitsiz -> unhealthy isaretle
- 5 dakika unhealthy -> auto-deregister (REQ-3.6)
- agent_down event publish

Boris Cherny Standards: Verification feedback loops
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Configuration from spec REQ-3.5, REQ-3.6
HEALTH_CHECK_INTERVAL = 30  # seconds
UNHEALTHY_THRESHOLD = 60  # seconds without response
DEREGISTER_THRESHOLD = 300  # 5 minutes
PING_TIMEOUT = 5  # seconds


class AgentStatus(Enum):
    """Agent durum enumlari."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEREGISTERED = "deregistered"
    UNKNOWN = "unknown"


@dataclass
class AgentHealthStatus:
    """Agent saglik durumu."""

    agent_id: str
    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: datetime = field(default_factory=datetime.now)
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    successful_checks: int = 0
    response_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Basari orani."""
        if self.total_checks == 0:
            return 0.0
        return self.successful_checks / self.total_checks * 100


@dataclass
class HealthCheckResult:
    """Saglik kontrolu sonucu."""

    agent_id: str
    is_healthy: bool
    response_time_ms: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class AgentHealthChecker:
    """
    Agent Health Check Background Task (REQ-3.5, REQ-3.6)

    Agent sagligini izler ve unhealthy olanlari deregister eder.

    Attributes:
        check_interval: Kontrol araligi (default 30s)
        unhealthy_threshold: Unhealthy esigi (default 60s)
        deregister_threshold: Deregister esigi (default 5 dakika)
    """

    def __init__(
        self,
        check_interval: int = HEALTH_CHECK_INTERVAL,
        unhealthy_threshold: int = UNHEALTHY_THRESHOLD,
        deregister_threshold: int = DEREGISTER_THRESHOLD,
        ping_timeout: int = PING_TIMEOUT,
    ):
        """
        AgentHealthChecker olustur.

        Args:
            check_interval: Kontrol araligi (saniye)
            unhealthy_threshold: Unhealthy esigi (saniye)
            deregister_threshold: Deregister esigi (saniye)
            ping_timeout: Ping timeout (saniye)
        """
        self.check_interval = check_interval
        self.unhealthy_threshold = unhealthy_threshold
        self.deregister_threshold = deregister_threshold
        self.ping_timeout = ping_timeout

        # Agent health status tracking
        self._agent_health: Dict[str, AgentHealthStatus] = {}

        # Agent registry reference (set externally)
        self._agent_registry: Dict[str, Any] = {}

        # Background task
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Callbacks
        self._on_unhealthy_callbacks: List[Callable] = []
        self._on_healthy_callbacks: List[Callable] = []
        self._on_deregister_callbacks: List[Callable] = []

        # Blackboard reference for event publishing
        self._blackboard: Optional[Any] = None

        logger.info(
            f"AgentHealthChecker initialized: interval={check_interval}s, "
            f"unhealthy={unhealthy_threshold}s, deregister={deregister_threshold}s"
        )

    def set_agent_registry(self, registry: Dict[str, Any]) -> None:
        """
        Agent registry referansini ayarla.

        Args:
            registry: Agent registry dict
        """
        self._agent_registry = registry

    def set_blackboard(self, blackboard: Any) -> None:
        """
        Blackboard referansini ayarla.

        Args:
            blackboard: Blackboard instance
        """
        self._blackboard = blackboard

    async def start(self) -> None:
        """Health check background task'i baslat."""
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info("Agent health checker started")

    async def stop(self) -> None:
        """Health check background task'i durdur."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Agent health checker stopped")

    async def _health_check_loop(self) -> None:
        """
        Ana health check dongusu (REQ-3.5).

        Her 30 saniyede bir tum agent'lari kontrol eder.
        """
        while self._running:
            try:
                await self._check_all_agents()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _check_all_agents(self) -> None:
        """Tum kayitli agent'lari kontrol et."""
        now = datetime.now()
        agents_to_check = list(self._agent_registry.keys())

        for agent_id in agents_to_check:
            try:
                result = await self._check_agent(agent_id)
                await self._process_check_result(agent_id, result, now)
            except Exception as e:
                logger.error(f"Error checking agent {agent_id}: {e}")

    async def _check_agent(self, agent_id: str) -> HealthCheckResult:
        """
        Tek bir agent'i kontrol et (REQ-3.5).

        Args:
            agent_id: Agent ID

        Returns:
            HealthCheckResult
        """
        start_time = time.perf_counter()

        try:
            agent_ref = self._agent_registry.get(agent_id)
            if not agent_ref:
                return HealthCheckResult(
                    agent_id=agent_id,
                    is_healthy=False,
                    error="agent_not_found",
                )

            # Get actual agent (might be weakref)
            agent = agent_ref() if callable(agent_ref) else agent_ref
            if not agent:
                return HealthCheckResult(
                    agent_id=agent_id,
                    is_healthy=False,
                    error="agent_reference_invalid",
                )

            # Try to ping the agent
            is_healthy = await self._ping_agent(agent, agent_id)

            response_time = (time.perf_counter() - start_time) * 1000

            return HealthCheckResult(
                agent_id=agent_id,
                is_healthy=is_healthy,
                response_time_ms=response_time,
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                agent_id=agent_id,
                is_healthy=False,
                error="ping_timeout",
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as e:
            return HealthCheckResult(
                agent_id=agent_id,
                is_healthy=False,
                error=str(e),
                response_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    async def _ping_agent(self, agent: Any, agent_id: str) -> bool:
        """
        Agent'a ping at.

        Args:
            agent: Agent instance
            agent_id: Agent ID

        Returns:
            Healthy ise True
        """
        # Try health_check method if available
        if hasattr(agent, "health_check"):
            try:
                result = await asyncio.wait_for(
                    agent.health_check()
                    if asyncio.iscoroutinefunction(agent.health_check)
                    else asyncio.to_thread(agent.health_check),
                    timeout=self.ping_timeout,
                )
                return bool(result)
            except Exception:
                return False

        # Try is_healthy property
        if hasattr(agent, "is_healthy"):
            return bool(agent.is_healthy)

        # Try status attribute
        if hasattr(agent, "status"):
            return agent.status in ("healthy", "active", "ready")

        # Assume healthy if no health check method
        logger.debug(f"Agent {agent_id} has no health check method, assuming healthy")
        return True

    async def _process_check_result(
        self,
        agent_id: str,
        result: HealthCheckResult,
        now: datetime,
    ) -> None:
        """
        Saglik kontrolu sonucunu isle.

        Args:
            agent_id: Agent ID
            result: Kontrol sonucu
            now: Mevcut zaman
        """
        # Get or create health status
        if agent_id not in self._agent_health:
            self._agent_health[agent_id] = AgentHealthStatus(agent_id=agent_id)

        status = self._agent_health[agent_id]
        status.last_check = now
        status.total_checks += 1
        status.response_time_ms = result.response_time_ms

        if result.is_healthy:
            # Agent is healthy
            status.last_seen = now
            status.consecutive_failures = 0
            status.successful_checks += 1

            if status.status != AgentStatus.HEALTHY:
                status.status = AgentStatus.HEALTHY
                await self._on_agent_healthy(agent_id)
                logger.info(f"Agent {agent_id} is now healthy")
        else:
            # Agent is not healthy
            status.consecutive_failures += 1

            # Calculate time since last seen
            time_since_last_seen = (now - status.last_seen).total_seconds()

            # REQ-3.6: Auto-deregister after threshold
            if time_since_last_seen >= self.deregister_threshold:
                if status.status != AgentStatus.DEREGISTERED:
                    await self._deregister_agent(agent_id)
                    status.status = AgentStatus.DEREGISTERED
                    logger.warning(
                        f"Agent {agent_id} deregistered after "
                        f"{time_since_last_seen:.0f}s of being unhealthy"
                    )

            # Mark as unhealthy after threshold
            elif time_since_last_seen >= self.unhealthy_threshold:
                if status.status == AgentStatus.HEALTHY:
                    status.status = AgentStatus.UNHEALTHY
                    await self._on_agent_unhealthy(agent_id)
                    logger.warning(
                        f"Agent {agent_id} marked unhealthy after "
                        f"{status.consecutive_failures} consecutive failures"
                    )

    async def _on_agent_unhealthy(self, agent_id: str) -> None:
        """
        Agent unhealthy oldugunda.

        Args:
            agent_id: Agent ID
        """
        # Publish event
        if self._blackboard:
            try:
                await self._blackboard.publish_event(
                    event_type="agent_unhealthy",
                    data={"agent_id": agent_id},
                    source_agent="health_checker",
                )
            except Exception as e:
                logger.error(f"Failed to publish agent_unhealthy event: {e}")

        # Trigger callbacks
        for callback in self._on_unhealthy_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id)
                else:
                    callback(agent_id)
            except Exception as e:
                logger.error(f"Unhealthy callback error: {e}")

    async def _on_agent_healthy(self, agent_id: str) -> None:
        """
        Agent healthy oldugunda.

        Args:
            agent_id: Agent ID
        """
        # Trigger callbacks
        for callback in self._on_healthy_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id)
                else:
                    callback(agent_id)
            except Exception as e:
                logger.error(f"Healthy callback error: {e}")

    async def _deregister_agent(self, agent_id: str) -> None:
        """
        Agent'i deregister et (REQ-3.6).

        Args:
            agent_id: Agent ID
        """
        # Publish event
        if self._blackboard:
            try:
                await self._blackboard.publish_event(
                    event_type="agent_down",
                    data={"agent_id": agent_id, "reason": "health_check_failed"},
                    source_agent="health_checker",
                )
            except Exception as e:
                logger.error(f"Failed to publish agent_down event: {e}")

        # Remove from registry
        if agent_id in self._agent_registry:
            del self._agent_registry[agent_id]

        # Trigger callbacks
        for callback in self._on_deregister_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id)
                else:
                    callback(agent_id)
            except Exception as e:
                logger.error(f"Deregister callback error: {e}")

    def register_agent(self, agent_id: str, agent: Any) -> None:
        """
        Agent'i kaydet.

        Args:
            agent_id: Agent ID
            agent: Agent instance
        """
        self._agent_registry[agent_id] = agent
        self._agent_health[agent_id] = AgentHealthStatus(
            agent_id=agent_id,
            status=AgentStatus.HEALTHY,
            last_seen=datetime.now(),
        )
        logger.debug(f"Agent {agent_id} registered for health monitoring")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Agent'i kayittan cikar.

        Args:
            agent_id: Agent ID
        """
        self._agent_registry.pop(agent_id, None)
        self._agent_health.pop(agent_id, None)
        logger.debug(f"Agent {agent_id} unregistered from health monitoring")

    def get_agent_status(self, agent_id: str) -> Optional[AgentHealthStatus]:
        """
        Agent saglik durumunu al.

        Args:
            agent_id: Agent ID

        Returns:
            AgentHealthStatus veya None
        """
        return self._agent_health.get(agent_id)

    def get_all_statuses(self) -> Dict[str, AgentHealthStatus]:
        """Tum agent durumlari."""
        return self._agent_health.copy()

    def get_healthy_agents(self) -> List[str]:
        """Healthy agent listesi."""
        return [
            agent_id
            for agent_id, status in self._agent_health.items()
            if status.status == AgentStatus.HEALTHY
        ]

    def get_unhealthy_agents(self) -> List[str]:
        """Unhealthy agent listesi."""
        return [
            agent_id
            for agent_id, status in self._agent_health.items()
            if status.status == AgentStatus.UNHEALTHY
        ]

    # Callback registration
    def on_unhealthy(self, callback: Callable) -> None:
        """Unhealthy callback kaydet."""
        self._on_unhealthy_callbacks.append(callback)

    def on_healthy(self, callback: Callable) -> None:
        """Healthy callback kaydet."""
        self._on_healthy_callbacks.append(callback)

    def on_deregister(self, callback: Callable) -> None:
        """Deregister callback kaydet."""
        self._on_deregister_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Metrikleri al.

        Returns:
            Metrik sozlugu
        """
        total_agents = len(self._agent_health)
        healthy_count = len(self.get_healthy_agents())
        unhealthy_count = len(self.get_unhealthy_agents())

        avg_response_time = 0.0
        if total_agents > 0:
            avg_response_time = sum(
                s.response_time_ms for s in self._agent_health.values()
            ) / total_agents

        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_count,
            "unhealthy_agents": unhealthy_count,
            "health_rate": healthy_count / total_agents * 100 if total_agents > 0 else 0,
            "average_response_time_ms": round(avg_response_time, 2),
            "check_interval_seconds": self.check_interval,
            "is_running": self._running,
        }


# Singleton instance
_health_checker: Optional[AgentHealthChecker] = None


def get_health_checker() -> AgentHealthChecker:
    """
    Singleton AgentHealthChecker instance al.

    Returns:
        AgentHealthChecker instance
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = AgentHealthChecker()
    return _health_checker
