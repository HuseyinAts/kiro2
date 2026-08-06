"""
Domain Blackboard - Redis-based Inter-Agent Communication
REQ-7.3, REQ-7.5
Teknofest 2025 - KIRO2 YKS Platformu

Blackboard pattern ile agent'lar arasi koordinasyon:
- Message TTL: 1 saat (3600 saniye)
- Shared Context TTL: 10 dakika (600 saniye)
- Redis-based message queue
- Fallback: In-memory queue
"""

import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# TTL Constants (seconds)
MESSAGE_TTL = 3600  # 1 hour
SHARED_CONTEXT_TTL = 600  # 10 minutes


@dataclass
class BlackboardMessage:
    """Blackboard mesaj yapisi (REQ-8.5: correlation_id for distributed tracing)"""

    message_id: str
    source_agent: str  # Agent domain or ID
    target_agent: str | None  # None = broadcast
    message_type: str  # "question", "response", "context_share", etc.
    content: dict[str, Any]
    priority: int = 0  # 0=normal, 1=high, 2=critical
    ttl_seconds: int = MESSAGE_TTL
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None  # REQ-8.5: Distributed tracing

    def __post_init__(self):
        """correlation_id yoksa otomatik olustur"""
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())

    def to_json(self) -> str:
        """JSON string'e donustur"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "BlackboardMessage":
        """JSON string'den olustur"""
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def create(
        cls,
        source_agent: str,
        message_type: str,
        content: dict[str, Any],
        target_agent: str | None = None,
        correlation_id: str | None = None,
        priority: int = 0,
    ) -> "BlackboardMessage":
        """
        Factory method with auto-generated IDs (REQ-8.5).

        Args:
            source_agent: Kaynak agent
            message_type: Mesaj tipi
            content: Mesaj icerigi
            target_agent: Hedef agent (None = broadcast)
            correlation_id: Distributed tracing ID (otomatik uretilir)
            priority: Oncelik (0=normal, 1=high, 2=critical)

        Returns:
            BlackboardMessage instance
        """
        return cls(
            message_id=str(uuid.uuid4()),
            source_agent=source_agent,
            target_agent=target_agent,
            message_type=message_type,
            content=content,
            priority=priority,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

    def is_expired(self) -> bool:
        """Mesaj suresi dolmus mu?"""
        return (time.time() - self.timestamp) > self.ttl_seconds


@dataclass
class SharedContext:
    """Agent'lar arasi paylasilan context"""

    context_id: str
    source_agent: str
    target_agent: str | None  # None = all agents
    data: dict[str, Any]
    ttl_seconds: int = SHARED_CONTEXT_TTL
    created_at: float = field(default_factory=time.time)

    def to_json(self) -> str:
        """JSON string'e donustur"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "SharedContext":
        """JSON string'den olustur"""
        data = json.loads(json_str)
        return cls(**data)

    def is_expired(self) -> bool:
        """Context suresi dolmus mu?"""
        return (time.time() - self.created_at) > self.ttl_seconds


class DomainBlackboard:
    """
    Domain Expert Agent'lar icin Blackboard (REQ-7.3, REQ-7.5)

    Redis-based message queue ve context sharing.
    Redis yoksa in-memory fallback kullanir.

    Attributes:
        redis_url: Redis baglanti URL'i
        message_ttl: Mesaj suresi (default 1 saat)
        context_ttl: Paylasilan context suresi (default 10 dakika)
    """

    def __init__(
        self,
        redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/2"),
        message_ttl: int = MESSAGE_TTL,
        context_ttl: int = SHARED_CONTEXT_TTL,
    ):
        """
        DomainBlackboard olustur

        Args:
            redis_url: Redis baglanti URL'i
            message_ttl: Mesaj suresi (saniye)
            context_ttl: Paylasilan context suresi (saniye)
        """
        self.redis_url = redis_url
        self.message_ttl = message_ttl
        self.context_ttl = context_ttl

        # Redis connection
        self._redis = None
        self._use_fallback = False

        # In-memory fallback
        self._message_queue: dict[str, list[BlackboardMessage]] = {}
        self._shared_contexts: dict[str, SharedContext] = {}

        # Subscribers
        self._subscribers: dict[str, list[Callable]] = {}

        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.contexts_shared = 0

        logger.info(
            f"DomainBlackboard initialized (message_ttl={message_ttl}s, "
            f"context_ttl={context_ttl}s)"
        )

    async def connect(self) -> bool:
        """
        Redis'e baglan

        Returns:
            True basarili, False fallback kullaniliyor
        """
        try:
            import redis.asyncio as aioredis

            self._redis = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info(f"Connected to Redis: {self.redis_url}")
            return True

        except ImportError:
            logger.warning("redis.asyncio not available, using in-memory fallback")
            self._use_fallback = True
            return False

        except Exception as e:
            logger.warning(f"Redis connection failed, using fallback: {e}")
            self._use_fallback = True
            return False

    async def disconnect(self):
        """Redis baglantisini kapat"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    async def post_message(
        self,
        source_agent: str,
        message_type: str,
        content: dict[str, Any],
        target_agent: str | None = None,
        priority: int = 0,
    ) -> str:
        """
        Blackboard'a mesaj gonder (REQ-7.3)

        Args:
            source_agent: Gonderen agent (domain veya ID)
            message_type: Mesaj tipi
            content: Mesaj icerigi
            target_agent: Hedef agent (None = broadcast)
            priority: Oncelik (0=normal, 1=high, 2=critical)

        Returns:
            Mesaj ID
        """
        message_id = str(uuid.uuid4())
        message = BlackboardMessage(
            message_id=message_id,
            source_agent=source_agent,
            target_agent=target_agent,
            message_type=message_type,
            content=content,
            priority=priority,
            ttl_seconds=self.message_ttl,
        )

        if self._use_fallback or self._redis is None:
            await self._post_message_fallback(message)
        else:
            await self._post_message_redis(message)

        self.messages_sent += 1
        logger.debug(
            f"Posted message {message_id}: {message_type} "
            f"from {source_agent} to {target_agent or 'all'}"
        )

        return message_id

    async def _post_message_redis(self, message: BlackboardMessage):
        """Redis'e mesaj gonder"""
        channel = f"blackboard:domain:{message.target_agent or 'broadcast'}"
        await self._redis.lpush(channel, message.to_json())
        await self._redis.ltrim(channel, 0, self.max_messages - 1)
        await self._redis.expire(channel, self.message_ttl)

    async def _post_message_fallback(self, message: BlackboardMessage):
        """In-memory queue'ya mesaj ekle"""
        target = message.target_agent or "broadcast"
        if target not in self._message_queue:
            self._message_queue[target] = []
        self._message_queue[target].append(message)

        # Cleanup expired messages and enforce size limit
        self._message_queue[target] = [
            m for m in self._message_queue[target] if not m.is_expired()
        ][:self.max_messages]

    async def get_messages(
        self,
        agent_id: str,
        include_broadcast: bool = True,
        limit: int = 100,
    ) -> list[BlackboardMessage]:
        """
        Agent icin mesajlari al

        Args:
            agent_id: Agent ID veya domain
            include_broadcast: Broadcast mesajlari dahil et
            limit: Maximum mesaj sayisi

        Returns:
            Mesaj listesi
        """
        messages = []

        if self._use_fallback or self._redis is None:
            messages = await self._get_messages_fallback(agent_id, include_broadcast)
        else:
            messages = await self._get_messages_redis(
                agent_id, include_broadcast, limit
            )

        self.messages_received += len(messages)
        return messages

    async def _get_messages_redis(
        self, agent_id: str, include_broadcast: bool, limit: int
    ) -> list[BlackboardMessage]:
        """Redis'ten mesajlari al"""
        messages = []

        # Agent-specific messages
        channel = f"blackboard:domain:{agent_id}"
        raw_messages = await self._redis.lrange(channel, 0, limit - 1)
        for raw in raw_messages:
            try:
                msg = BlackboardMessage.from_json(raw)
                if not msg.is_expired():
                    messages.append(msg)
            except Exception as e:
                logger.warning(f"Failed to parse message: {e}")

        # Broadcast messages
        if include_broadcast:
            channel = "blackboard:domain:broadcast"
            raw_broadcasts = await self._redis.lrange(channel, 0, limit - 1)
            for raw in raw_broadcasts:
                try:
                    msg = BlackboardMessage.from_json(raw)
                    if not msg.is_expired():
                        messages.append(msg)
                except Exception as e:
                    logger.warning(f"Failed to parse broadcast: {e}")

        return messages

    async def _get_messages_fallback(
        self, agent_id: str, include_broadcast: bool
    ) -> list[BlackboardMessage]:
        """In-memory queue'dan mesajlari al"""
        messages = []

        # Agent-specific
        if agent_id in self._message_queue:
            messages.extend(
                m for m in self._message_queue[agent_id] if not m.is_expired()
            )

        # Broadcast
        if include_broadcast and "broadcast" in self._message_queue:
            messages.extend(
                m for m in self._message_queue["broadcast"] if not m.is_expired()
            )

        return messages

    async def share_context(
        self,
        source_agent: str,
        data: dict[str, Any],
        target_agent: str | None = None,
    ) -> str:
        """
        Context payllas (REQ-7.5)

        Args:
            source_agent: Paylasan agent
            data: Paylasilacak context verisi
            target_agent: Hedef agent (None = tum agent'lar)

        Returns:
            Context ID
        """
        context_id = str(uuid.uuid4())
        context = SharedContext(
            context_id=context_id,
            source_agent=source_agent,
            target_agent=target_agent,
            data=data,
            ttl_seconds=self.context_ttl,
        )

        if self._use_fallback or self._redis is None:
            await self._share_context_fallback(context)
        else:
            await self._share_context_redis(context)

        self.contexts_shared += 1
        logger.debug(
            f"Shared context {context_id} from {source_agent} "
            f"to {target_agent or 'all'} (TTL: {self.context_ttl}s)"
        )

        return context_id

    async def _share_context_redis(self, context: SharedContext):
        """Redis'e context kaydet"""
        key = f"blackboard:context:{context.context_id}"
        await self._redis.set(key, context.to_json(), ex=self.context_ttl)

        # Also add to agent-specific context list
        target = context.target_agent or "all"
        list_key = f"blackboard:contexts:{target}"
        await self._redis.lpush(list_key, context.context_id)
        await self._redis.ltrim(list_key, 0, self.max_messages - 1)
        await self._redis.expire(list_key, self.context_ttl)

    async def _share_context_fallback(self, context: SharedContext):
        """In-memory'ye context kaydet"""
        self._shared_contexts[context.context_id] = context

        # Cleanup expired contexts
        self._shared_contexts = {
            k: v for k, v in self._shared_contexts.items() if not v.is_expired()
        }

    async def get_shared_context(self, agent_id: str) -> dict[str, Any]:
        """
        Agent icin paylasilan context'i al

        Args:
            agent_id: Agent ID veya domain

        Returns:
            Birlestirilmis context verisi
        """
        if self._use_fallback or self._redis is None:
            return await self._get_context_fallback(agent_id)
        return await self._get_context_redis(agent_id)

    async def _get_context_redis(self, agent_id: str) -> dict[str, Any]:
        """Redis'ten context al"""
        combined_data = {}

        # Agent-specific contexts
        for target in [agent_id, "all"]:
            list_key = f"blackboard:contexts:{target}"
            context_ids = await self._redis.lrange(list_key, 0, -1)

            for ctx_id in context_ids:
                key = f"blackboard:context:{ctx_id}"
                raw = await self._redis.get(key)
                if raw:
                    try:
                        ctx = SharedContext.from_json(raw)
                        if not ctx.is_expired():
                            combined_data.update(ctx.data)
                    except Exception as e:
                        logger.warning(f"Failed to parse context: {e}")

        return combined_data

    async def _get_context_fallback(self, agent_id: str) -> dict[str, Any]:
        """In-memory'den context al"""
        combined_data = {}

        for ctx in self._shared_contexts.values():
            if ctx.is_expired():
                continue
            if ctx.target_agent is None or ctx.target_agent == agent_id:
                combined_data.update(ctx.data)

        return combined_data

    async def clear_agent_context(self, agent_id: str):
        """Agent'in context'ini temizle"""
        if self._use_fallback or self._redis is None:
            self._shared_contexts = {
                k: v
                for k, v in self._shared_contexts.items()
                if v.source_agent != agent_id
            }
        else:
            # Redis'te agent context'lerini sil
            pattern = f"blackboard:contexts:{agent_id}"
            await self._redis.delete(pattern)

        logger.info(f"Cleared context for agent: {agent_id}")

    def get_metrics(self) -> dict[str, Any]:
        """Blackboard metriklerini al"""
        return {
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "contexts_shared": self.contexts_shared,
            "using_fallback": self._use_fallback,
            "message_ttl": self.message_ttl,
            "context_ttl": self.context_ttl,
        }


# Global instance
_blackboard_instance: DomainBlackboard | None = None


async def get_domain_blackboard() -> DomainBlackboard:
    """Global DomainBlackboard instance'ini al"""
    global _blackboard_instance
    if _blackboard_instance is None:
        _blackboard_instance = DomainBlackboard()
        await _blackboard_instance.connect()
    return _blackboard_instance
