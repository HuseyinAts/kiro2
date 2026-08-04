"""
Multi-Agent Blackboard Sistemi - Devrimsel Özellik #7
Teknofest 2025 - Eğitim Eylemci Projesi

Bu sistem:
- Agent'lar arası gerçek zamanlı bilgi paylaşımı sağlar
- Merkezi blackboard veri yapısı ile koordinasyon yapar
- WebSocket tabanlı gerçek zamanlı senkronizasyon sunar
- Event-driven architecture ile agent koordinasyonu yapar

Devrimsel Özellik: Her agent diğerlerinin keşiflerinden ANINDA haberdar!
"""

import asyncio
import json
import logging
import uuid
import weakref
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Blackboard olay tipleri"""

    DATA_WRITTEN = "data_written"
    DATA_READ = "data_read"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    AGENT_REGISTERED = "agent_registered"
    AGENT_SUBSCRIBED = "agent_subscribed"
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"
    EMERGENCY_ALERT = "emergency_alert"


class Priority(Enum):
    """Olay öncelik seviyeleri"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BlackboardEvent:
    """Blackboard olayı"""

    event_id: str
    event_type: EventType
    key: str
    value: Any
    source_agent: str
    target_agents: list[str] | None = None  # None = broadcast
    priority: Priority = Priority.MEDIUM
    timestamp: datetime = None
    metadata: dict[str, Any] = None
    requires_response: bool = False
    correlation_id: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BlackboardData:
    """Blackboard veri yapısı"""

    key: str
    value: Any
    source_agent: str
    timestamp: datetime
    version: int = 1
    access_count: int = 0
    subscribers: set[str] = None
    ttl: datetime | None = None  # Time to live
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.subscribers is None:
            self.subscribers = set()
        if self.metadata is None:
            self.metadata = {}


class AgentSubscription:
    """Agent abonelik bilgisi"""

    def __init__(
        self,
        agent_name: str,
        event_types: list[EventType],
        key_patterns: list[str] = None,
        callback: Callable | None = None,
        priority_filter: Priority | None = None,
    ):
        self.agent_name = agent_name
        self.event_types = event_types
        self.key_patterns = key_patterns or ["*"]  # * = tüm key'ler
        self.callback = callback
        self.priority_filter = priority_filter
        self.created_at = datetime.now()
        self.notification_count = 0


class MultiAgentBlackboard:
    """
    Devrimsel Multi-Agent Blackboard Sistemi

    Bu sistem agent'lar arası gerçek zamanlı bilgi paylaşımı ve koordinasyon sağlar.
    Her agent diğerlerinin keşiflerinden anında haberdar olur!
    """

    def __init__(self, max_history_size: int = 10000):
        # Merkezi blackboard veri yapısı
        self.blackboard: dict[str, BlackboardData] = {}

        # Agent kayıtları ve abonelikleri
        self.registered_agents: dict[str, Any] = {}  # agent_name -> agent_instance
        self.subscriptions: dict[str, list[AgentSubscription]] = defaultdict(list)

        # Olay geçmişi ve koordinasyon
        self.event_history: list[BlackboardEvent] = []
        self.max_history_size = max_history_size
        self.coordination_requests: dict[str, dict[str, Any]] = {}

        # WebSocket bağlantıları (gerçek zamanlı senkronizasyon için)
        self.websocket_connections: dict[str, Any] = {}

        # Performans metrikleri
        self.metrics = {
            "total_writes": 0,
            "total_reads": 0,
            "total_notifications": 0,
            "active_subscriptions": 0,
            "coordination_requests": 0,
            "average_response_time": 0.0,
        }

        # Test compatibility attributes
        self.subscribers = defaultdict(list)  # For test compatibility

        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """TTL temizleme görevini başlat (lazy initialization)"""
        if self._cleanup_task is None:
            try:
                # Event loop var mı kontrol et
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
            except RuntimeError:
                # Event loop yok, cleanup task'ı daha sonra başlatılacak
                pass

    async def _periodic_cleanup(self):
        """Periyodik temizleme görevi"""
        while True:
            try:
                await asyncio.sleep(60)  # Her dakika temizle
                await self._cleanup_expired_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")

    async def _cleanup_expired_data(self):
        """Süresi dolmuş verileri temizle"""
        now = datetime.now()
        expired_keys = []

        for key, data in self.blackboard.items():
            if data.ttl and now > data.ttl:
                expired_keys.append(key)

        for key in expired_keys:
            await self.delete(key, "system_cleanup")
            logger.info(f"Expired data cleaned up: {key}")

    def register_agent(self, agent_name: str, agent_instance: Any) -> bool:
        """
        Agent'ı blackboard sistemine kaydet

        Args:
            agent_name: Agent adı
            agent_instance: Agent instance'ı

        Returns:
            Kayıt başarılı mı
        """
        try:
            if agent_name in self.registered_agents:
                logger.warning(f"Agent already registered: {agent_name}")
                return False

            # Weak reference kullan (memory leak önlemi)
            self.registered_agents[agent_name] = weakref.ref(agent_instance)

            # Test compatibility: agent'ı attribute olarak da ekle
            setattr(self, f"{agent_name}_agent", agent_instance)

            # Kayıt olayını yayınla
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.AGENT_REGISTERED,
                key=f"agent_registered_{agent_name}",
                value={"agent_name": agent_name, "timestamp": datetime.now()},
                source_agent="blackboard_system",
            )

            asyncio.create_task(self._broadcast_event(event))

            logger.info(f"Agent registered: {agent_name}")
            return True

        except Exception as e:
            logger.error(f"Agent registration failed: {agent_name}, error: {e}")
            return False

    def subscribe_simple(self, agent_name: str, event_type: str) -> bool:
        """Simple subscribe method for test compatibility"""
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []

        if event_type not in self.subscribers[agent_name]:
            self.subscribers[agent_name].append(event_type)

        return True

    def subscribe(
        self,
        agent_name: str,
        event_types: list[EventType],
        key_patterns: list[str] = None,
        callback: Callable | None = None,
        priority_filter: Priority | None = None,
    ) -> bool:
        """
        Agent'ı belirli olaylara abone et

        Args:
            agent_name: Agent adı
            event_types: Abone olunacak olay tipleri
            key_patterns: Key pattern'leri (regex destekli)
            callback: Bildirim callback fonksiyonu
            priority_filter: Minimum öncelik seviyesi

        Returns:
            Abonelik başarılı mı
        """
        try:
            if agent_name not in self.registered_agents:
                logger.error(f"Agent not registered: {agent_name}")
                return False

            subscription = AgentSubscription(
                agent_name=agent_name,
                event_types=event_types,
                key_patterns=key_patterns,
                callback=callback,
                priority_filter=priority_filter,
            )

            self.subscriptions[agent_name].append(subscription)
            self.metrics["active_subscriptions"] += 1

            # Abonelik olayını yayınla
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.AGENT_SUBSCRIBED,
                key=f"agent_subscribed_{agent_name}",
                value={
                    "agent_name": agent_name,
                    "event_types": [et.value for et in event_types],
                    "key_patterns": key_patterns,
                },
                source_agent="blackboard_system",
            )

            asyncio.create_task(self._broadcast_event(event))

            logger.info(f"Agent subscribed: {agent_name} to {event_types}")
            return True

        except Exception as e:
            logger.error(f"Subscription failed: {agent_name}, error: {e}")
            return False

    async def write(
        self,
        key: str,
        value: Any,
        source_agent: str,
        ttl_seconds: int | None = None,
        metadata: dict[str, Any] = None,
        priority: Priority = Priority.MEDIUM,
    ) -> bool:
        """
        Blackboard'a veri yaz ve abone agent'ları bilgilendir

        Args:
            key: Veri anahtarı
            value: Veri değeri
            source_agent: Kaynak agent
            ttl_seconds: Yaşam süresi (saniye)
            metadata: Ek metadata
            priority: Olay önceliği

        Returns:
            Yazma işlemi başarılı mı
        """
        try:
            # Lazy cleanup task initialization
            if self._cleanup_task is None:
                self._start_cleanup_task()

            start_time = datetime.now()

            # TTL hesapla
            ttl = None
            if ttl_seconds:
                ttl = datetime.now() + timedelta(seconds=ttl_seconds)

            # Mevcut veri var mı kontrol et
            is_update = key in self.blackboard
            old_version = self.blackboard[key].version if is_update else 0

            # Veriyi yaz
            self.blackboard[key] = BlackboardData(
                key=key,
                value=value,
                source_agent=source_agent,
                timestamp=datetime.now(),
                version=old_version + 1,
                ttl=ttl,
                metadata=metadata or {},
            )

            # Metrikleri güncelle
            self.metrics["total_writes"] += 1

            # Olay oluştur
            event_type = EventType.DATA_UPDATED if is_update else EventType.DATA_WRITTEN
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                key=key,
                value=value,
                source_agent=source_agent,
                priority=priority,
                metadata=metadata,
            )

            # Olayı kaydet
            self._add_to_history(event)

            # Abone agent'ları bilgilendir
            await self._notify_subscribers(event)

            # WebSocket ile gerçek zamanlı bildirim
            await self._broadcast_websocket(event)

            # Performans metriği güncelle
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_response_time(response_time)

            logger.info(f"Data written to blackboard: {key} by {source_agent}")
            return True

        except Exception as e:
            logger.error(f"Write operation failed: {key}, error: {e}")
            return False

    def read(self, key: str, reader_agent: str = "unknown") -> Any | None:
        """
        Blackboard'dan veri oku

        Args:
            key: Veri anahtarı
            reader_agent: Okuyan agent

        Returns:
            Veri değeri veya None
        """
        try:
            if key not in self.blackboard:
                return None

            data = self.blackboard[key]

            # TTL kontrolü
            if data.ttl and datetime.now() > data.ttl:
                asyncio.create_task(self.delete(key, "ttl_expired"))
                return None

            # Access count güncelle
            data.access_count += 1
            self.metrics["total_reads"] += 1

            # Read olayı oluştur
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.DATA_READ,
                key=key,
                value=data.value,
                source_agent=reader_agent,
                priority=Priority.LOW,
            )

            self._add_to_history(event)

            logger.debug(f"Data read from blackboard: {key} by {reader_agent}")
            return data.value

        except Exception as e:
            logger.error(f"Read operation failed: {key}, error: {e}")
            return None

    async def delete(self, key: str, source_agent: str) -> bool:
        """
        Blackboard'dan veri sil

        Args:
            key: Veri anahtarı
            source_agent: Silen agent

        Returns:
            Silme işlemi başarılı mı
        """
        try:
            if key not in self.blackboard:
                return False

            deleted_data = self.blackboard.pop(key)

            # Delete olayı oluştur
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.DATA_DELETED,
                key=key,
                value=deleted_data.value,
                source_agent=source_agent,
                priority=Priority.MEDIUM,
            )

            self._add_to_history(event)
            await self._notify_subscribers(event)
            await self._broadcast_websocket(event)

            logger.info(f"Data deleted from blackboard: {key} by {source_agent}")
            return True

        except Exception as e:
            logger.error(f"Delete operation failed: {key}, error: {e}")
            return False

    def _add_to_history(self, event: BlackboardEvent):
        """Olayı geçmişe ekle"""
        self.event_history.append(event)

        # Geçmiş boyutu kontrolü
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size :]

    async def _notify_subscribers(self, event: BlackboardEvent):
        """Abone agent'ları bilgilendir"""
        try:
            notification_tasks = []

            for agent_name, subscriptions in self.subscriptions.items():
                for subscription in subscriptions:
                    if self._should_notify(subscription, event):
                        task = self._send_notification(subscription, event)
                        notification_tasks.append(task)

            if notification_tasks:
                await asyncio.gather(*notification_tasks, return_exceptions=True)
                self.metrics["total_notifications"] += len(notification_tasks)

        except Exception as e:
            logger.error(f"Notification failed: {e}")

    def _should_notify(
        self, subscription: AgentSubscription, event: BlackboardEvent
    ) -> bool:
        """Bildirim gönderilmeli mi kontrol et"""
        # Event type kontrolü
        if event.event_type not in subscription.event_types:
            return False

        # Priority kontrolü
        if (
            subscription.priority_filter
            and event.priority.value < subscription.priority_filter.value
        ):
            return False

        # Key pattern kontrolü
        if subscription.key_patterns and "*" not in subscription.key_patterns:
            import re

            key_match = False
            for pattern in subscription.key_patterns:
                if re.match(pattern.replace("*", ".*"), event.key):
                    key_match = True
                    break
            if not key_match:
                return False

        # Kendi olaylarını filtrele (opsiyonel)
        if event.source_agent == subscription.agent_name:
            return False

        return True

    async def _send_notification(
        self, subscription: AgentSubscription, event: BlackboardEvent
    ):
        """Belirli agent'a bildirim gönder"""
        try:
            agent_ref = self.registered_agents.get(subscription.agent_name)
            if not agent_ref:
                return

            agent = agent_ref()  # Weak reference'dan agent'ı al
            if not agent:
                # Agent garbage collect edilmiş
                del self.registered_agents[subscription.agent_name]
                return

            # Callback varsa kullan
            if subscription.callback:
                await subscription.callback(event)

            # Agent'ın on_blackboard_update metodunu çağır
            elif hasattr(agent, "on_blackboard_update"):
                await agent.on_blackboard_update(
                    event.key, event.value, event.source_agent, event.event_type
                )

            subscription.notification_count += 1

        except Exception as e:
            logger.error(
                f"Notification send failed: {subscription.agent_name}, error: {e}"
            )

    async def _broadcast_event(self, event: BlackboardEvent):
        """Olayı tüm abone agent'lara yayınla"""
        await self._notify_subscribers(event)
        await self._broadcast_websocket(event)

    async def _broadcast_websocket(self, event: BlackboardEvent):
        """WebSocket ile gerçek zamanlı yayın"""
        if not self.websocket_connections:
            return

        try:
            message = {
                "type": "blackboard_event",
                "event": asdict(event),
                "timestamp": event.timestamp.isoformat(),
            }

            # JSON serialization için datetime'ları string'e çevir
            message["event"]["timestamp"] = event.timestamp.isoformat()

            message_json = json.dumps(message, default=str)

            # Tüm WebSocket bağlantılarına gönder
            for connection_id, websocket in list(self.websocket_connections.items()):
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.warning(
                        f"WebSocket send failed: {connection_id}, error: {e}"
                    )
                    # Bozuk bağlantıyı kaldır
                    self.websocket_connections.pop(connection_id, None)

        except Exception as e:
            logger.error(f"WebSocket broadcast failed: {e}")

    def _update_response_time(self, response_time_ms: float):
        """Ortalama yanıt süresini güncelle"""
        current_avg = self.metrics["average_response_time"]
        total_operations = self.metrics["total_writes"] + self.metrics["total_reads"]

        if total_operations > 1:
            self.metrics["average_response_time"] = (
                current_avg * (total_operations - 1) + response_time_ms
            ) / total_operations
        else:
            self.metrics["average_response_time"] = response_time_ms

    def add_websocket_connection(self, connection_id: str, websocket):
        """WebSocket bağlantısı ekle"""
        self.websocket_connections[connection_id] = websocket
        logger.info(f"WebSocket connection added: {connection_id}")

    def remove_websocket_connection(self, connection_id: str):
        """WebSocket bağlantısını kaldır"""
        self.websocket_connections.pop(connection_id, None)
        logger.info(f"WebSocket connection removed: {connection_id}")

    def get_metrics(self) -> dict[str, Any]:
        """Performans metriklerini al"""
        return {
            **self.metrics,
            "registered_agents": len(self.registered_agents),
            "active_data_entries": len(self.blackboard),
            "event_history_size": len(self.event_history),
            "websocket_connections": len(self.websocket_connections),
        }

    def get_agent_status(self) -> dict[str, Any]:
        """Agent durumlarını al"""
        status = {}
        for agent_name, agent_ref in self.registered_agents.items():
            agent = agent_ref()
            if agent:
                status[agent_name] = {
                    "status": getattr(agent, "status", "unknown"),
                    "subscriptions": len(self.subscriptions.get(agent_name, [])),
                    "last_activity": getattr(agent, "last_activity", None),
                }
            else:
                status[agent_name] = {"status": "garbage_collected"}

        return status

    async def request_coordination(
        self,
        requester_agent: str,
        target_agents: list[str],
        coordination_type: str,
        parameters: dict[str, Any],
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """
        Agent koordinasyonu talep et

        Args:
            requester_agent: Talep eden agent
            target_agents: Hedef agent'lar
            coordination_type: Koordinasyon tipi
            parameters: Koordinasyon parametreleri
            timeout_seconds: Timeout süresi

        Returns:
            Koordinasyon sonucu
        """
        try:
            coordination_id = str(uuid.uuid4())

            # Koordinasyon talebini kaydet
            self.coordination_requests[coordination_id] = {
                "requester": requester_agent,
                "targets": target_agents,
                "type": coordination_type,
                "parameters": parameters,
                "responses": {},
                "created_at": datetime.now(),
                "timeout": datetime.now() + timedelta(seconds=timeout_seconds),
                "status": "pending",
            }

            # Koordinasyon olayı oluştur
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.COORDINATION_REQUEST,
                key=f"coordination_{coordination_id}",
                value={
                    "coordination_id": coordination_id,
                    "type": coordination_type,
                    "parameters": parameters,
                    "requester": requester_agent,
                },
                source_agent=requester_agent,
                target_agents=target_agents,
                priority=Priority.HIGH,
                requires_response=True,
                correlation_id=coordination_id,
            )

            await self._broadcast_event(event)
            self.metrics["coordination_requests"] += 1

            # Yanıtları bekle
            return await self._wait_for_coordination_responses(
                coordination_id, timeout_seconds
            )

        except Exception as e:
            logger.error(f"Coordination request failed: {e}")
            return {"success": False, "error": str(e)}

    async def _wait_for_coordination_responses(
        self, coordination_id: str, timeout_seconds: int
    ) -> dict[str, Any]:
        """Koordinasyon yanıtlarını bekle"""
        try:
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < timeout_seconds:
                request = self.coordination_requests.get(coordination_id)
                if not request:
                    break

                # Tüm yanıtlar geldi mi?
                if len(request["responses"]) >= len(request["targets"]):
                    request["status"] = "completed"
                    return {
                        "success": True,
                        "coordination_id": coordination_id,
                        "responses": request["responses"],
                        "completion_time": (
                            datetime.now() - request["created_at"]
                        ).total_seconds(),
                    }

                await asyncio.sleep(0.1)  # 100ms bekle

            # Timeout
            if coordination_id in self.coordination_requests:
                self.coordination_requests[coordination_id]["status"] = "timeout"

            return {
                "success": False,
                "error": "coordination_timeout",
                "partial_responses": self.coordination_requests.get(
                    coordination_id, {}
                ).get("responses", {}),
            }

        except Exception as e:
            logger.error(f"Coordination wait failed: {e}")
            return {"success": False, "error": str(e)}

    async def respond_to_coordination(
        self, coordination_id: str, responding_agent: str, response_data: dict[str, Any]
    ) -> bool:
        """
        Koordinasyon talebine yanıt ver

        Args:
            coordination_id: Koordinasyon ID'si
            responding_agent: Yanıt veren agent
            response_data: Yanıt verisi

        Returns:
            Yanıt başarılı mı
        """
        try:
            if coordination_id not in self.coordination_requests:
                logger.warning(f"Unknown coordination request: {coordination_id}")
                return False

            request = self.coordination_requests[coordination_id]

            # Yanıtı kaydet
            request["responses"][responding_agent] = {
                "data": response_data,
                "timestamp": datetime.now(),
            }

            # Yanıt olayı oluştur
            event = BlackboardEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.COORDINATION_RESPONSE,
                key=f"coordination_response_{coordination_id}",
                value={
                    "coordination_id": coordination_id,
                    "responding_agent": responding_agent,
                    "response": response_data,
                },
                source_agent=responding_agent,
                target_agents=[request["requester"]],
                priority=Priority.HIGH,
                correlation_id=coordination_id,
            )

            await self._broadcast_event(event)

            logger.info(
                f"Coordination response received: {coordination_id} from {responding_agent}"
            )
            return True

        except Exception as e:
            logger.error(f"Coordination response failed: {e}")
            return False

    def save_checkpoint(self, filepath: str) -> bool:
        """Blackboard durumunu dosyaya kaydet (Checkpoint)"""
        try:
            import os
            from dataclasses import asdict
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data_to_save = {}
            for k, v in self.blackboard.items():
                data_dict = asdict(v)
                if isinstance(data_dict.get('subscribers'), set):
                    data_dict['subscribers'] = list(data_dict['subscribers'])
                data_to_save[k] = data_dict
                
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, default=str)
                
            logger.info(f"Blackboard checkpoint saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save blackboard checkpoint: {e}")
            return False

    def load_checkpoint(self, filepath: str) -> bool:
        """Blackboard durumunu dosyadan yükle (Resume)"""
        try:
            import os
            from datetime import datetime
            
            if not os.path.exists(filepath):
                return False
                
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for k, v_dict in data.items():
                if v_dict.get('timestamp') and isinstance(v_dict['timestamp'], str):
                    v_dict['timestamp'] = datetime.fromisoformat(v_dict['timestamp'])
                if v_dict.get('ttl') and isinstance(v_dict['ttl'], str):
                    v_dict['ttl'] = datetime.fromisoformat(v_dict['ttl'])
                if v_dict.get('subscribers'):
                    v_dict['subscribers'] = set(v_dict['subscribers'])
                    
                self.blackboard[k] = BlackboardData(**v_dict)
                
            logger.info(f"Blackboard checkpoint loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load blackboard checkpoint: {e}")
            return False

    def cleanup(self):
        """Blackboard temizleme"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()

            self.blackboard.clear()
            self.registered_agents.clear()
            self.subscriptions.clear()
            self.event_history.clear()
            self.coordination_requests.clear()
            self.websocket_connections.clear()

            logger.info("Blackboard cleaned up")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Global blackboard instance
_global_blackboard: MultiAgentBlackboard | None = None


def get_blackboard() -> MultiAgentBlackboard:
    """Global blackboard instance'ını al"""
    global _global_blackboard
    if _global_blackboard is None:
        _global_blackboard = MultiAgentBlackboard()
    return _global_blackboard


def reset_blackboard():
    """Global blackboard'ı sıfırla (test amaçlı)"""
    global _global_blackboard
    if _global_blackboard:
        _global_blackboard.cleanup()
    _global_blackboard = None
