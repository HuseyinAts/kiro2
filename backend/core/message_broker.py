"""
KIRO2 Message Broker - RabbitMQ Integration
Mikroservisler arası asenkron mesajlaşma altyapısı
"""

import asyncio
import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import aio_pika
from aio_pika import ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractExchange, AbstractQueue

from core.events import MicroserviceEventType, ServiceEvent, ServiceName


class ExchangeName(Enum):
    """RabbitMQ Exchange isimleri"""
    EVENTS = "kiro2.events"
    COMMANDS = "kiro2.commands"
    DEAD_LETTER = "kiro2.dead_letter"


class QueueName(Enum):
    """RabbitMQ Queue isimleri"""
    # Exam Service
    EXAM_EVENTS = "exam.events"
    EXAM_COMMANDS = "exam.commands"

    # Question Service
    QUESTION_EVENTS = "question.events"
    QUESTION_COMMANDS = "question.commands"

    # IRT/CAT Service
    IRT_EVENTS = "irt.events"
    IRT_COMMANDS = "irt.commands"

    # AI Service
    AI_EVENTS = "ai.events"
    AI_COMMANDS = "ai.commands"

    # Learning Path Service
    LEARNING_PATH_EVENTS = "learning_path.events"
    LEARNING_PATH_COMMANDS = "learning_path.commands"

    # Dead Letter Queue
    DEAD_LETTER = "dead_letter.queue"


@dataclass
class BrokerConfig:
    """Message Broker konfigürasyonu"""
    host: str = field(default_factory=lambda: os.getenv("RABBITMQ_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_PORT", "5672")))
    username: str = field(default_factory=lambda: os.getenv("RABBITMQ_USER", "guest"))
    password: str = field(default_factory=lambda: os.getenv("RABBITMQ_PASSWORD", "guest"))
    virtual_host: str = field(default_factory=lambda: os.getenv("RABBITMQ_VHOST", "/"))
    prefetch_count: int = 10
    connection_timeout: float = 30.0
    heartbeat: int = 60

    @property
    def url(self) -> str:
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.virtual_host}"


class MessageBroker:
    """RabbitMQ Message Broker for KIRO2 Microservices"""

    def __init__(self, config: BrokerConfig | None = None, service_name: ServiceName = ServiceName.MONOLITH):
        self.config = config or BrokerConfig()
        self.service_name = service_name
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchanges: dict[ExchangeName, AbstractExchange] = {}
        self.queues: dict[QueueName, AbstractQueue] = {}
        self.handlers: dict[str, list[Callable]] = {}
        self._running = False
        self._consumer_tags: list[str] = []

    async def connect(self) -> None:
        """RabbitMQ bağlantısı kur"""
        try:
            self.connection = await connect_robust(
                self.config.url,
                timeout=self.config.connection_timeout,
                heartbeat=self.config.heartbeat,
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.config.prefetch_count)

            # Exchange'leri oluştur
            await self._setup_exchanges()

            # Queue'ları oluştur
            await self._setup_queues()

            self._running = True
            print(f"[MessageBroker] Connected to RabbitMQ at {self.config.host}:{self.config.port}")

        except Exception as e:
            print(f"[MessageBroker] Connection failed: {e}")
            raise

    async def _setup_exchanges(self) -> None:
        """Exchange'leri oluştur"""
        # Events exchange (topic)
        self.exchanges[ExchangeName.EVENTS] = await self.channel.declare_exchange(
            ExchangeName.EVENTS.value,
            ExchangeType.TOPIC,
            durable=True,
        )

        # Commands exchange (direct)
        self.exchanges[ExchangeName.COMMANDS] = await self.channel.declare_exchange(
            ExchangeName.COMMANDS.value,
            ExchangeType.DIRECT,
            durable=True,
        )

        # Dead letter exchange
        self.exchanges[ExchangeName.DEAD_LETTER] = await self.channel.declare_exchange(
            ExchangeName.DEAD_LETTER.value,
            ExchangeType.FANOUT,
            durable=True,
        )

    async def _setup_queues(self) -> None:
        """Queue'ları oluştur ve binding yap"""
        # Dead letter queue arguments
        dl_args = {
            "x-dead-letter-exchange": ExchangeName.DEAD_LETTER.value,
            "x-message-ttl": 86400000,  # 24 saat
        }

        # Service-specific queues
        service_queue_map = {
            ServiceName.EXAM: [QueueName.EXAM_EVENTS, QueueName.EXAM_COMMANDS],
            ServiceName.QUESTION: [QueueName.QUESTION_EVENTS, QueueName.QUESTION_COMMANDS],
            ServiceName.IRT: [QueueName.IRT_EVENTS, QueueName.IRT_COMMANDS],
            ServiceName.AI: [QueueName.AI_EVENTS, QueueName.AI_COMMANDS],
            ServiceName.LEARNING_PATH: [QueueName.LEARNING_PATH_EVENTS, QueueName.LEARNING_PATH_COMMANDS],
        }

        # Sadece bu servisin queue'larını oluştur
        if self.service_name in service_queue_map:
            for queue_name in service_queue_map[self.service_name]:
                queue = await self.channel.declare_queue(
                    queue_name.value,
                    durable=True,
                    arguments=dl_args,
                )
                self.queues[queue_name] = queue

                # Event queue'ları için topic binding
                if "events" in queue_name.value:
                    service_prefix = queue_name.value.split(".")[0]
                    await queue.bind(
                        self.exchanges[ExchangeName.EVENTS],
                        routing_key=f"{service_prefix}.*",
                    )
                    # Tüm event'leri dinle (wildcard)
                    await queue.bind(
                        self.exchanges[ExchangeName.EVENTS],
                        routing_key="#",
                    )

        # Dead letter queue (her servis için)
        dl_queue = await self.channel.declare_queue(
            QueueName.DEAD_LETTER.value,
            durable=True,
        )
        self.queues[QueueName.DEAD_LETTER] = dl_queue
        await dl_queue.bind(self.exchanges[ExchangeName.DEAD_LETTER])

    async def publish_event(
        self,
        event: ServiceEvent,
        routing_key: str | None = None,
    ) -> bool:
        """Event yayınla"""
        if not self._running:
            print("[MessageBroker] Not connected, cannot publish")
            return False

        try:
            # Routing key belirle
            if not routing_key:
                routing_key = event.event_type.value if event.event_type else "unknown"

            # Message oluştur
            message = Message(
                body=json.dumps(event.to_dict()).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "event_type": event.event_type.value if event.event_type else None,
                    "source_service": event.source_service.value,
                    "correlation_id": event.correlation_id,
                    "timestamp": event.timestamp.isoformat(),
                },
                message_id=event.event_id,
                correlation_id=event.correlation_id,
                timestamp=event.timestamp,
            )

            # Publish
            await self.exchanges[ExchangeName.EVENTS].publish(
                message,
                routing_key=routing_key,
            )

            print(f"[MessageBroker] Published event: {routing_key} ({event.event_id})")
            return True

        except Exception as e:
            print(f"[MessageBroker] Publish failed: {e}")
            return False

    async def publish_command(
        self,
        target_service: ServiceName,
        command: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> bool:
        """Hedef servise komut gönder"""
        if not self._running:
            return False

        try:
            message_data = {
                "command": command,
                "source_service": self.service_name.value,
                "target_service": target_service.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "correlation_id": correlation_id,
                "payload": payload,
            }

            message = Message(
                body=json.dumps(message_data).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                correlation_id=correlation_id,
            )

            routing_key = f"{target_service.value}.commands"
            await self.exchanges[ExchangeName.COMMANDS].publish(
                message,
                routing_key=routing_key,
            )

            print(f"[MessageBroker] Sent command: {command} to {target_service.value}")
            return True

        except Exception as e:
            print(f"[MessageBroker] Command send failed: {e}")
            return False

    def on_event(self, event_type: MicroserviceEventType | str):
        """Event handler decorator"""
        def decorator(func: Callable):
            key = event_type.value if isinstance(event_type, MicroserviceEventType) else event_type
            if key not in self.handlers:
                self.handlers[key] = []
            self.handlers[key].append(func)
            return func
        return decorator

    async def start_consuming(self) -> None:
        """Event'leri dinlemeye başla"""
        if not self._running:
            await self.connect()

        # Her queue için consumer başlat
        for queue_name, queue in self.queues.items():
            if queue_name == QueueName.DEAD_LETTER:
                continue  # Dead letter ayrı işlenir

            consumer_tag = await queue.consume(self._process_message)
            self._consumer_tags.append(consumer_tag)
            print(f"[MessageBroker] Started consuming from: {queue_name.value}")

    async def _process_message(self, message: aio_pika.IncomingMessage) -> None:
        """Gelen mesajı işle"""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                event_type = body.get("event_type") or message.headers.get("event_type")

                # Handler'ları çağır
                handlers = self.handlers.get(event_type, [])
                handlers.extend(self.handlers.get("*", []))  # Wildcard handlers

                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(body)
                        else:
                            handler(body)
                    except Exception as e:
                        print(f"[MessageBroker] Handler error: {e}")

            except Exception as e:
                print(f"[MessageBroker] Message processing error: {e}")
                # Dead letter queue'ya gönder
                await message.reject(requeue=False)

    async def close(self) -> None:
        """Bağlantıyı kapat"""
        self._running = False

        if self.connection:
            await self.connection.close()

        print("[MessageBroker] Connection closed")


# Global broker instance
_broker: MessageBroker | None = None


async def get_message_broker(service_name: ServiceName = ServiceName.MONOLITH) -> MessageBroker:
    """Global message broker instance al"""
    global _broker

    if _broker is None:
        _broker = MessageBroker(service_name=service_name)
        await _broker.connect()

    return _broker


async def publish_microservice_event(
    event_type: MicroserviceEventType,
    payload: dict[str, Any],
    user_id: int | None = None,
    correlation_id: str | None = None,
) -> bool:
    """Kolaylık fonksiyonu: mikroservis event'i yayınla"""
    from core.events import create_event

    broker = await get_message_broker()
    event = create_event(
        event_type=event_type,
        payload=payload,
        user_id=user_id,
        correlation_id=correlation_id,
    )
    return await broker.publish_event(event)


# Sağlık kontrolü için
async def check_broker_health() -> dict[str, Any]:
    """Message broker sağlık kontrolü"""
    try:
        broker = await get_message_broker()
        return {
            "status": "healthy" if broker._running else "unhealthy",
            "service": broker.service_name.value,
            "queues": list(broker.queues.keys()),
            "exchanges": list(broker.exchanges.keys()),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
