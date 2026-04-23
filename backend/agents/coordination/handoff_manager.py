"""
Handoff Manager - Agent Delegation Service (REQ-7.1-7.6)
Teknofest 2025 - KIRO2 YKS Platformu

Agent handoff ve delegation yonetimi:
- Capability-based target agent selection (REQ-7.1)
- Minimal context transfer (REQ-7.2)
- Acknowledgment mesajlari (REQ-7.3)
- Failure rollback mekanizmasi (REQ-7.4)
- Chain limit enforcement - max 5 (REQ-7.5)
- Metrics tracking (REQ-7.6)

Boris Cherny Standards: Verification feedback loops
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Configuration from spec REQ-7.5
MAX_HANDOFF_CHAIN_LENGTH = 5

# Capability to domain mapping
CAPABILITY_DOMAIN_MAP = {
    "math": "matematik",
    "matematik": "matematik",
    "physics": "fizik",
    "fizik": "fizik",
    "chemistry": "kimya",
    "kimya": "kimya",
    "biology": "biyoloji",
    "biyoloji": "biyoloji",
    "turkish": "turkce",
    "turkce": "turkce",
    "social": "sosyal",
    "sosyal": "sosyal",
    "foreign_language": "yabanci_dil",
    "yabanci_dil": "yabanci_dil",
    "english": "yabanci_dil",
}

# Required context fields per capability (REQ-7.2)
CAPABILITY_REQUIRED_CONTEXT = {
    "matematik": ["question", "student_level", "topic"],
    "fizik": ["question", "student_level", "topic", "formulas"],
    "kimya": ["question", "student_level", "topic", "elements"],
    "biyoloji": ["question", "student_level", "topic"],
    "turkce": ["question", "student_level", "topic", "text_type"],
    "sosyal": ["question", "student_level", "topic", "period"],
    "yabanci_dil": ["question", "student_level", "topic", "language"],
    "default": ["question", "student_level"],
}


@dataclass
class HandoffRequest:
    """Handoff istegi veri yapisi."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: str = ""
    target_capability: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    chain_depth: int = 0
    chain_id: str | None = None
    parent_handoff_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    timeout_seconds: float = 30.0


@dataclass
class HandoffResult:
    """Handoff sonucu veri yapisi."""

    success: bool
    request_id: str = ""
    target_agent: str | None = None
    rejected: bool = False
    reason: str | None = None
    chain_depth: int = 0
    latency_ms: float = 0.0
    context_transferred: dict[str, Any] = field(default_factory=dict)
    acknowledgment_received: bool = False


@dataclass
class HandoffMetrics:
    """Handoff metrikleri (REQ-7.6)."""

    total_handoffs: int = 0
    successful_handoffs: int = 0
    failed_handoffs: int = 0
    chain_limit_rejections: int = 0
    rollbacks: int = 0
    max_chain_observed: int = 0
    total_latency_ms: float = 0.0
    average_latency_ms: float = 0.0


class HandoffManager:
    """
    Agent Handoff Manager (REQ-7.1-7.6)

    Agent'lar arasi gorev devri yonetimi.

    Attributes:
        max_chain_depth: Maksimum handoff zincir derinligi (default 5)
        timeout_seconds: Handoff timeout suresi
    """

    def __init__(
        self,
        max_chain_depth: int = MAX_HANDOFF_CHAIN_LENGTH,
        timeout_seconds: float = 30.0,
    ):
        """
        HandoffManager olustur.

        Args:
            max_chain_depth: Maksimum zincir derinligi (REQ-7.5)
            timeout_seconds: Handoff timeout suresi
        """
        self.max_chain_depth = max_chain_depth
        self.timeout_seconds = timeout_seconds

        # Agent registry (domain -> agent list)
        self._agent_registry: dict[str, list[str]] = {}

        # Active handoffs
        self._active_handoffs: dict[str, HandoffRequest] = {}

        # Handoff chains for tracking
        self._handoff_chains: dict[str, list[str]] = {}

        # Metrics (REQ-7.6)
        self.metrics = HandoffMetrics()

        # Callbacks
        self._acknowledgment_callbacks: dict[str, Callable] = {}

        logger.info(
            f"HandoffManager initialized: max_chain_depth={max_chain_depth}, "
            f"timeout={timeout_seconds}s"
        )

    def register_agent(self, agent_id: str, capabilities: list[str]) -> bool:
        """
        Agent'i handoff sisteme kaydet.

        Args:
            agent_id: Agent kimlik bilgisi
            capabilities: Agent'in yetenekleri

        Returns:
            Basarili ise True
        """
        for capability in capabilities:
            domain = CAPABILITY_DOMAIN_MAP.get(capability, capability)
            if domain not in self._agent_registry:
                self._agent_registry[domain] = []
            if agent_id not in self._agent_registry[domain]:
                self._agent_registry[domain].append(agent_id)
                logger.debug(f"Agent {agent_id} registered for {domain}")

        return True

    def deregister_agent(self, agent_id: str) -> bool:
        """
        Agent'i handoff sistemden cikar.

        Args:
            agent_id: Agent kimlik bilgisi

        Returns:
            Basarili ise True
        """
        removed = False
        for domain, agents in self._agent_registry.items():
            if agent_id in agents:
                agents.remove(agent_id)
                removed = True
                logger.debug(f"Agent {agent_id} deregistered from {domain}")

        return removed

    async def initiate_handoff(
        self,
        source_agent: str,
        target_capability: str,
        context: dict[str, Any],
        chain_depth: int = 0,
        chain_id: str | None = None,
        parent_handoff_id: str | None = None,
    ) -> HandoffResult:
        """
        Agent handoff baslat (REQ-7.1).

        Args:
            source_agent: Kaynak agent
            target_capability: Hedef yetenek
            context: Aktarilacak context
            chain_depth: Mevcut zincir derinligi
            chain_id: Zincir kimlik bilgisi
            parent_handoff_id: Ebeveyn handoff ID

        Returns:
            HandoffResult ile sonuc
        """
        start_time = time.perf_counter()
        chain_id = chain_id or str(uuid.uuid4())

        # Create request
        request = HandoffRequest(
            source_agent=source_agent,
            target_capability=target_capability,
            context=context,
            chain_depth=chain_depth,
            chain_id=chain_id,
            parent_handoff_id=parent_handoff_id,
            timeout_seconds=self.timeout_seconds,
        )

        # REQ-7.5: Check chain limit
        if chain_depth >= self.max_chain_depth:
            self.metrics.chain_limit_rejections += 1
            logger.warning(
                f"Handoff chain limit exceeded: depth={chain_depth}, "
                f"max={self.max_chain_depth}"
            )
            return HandoffResult(
                success=False,
                request_id=request.request_id,
                rejected=True,
                reason="chain_limit_exceeded",
                chain_depth=chain_depth,
            )

        # REQ-7.1: Select target agent by capability
        domain = CAPABILITY_DOMAIN_MAP.get(target_capability, target_capability)
        target_agent = self._select_target_agent(domain, source_agent)

        if not target_agent:
            self.metrics.failed_handoffs += 1
            logger.warning(f"No suitable agent found for capability: {target_capability}")
            return HandoffResult(
                success=False,
                request_id=request.request_id,
                reason="no_suitable_agent_found",
                chain_depth=chain_depth,
            )

        # REQ-7.2: Extract minimal context
        minimal_context = self._extract_minimal_context(context, domain)
        request.context = minimal_context

        # Track active handoff
        self._active_handoffs[request.request_id] = request

        # Track chain
        if chain_id not in self._handoff_chains:
            self._handoff_chains[chain_id] = []
        self._handoff_chains[chain_id].append(request.request_id)

        try:
            # Execute handoff with timeout
            success = await asyncio.wait_for(
                self._execute_handoff(request, target_agent),
                timeout=self.timeout_seconds,
            )

            if success:
                # REQ-7.3: Send acknowledgment
                await self._send_acknowledgment(source_agent, request.request_id, True)

                # Update metrics
                self.metrics.successful_handoffs += 1
            else:
                # REQ-7.4: Rollback on failure
                await self._rollback_handoff(request, source_agent)
                self.metrics.failed_handoffs += 1

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_metrics(success, latency_ms, chain_depth + 1)

            return HandoffResult(
                success=success,
                request_id=request.request_id,
                target_agent=target_agent,
                chain_depth=chain_depth + 1,
                latency_ms=latency_ms,
                context_transferred=minimal_context,
                acknowledgment_received=success,
            )

        except TimeoutError:
            # REQ-7.4: Rollback on timeout
            await self._rollback_handoff(request, source_agent)
            self.metrics.failed_handoffs += 1
            self.metrics.rollbacks += 1

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Handoff timeout after {latency_ms:.2f}ms: {request.request_id}")

            return HandoffResult(
                success=False,
                request_id=request.request_id,
                reason="handoff_timeout",
                chain_depth=chain_depth,
                latency_ms=latency_ms,
            )

        except Exception as e:
            # REQ-7.4: Rollback on error
            await self._rollback_handoff(request, source_agent)
            self.metrics.failed_handoffs += 1
            self.metrics.rollbacks += 1

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Handoff error: {e}")

            return HandoffResult(
                success=False,
                request_id=request.request_id,
                reason=f"handoff_error: {e!s}",
                chain_depth=chain_depth,
                latency_ms=latency_ms,
            )

        finally:
            # Cleanup
            self._active_handoffs.pop(request.request_id, None)

    def _select_target_agent(
        self, domain: str, exclude_agent: str
    ) -> str | None:
        """
        Hedef agent sec (REQ-7.1).

        Round-robin load balancing ile agent secer.

        Args:
            domain: Hedef domain
            exclude_agent: Haric tutulacak agent

        Returns:
            Agent ID veya None
        """
        agents = self._agent_registry.get(domain, [])
        available = [a for a in agents if a != exclude_agent]

        if not available:
            return None

        # Simple round-robin (first available)
        return available[0]

    def _extract_minimal_context(
        self, full_context: dict[str, Any], domain: str
    ) -> dict[str, Any]:
        """
        Minimal context cikar (REQ-7.2).

        Sadece hedef domain icin gerekli alanlari aktarir.

        Args:
            full_context: Tam context
            domain: Hedef domain

        Returns:
            Minimal context
        """
        required_fields = CAPABILITY_REQUIRED_CONTEXT.get(
            domain, CAPABILITY_REQUIRED_CONTEXT["default"]
        )

        minimal = {}
        for field in required_fields:
            if field in full_context:
                minimal[field] = full_context[field]

        # Always include essential metadata
        for meta_field in ["session_id", "user_id", "correlation_id"]:
            if meta_field in full_context:
                minimal[meta_field] = full_context[meta_field]

        logger.debug(
            f"Context minimized: {len(full_context)} -> {len(minimal)} fields"
        )
        return minimal

    async def _execute_handoff(
        self, request: HandoffRequest, target_agent: str
    ) -> bool:
        """
        Handoff'u calistir.

        Args:
            request: Handoff istegi
            target_agent: Hedef agent

        Returns:
            Basarili ise True
        """
        # Simulate handoff execution (in real impl, this would message the target agent)
        logger.info(
            f"Executing handoff: {request.source_agent} -> {target_agent}, "
            f"capability={request.target_capability}"
        )

        # In production, this would:
        # 1. Send message to target agent via blackboard
        # 2. Wait for acknowledgment
        # 3. Verify target agent accepted the task

        # Simulated success
        await asyncio.sleep(0.001)  # Minimal delay for async
        return True

    async def _send_acknowledgment(
        self, source_agent: str, request_id: str, success: bool
    ) -> None:
        """
        Kaynak agent'a acknowledgment gonder (REQ-7.3).

        Args:
            source_agent: Kaynak agent
            request_id: Istek ID
            success: Basari durumu
        """
        logger.debug(
            f"Sending acknowledgment to {source_agent}: "
            f"request={request_id}, success={success}"
        )

        # Call registered callback if exists
        callback = self._acknowledgment_callbacks.get(source_agent)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(request_id, success)
                else:
                    callback(request_id, success)
            except Exception as e:
                logger.error(f"Acknowledgment callback error: {e}")

    async def _rollback_handoff(
        self, request: HandoffRequest, source_agent: str
    ) -> None:
        """
        Handoff'u geri al (REQ-7.4).

        Args:
            request: Handoff istegi
            source_agent: Kaynak agent
        """
        logger.warning(
            f"Rolling back handoff: {request.request_id}, "
            f"returning to {source_agent}"
        )

        # Notify source agent of failure
        await self._send_acknowledgment(source_agent, request.request_id, False)

        # Remove from chain
        chain_id = request.chain_id
        if chain_id and chain_id in self._handoff_chains:
            chain = self._handoff_chains[chain_id]
            if request.request_id in chain:
                chain.remove(request.request_id)

    def _update_metrics(
        self, success: bool, latency_ms: float, chain_depth: int
    ) -> None:
        """
        Metrikleri guncelle (REQ-7.6).

        Args:
            success: Basari durumu
            latency_ms: Gecikme suresi
            chain_depth: Zincir derinligi
        """
        self.metrics.total_handoffs += 1
        self.metrics.total_latency_ms += latency_ms

        # Update average
        self.metrics.average_latency_ms = (
            self.metrics.total_latency_ms / self.metrics.total_handoffs
        )

        # Update max chain
        self.metrics.max_chain_observed = max(self.metrics.max_chain_observed, chain_depth)

    def register_acknowledgment_callback(
        self, agent_id: str, callback: Callable
    ) -> None:
        """
        Acknowledgment callback kaydet.

        Args:
            agent_id: Agent ID
            callback: Callback fonksiyonu
        """
        self._acknowledgment_callbacks[agent_id] = callback

    def get_chain_depth(self, chain_id: str) -> int:
        """
        Zincir derinligini al.

        Args:
            chain_id: Zincir ID

        Returns:
            Derinlik
        """
        return len(self._handoff_chains.get(chain_id, []))

    def get_metrics(self) -> dict[str, Any]:
        """
        Metrikleri al (REQ-7.6).

        Returns:
            Metrik sozlugu
        """
        return {
            "total_handoffs": self.metrics.total_handoffs,
            "successful_handoffs": self.metrics.successful_handoffs,
            "failed_handoffs": self.metrics.failed_handoffs,
            "chain_limit_rejections": self.metrics.chain_limit_rejections,
            "rollbacks": self.metrics.rollbacks,
            "max_chain_observed": self.metrics.max_chain_observed,
            "average_latency_ms": round(self.metrics.average_latency_ms, 2),
            "success_rate": (
                self.metrics.successful_handoffs / self.metrics.total_handoffs * 100
                if self.metrics.total_handoffs > 0
                else 0.0
            ),
        }

    def clear_chain(self, chain_id: str) -> None:
        """
        Zinciri temizle.

        Args:
            chain_id: Zincir ID
        """
        self._handoff_chains.pop(chain_id, None)


# Singleton instance
_handoff_manager: HandoffManager | None = None


def get_handoff_manager() -> HandoffManager:
    """
    Singleton HandoffManager instance al.

    Returns:
        HandoffManager instance
    """
    global _handoff_manager
    if _handoff_manager is None:
        _handoff_manager = HandoffManager()
    return _handoff_manager
