"""
Multi-Agent Blackboard Coordinator
REQ-11.1, REQ-11.2, REQ-11.3, REQ-11.6
Teknofest 2025 - Eğitim Eylemci Projesi

Blackboard pattern ile multi-agent koordinasyonu sağlar:
- Discovery Notification (REQ-11.1): Yeni bilgi < 100ms broadcast
- Learning Style Sync (REQ-11.2): Profil tespiti → Tüm agentler adapte
- Performance Data Sync (REQ-11.3): Performans güncellemesi → Koordine yanıt
- Auto-Reconnect (REQ-11.6): Bağlantı kopması → Otomatik yeniden bağlan
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Blackboard mesaj tipleri"""

    DISCOVERY = "discovery"  # Yeni bilgi keşfi
    LEARNING_STYLE = "learning_style"  # Öğrenme stili değişikliği
    PERFORMANCE_UPDATE = "performance_update"  # Performans güncellemesi
    AGENT_REGISTERED = "agent_registered"  # Agent kaydı
    AGENT_UNREGISTERED = "agent_unregistered"  # Agent kaydı silindi
    HEARTBEAT = "heartbeat"  # Agent sağlık kontrolü


@dataclass
class BlackboardMessage:
    """Blackboard mesaj yapısı"""

    message_type: str
    agent_id: str
    timestamp: float
    data: Dict[str, Any]
    priority: int = 0  # 0 = normal, 1 = high, 2 = critical

    def to_json(self) -> str:
        """JSON'a dönüştür"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "BlackboardMessage":
        """JSON'dan oluştur"""
        data = json.loads(json_str)
        return cls(**data)


class BlackboardCoordinator:
    """
    Multi-Agent Blackboard Koordinatörü

    Redis Pub/Sub kullanarak agentler arası real-time iletişim sağlar.
    Her agent blackboard'a abone olur ve mesajları yayınlayabilir.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/1",
        broadcast_timeout_ms: int = 100,
        auto_reconnect: bool = True,
        heartbeat_interval: int = 30,
    ):
        """
        Blackboard Coordinator'ı başlat

        Args:
            redis_url: Redis bağlantı URL'i
            broadcast_timeout_ms: Broadcast gecikmesi limiti (ms)
            auto_reconnect: Otomatik yeniden bağlanma
            heartbeat_interval: Heartbeat aralığı (saniye)
        """
        self.redis_url = redis_url
        self.broadcast_timeout_ms = broadcast_timeout_ms / 1000  # Convert to seconds
        self.auto_reconnect = auto_reconnect
        self.heartbeat_interval = heartbeat_interval

        # Redis bağlantıları
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None

        # Registered agents
        self.registered_agents: Set[str] = set()

        # Subscribers (topic -> [callbacks])
        self.subscribers: Dict[str, List[Callable]] = {}

        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.last_broadcast_time = 0.0

        # State
        self.is_running = False
        self._tasks: List[asyncio.Task] = []

        logger.info("Blackboard Coordinator initialized")

    async def connect(self):
        """Redis'e bağlan"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            self.pubsub = self.redis.pubsub()

            # Subscribe to all blackboard topics
            await self.pubsub.subscribe("blackboard:*")

            logger.info(f"Connected to Redis: {self.redis_url}")
            self.is_running = True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Redis bağlantısını kapat"""
        self.is_running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        if self.pubsub:
            await self.pubsub.unsubscribe("blackboard:*")
            await self.pubsub.close()

        if self.redis:
            await self.redis.close()

        logger.info("Disconnected from Redis")

    async def register_agent(self, agent_id: str):
        """Agent'ı blackboard'a kaydet"""
        if agent_id in self.registered_agents:
            logger.warning(f"Agent {agent_id} already registered")
            return

        self.registered_agents.add(agent_id)

        # Broadcast agent registration
        await self.publish(
            topic="agent_lifecycle",
            message=BlackboardMessage(
                message_type=MessageType.AGENT_REGISTERED.value,
                agent_id=agent_id,
                timestamp=time.time(),
                data={"status": "registered"},
            ),
        )

        logger.info(f"Agent registered: {agent_id}")

    async def unregister_agent(self, agent_id: str):
        """Agent kaydını sil"""
        if agent_id not in self.registered_agents:
            logger.warning(f"Agent {agent_id} not registered")
            return

        self.registered_agents.remove(agent_id)

        # Broadcast agent unregistration
        await self.publish(
            topic="agent_lifecycle",
            message=BlackboardMessage(
                message_type=MessageType.AGENT_UNREGISTERED.value,
                agent_id=agent_id,
                timestamp=time.time(),
                data={"status": "unregistered"},
            ),
        )

        logger.info(f"Agent unregistered: {agent_id}")

    def subscribe(self, topic: str, callback: Callable):
        """
        Bir topic'e abone ol

        Args:
            topic: Topic adı
            callback: Mesaj alındığında çağrılacak fonksiyon
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []

        self.subscribers[topic].append(callback)
        logger.info(f"Subscribed to topic: {topic}")

    async def publish(
        self, topic: str, message: BlackboardMessage, ensure_delivery: bool = True
    ):
        """
        Blackboard'a mesaj yayınla (REQ-11.1: < 100ms)

        Args:
            topic: Topic adı
            message: Yayınlanacak mesaj
            ensure_delivery: Teslimat garantisi
        """
        start_time = time.time()

        try:
            channel = f"blackboard:{topic}"
            message_json = message.to_json()

            # Publish to Redis
            await self.redis.publish(channel, message_json)

            # Update metrics
            self.messages_sent += 1
            elapsed_ms = (time.time() - start_time) * 1000
            self.last_broadcast_time = elapsed_ms

            # Check broadcast timeout (REQ-11.1)
            if elapsed_ms > self.broadcast_timeout_ms * 1000:
                logger.warning(
                    f"Broadcast timeout exceeded: {elapsed_ms:.2f}ms > "
                    f"{self.broadcast_timeout_ms * 1000}ms"
                )

            logger.debug(
                f"Published to {topic}: {message.message_type} "
                f"from {message.agent_id} ({elapsed_ms:.2f}ms)"
            )

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            if ensure_delivery:
                raise

    async def _message_listener(self):
        """Redis Pub/Sub mesajlarını dinle"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    # Parse message
                    channel = message["channel"]
                    topic = channel.replace("blackboard:", "")
                    msg = BlackboardMessage.from_json(message["data"])

                    # Update metrics
                    self.messages_received += 1

                    # Call subscribers
                    if topic in self.subscribers:
                        for callback in self.subscribers[topic]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(msg)
                                else:
                                    callback(msg)
                            except Exception as e:
                                logger.error(f"Subscriber callback error: {e}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info("Message listener cancelled")
        except Exception as e:
            logger.error(f"Message listener error: {e}")
            if self.auto_reconnect:
                await self._reconnect()

    async def _reconnect(self):
        """Otomatik yeniden bağlanma (REQ-11.6)"""
        logger.warning("Attempting to reconnect...")
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                await asyncio.sleep(2**retry_count)  # Exponential backoff
                await self.connect()
                logger.info("Reconnected successfully")
                return
            except Exception as e:
                retry_count += 1
                logger.error(f"Reconnect attempt {retry_count} failed: {e}")

        logger.error("Max reconnection attempts reached")

    async def _heartbeat_sender(self, agent_id: str):
        """Periyodik heartbeat gönder"""
        while self.is_running:
            try:
                await self.publish(
                    topic="heartbeat",
                    message=BlackboardMessage(
                        message_type=MessageType.HEARTBEAT.value,
                        agent_id=agent_id,
                        timestamp=time.time(),
                        data={"status": "alive"},
                    ),
                    ensure_delivery=False,
                )
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def start(self, agent_id: Optional[str] = None):
        """
        Coordinator'ı başlat

        Args:
            agent_id: Bu coordinator'ı çalıştıran agent ID (opsiyonel)
        """
        if not self.is_running:
            await self.connect()

        # Start message listener
        listener_task = asyncio.create_task(self._message_listener())
        self._tasks.append(listener_task)

        # Start heartbeat (if agent_id provided)
        if agent_id:
            heartbeat_task = asyncio.create_task(self._heartbeat_sender(agent_id))
            self._tasks.append(heartbeat_task)

        logger.info("Blackboard Coordinator started")

    async def stop(self):
        """Coordinator'ı durdur"""
        await self.disconnect()
        logger.info("Blackboard Coordinator stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """Koordinatör metriklerini al"""
        return {
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "last_broadcast_time_ms": self.last_broadcast_time,
            "registered_agents": len(self.registered_agents),
            "active_subscriptions": sum(
                len(subs) for subs in self.subscribers.values()
            ),
            "is_running": self.is_running,
        }


# Example usage and helper functions


async def broadcast_learning_style_detected(
    coordinator: BlackboardCoordinator,
    agent_id: str,
    student_id: str,
    profile: str,
    confidence: float,
):
    """
    Öğrenme stili tespiti broadcast et (REQ-11.2)

    Örnek kullanım:
        await broadcast_learning_style_detected(
            coordinator=blackboard,
            agent_id="learning_style_detector_1",
            student_id="student_123",
            profile="Visual-Active-Sensing-Sequential",
            confidence=0.85
        )
    """
    await coordinator.publish(
        topic="learning_style_detected",
        message=BlackboardMessage(
            message_type=MessageType.LEARNING_STYLE.value,
            agent_id=agent_id,
            timestamp=time.time(),
            data={
                "student_id": student_id,
                "profile": profile,
                "confidence": confidence,
            },
            priority=1,  # High priority
        ),
    )


async def broadcast_discovery(
    coordinator: BlackboardCoordinator,
    agent_id: str,
    discovery_type: str,
    discovery_data: Dict[str, Any],
):
    """
    Yeni bilgi keşfini broadcast et (REQ-11.1)

    Örnek kullanım:
        await broadcast_discovery(
            coordinator=blackboard,
            agent_id="resource_agent_1",
            discovery_type="new_video_resource",
            discovery_data={
                "video_id": "abc123",
                "subject": "matematik",
                "relevance_score": 0.92
            }
        )
    """
    await coordinator.publish(
        topic="discovery",
        message=BlackboardMessage(
            message_type=MessageType.DISCOVERY.value,
            agent_id=agent_id,
            timestamp=time.time(),
            data={"discovery_type": discovery_type, **discovery_data},
            priority=1,  # High priority
        ),
    )


if __name__ == "__main__":
    import signal
    import sys

    async def main_service():
        """Run coordinator as a long-running service"""
        redis_url = os.getenv("REDIS_PUBSUB_URL", "redis://localhost:6379/1")
        coordinator = BlackboardCoordinator(
            redis_url=redis_url, broadcast_timeout_ms=100, auto_reconnect=True
        )
        await coordinator.connect()
        await coordinator.start(agent_id="blackboard_coordinator_main")

        print(f"[Blackboard Coordinator] Started on {redis_url}")
        print("[Blackboard Coordinator] Press Ctrl+C to stop")

        # Keep running
        try:
            while True:
                await asyncio.sleep(10)
                metrics = coordinator.get_metrics()
                print(f"[Blackboard Coordinator] Metrics: {metrics}")
        except KeyboardInterrupt:
            print("\n[Blackboard Coordinator] Shutting down...")
            await coordinator.stop()

    async def main_test():
        """Run coordinator in test mode"""
        coordinator = BlackboardCoordinator(
            redis_url="redis://localhost:6379/1",
            broadcast_timeout_ms=100,
            auto_reconnect=True,
        )

        # Subscribe to learning style changes
        def on_learning_style_change(message: BlackboardMessage):
            print(f"Learning style detected: {message.data}")

        coordinator.subscribe("learning_style_detected", on_learning_style_change)

        # Start coordinator
        await coordinator.start(agent_id="test_coordinator")

        # Wait a bit
        await asyncio.sleep(2)

        # Test broadcast
        await broadcast_learning_style_detected(
            coordinator=coordinator,
            agent_id="test_agent",
            student_id="student_123",
            profile="Visual-Active",
            confidence=0.85,
        )

        # Print metrics
        print(f"Metrics: {coordinator.get_metrics()}")

        # Cleanup
        await coordinator.stop()

    # Run in service mode by default, test mode with --test flag
    if "--test" in sys.argv:
        asyncio.run(main_test())
    else:
        asyncio.run(main_service())
