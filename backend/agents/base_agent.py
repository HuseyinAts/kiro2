"""
Base Agent Sınıfı - Tüm AI Agent'lar için temel interface
Teknofest 2025 - Eğitim Eylemci Projesi

Bu sınıf:
- Tüm agent'lar için ortak interface sağlar
- Agent koordinasyonu için temel metodları içerir
- Blackboard pattern ile iletişim altyapısını sunar
- Logging ve error handling standardını belirler
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent tipleri"""

    LEARNING_PATH = "learning_path"
    STUDY_BUDDY = "study_buddy"
    ACCESSIBILITY = "accessibility"
    CONTENT_MANAGER = "content_manager"
    ASSESSMENT = "assessment"


class AgentStatus(Enum):
    """Agent durumları"""

    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    OFFLINE = "offline"


class MessageType(Enum):
    """Agent mesaj tipleri"""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    COORDINATION = "coordination"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Agent mesajı"""

    message_id: str
    sender_agent: str
    receiver_agent: str | None  # None = broadcast
    message_type: MessageType
    content: dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high
    requires_response: bool = False
    correlation_id: str | None = None  # İlişkili mesajlar için


@dataclass
class AgentCapability:
    """Agent yeteneği"""

    name: str
    description: str
    input_types: list[str]
    output_types: list[str]
    parameters: dict[str, Any]
    performance_metrics: dict[str, float]


@dataclass
class AgentMetrics:
    """Agent performans metrikleri"""

    agent_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_activity: datetime | None = None
    uptime_percentage: float = 100.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


class BaseAgent(ABC):
    """Tüm AI Agent'lar için temel sınıf"""

    def __init__(
        self, agent_id: str, agent_type: AgentType, name: str, description: str
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities: list[AgentCapability] = []
        self.metrics = AgentMetrics(agent_id=agent_id)
        self.message_queue: list[AgentMessage] = []
        self.blackboard_subscriptions: list[str] = []
        self.coordination_handlers: dict[str, callable] = {}
        self.error_handlers: dict[str, callable] = {}

        # Agent-specific configuration
        self.config: dict[str, Any] = {}
        self.cache: dict[str, Any] = {}

        # Blackboard integration
        self.blackboard = None
        self.last_activity = datetime.now()

        # Initialize agent
        self._initialize()

    def _initialize(self):
        """Agent başlatma - alt sınıflar override edebilir"""
        logger.info(f"Initializing agent: {self.agent_id} ({self.agent_type.value})")
        self.status = AgentStatus.IDLE
        self.metrics.last_activity = datetime.now()

    @abstractmethod
    async def process_request(
        self,
        request_type: str,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Ana işlem metodu - her agent kendi implementasyonunu yapar

        Args:
            request_type: İstek tipi
            parameters: İstek parametreleri
            context: Ek bağlam bilgisi

        Returns:
            İşlem sonucu
        """

    def register_to_blackboard(self, blackboard):
        """Agent'ı blackboard sistemine kaydet"""
        try:
            self.blackboard = blackboard
            success = blackboard.register_agent(self.agent_id, self)

            if success:
                logger.info(f"Agent registered to blackboard: {self.agent_id}")
                # Temel olaylara abone ol
                self._setup_default_subscriptions()
            else:
                logger.error(f"Failed to register agent to blackboard: {self.agent_id}")

            return success

        except Exception as e:
            logger.error(f"Blackboard registration error: {self.agent_id}, error: {e}")
            return False

    def _setup_default_subscriptions(self):
        """Varsayılan blackboard aboneliklerini kur"""
        try:
            from ..algorithms.multi_agent_blackboard import EventType, Priority

            # Tüm agent'lar koordinasyon olaylarına abone olur
            self.blackboard.subscribe(
                agent_name=self.agent_id,
                event_types=[
                    EventType.COORDINATION_REQUEST,
                    EventType.COORDINATION_RESPONSE,
                    EventType.EMERGENCY_ALERT,
                ],
                key_patterns=[f"*{self.agent_type.value}*", "coordination_*"],
                priority_filter=Priority.MEDIUM,
            )

            logger.info(f"Default subscriptions set up for agent: {self.agent_id}")

        except Exception as e:
            logger.error(
                f"Default subscription setup error: {self.agent_id}, error: {e}"
            )

    async def on_blackboard_update(
        self, key: str, value: Any, source_agent: str, event_type
    ):
        """
        Blackboard güncellemesi callback'i
        Alt sınıflar bu metodu override edebilir
        """
        try:
            self.last_activity = datetime.now()

            logger.debug(
                f"Blackboard update received by {self.agent_id}: {key} from {source_agent}"
            )

            # Koordinasyon talebi kontrolü
            if "coordination_" in key and source_agent != self.agent_id:
                await self._handle_coordination_request(key, value, source_agent)

            # Alt sınıfların kendi implementasyonu için
            await self._process_blackboard_update(key, value, source_agent, event_type)

        except Exception as e:
            logger.error(
                f"Blackboard update handling error: {self.agent_id}, error: {e}"
            )

    async def _process_blackboard_update(
        self, key: str, value: Any, source_agent: str, event_type
    ):
        """
        Alt sınıfların override edebileceği blackboard update işleme metodu
        """

    async def _handle_coordination_request(
        self, key: str, value: Any, source_agent: str
    ):
        """Koordinasyon talebini işle"""
        try:
            if not isinstance(value, dict):
                return

            coordination_type = value.get("type")
            coordination_id = value.get("coordination_id")
            parameters = value.get("parameters", {})

            # Bu agent'a yönelik mi kontrol et
            if self.agent_id not in value.get("target_agents", []):
                return

            logger.info(
                f"Coordination request received: {coordination_type} from {source_agent}"
            )

            # Koordinasyon tipine göre işlem yap
            response_data = await self._process_coordination_request(
                coordination_type, parameters, source_agent
            )

            # Yanıtı blackboard'a yaz
            if self.blackboard and coordination_id:
                await self.blackboard.respond_to_coordination(
                    coordination_id=coordination_id,
                    responding_agent=self.agent_id,
                    response_data=response_data,
                )

        except Exception as e:
            logger.error(
                f"Coordination request handling error: {self.agent_id}, error: {e}"
            )

    async def _process_coordination_request(
        self, coordination_type: str, parameters: dict[str, Any], source_agent: str
    ) -> dict[str, Any]:
        """
        Koordinasyon talebini işle - alt sınıflar override edebilir
        """
        return {
            "status": "acknowledged",
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "message": f"Coordination request acknowledged: {coordination_type}",
        }

    async def write_to_blackboard(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        metadata: dict[str, Any] = None,
    ) -> bool:
        """Blackboard'a veri yaz"""
        try:
            if not self.blackboard:
                logger.warning(f"Agent {self.agent_id} not connected to blackboard")
                return False

            from ..algorithms.multi_agent_blackboard import Priority

            success = await self.blackboard.write(
                key=key,
                value=value,
                source_agent=self.agent_id,
                ttl_seconds=ttl_seconds,
                metadata=metadata,
                priority=Priority.MEDIUM,
            )

            if success:
                self.last_activity = datetime.now()
                logger.debug(f"Data written to blackboard by {self.agent_id}: {key}")

            return success

        except Exception as e:
            logger.error(f"Blackboard write error: {self.agent_id}, error: {e}")
            return False

    def read_from_blackboard(self, key: str) -> Any | None:
        """Blackboard'dan veri oku"""
        try:
            if not self.blackboard:
                logger.warning(f"Agent {self.agent_id} not connected to blackboard")
                return None

            value = self.blackboard.read(key, self.agent_id)

            if value is not None:
                self.last_activity = datetime.now()
                logger.debug(f"Data read from blackboard by {self.agent_id}: {key}")

            return value

        except Exception as e:
            logger.error(f"Blackboard read error: {self.agent_id}, error: {e}")
            return None

    async def request_coordination(
        self,
        target_agents: list[str],
        coordination_type: str,
        parameters: dict[str, Any],
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """Diğer agent'larla koordinasyon talep et"""
        try:
            if not self.blackboard:
                logger.warning(f"Agent {self.agent_id} not connected to blackboard")
                return {"success": False, "error": "not_connected_to_blackboard"}

            result = await self.blackboard.request_coordination(
                requester_agent=self.agent_id,
                target_agents=target_agents,
                coordination_type=coordination_type,
                parameters=parameters,
                timeout_seconds=timeout_seconds,
            )

            self.last_activity = datetime.now()
            logger.info(
                f"Coordination requested by {self.agent_id}: {coordination_type}"
            )

            return result

        except Exception as e:
            logger.error(f"Coordination request error: {self.agent_id}, error: {e}")
            return {"success": False, "error": str(e)}

    def get_agent_metrics(self) -> dict[str, Any]:
        """Agent metriklerini al"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "last_activity": self.last_activity.isoformat()
            if self.last_activity
            else None,
            "capabilities_count": len(self.capabilities),
            "subscriptions_count": len(self.blackboard_subscriptions),
            "cache_size": len(self.cache),
            "blackboard_connected": self.blackboard is not None,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "avg_response_time": self.metrics.avg_response_time,
                "uptime_percentage": self.metrics.uptime_percentage,
            },
        }
