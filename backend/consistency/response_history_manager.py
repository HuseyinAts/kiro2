"""
Response History Manager

Bu modül, AI yanıt geçmişini Redis'te yönetir.

Features:
- Redis list storage
- Son 50 yanıt saklama
- TTL: 30 gün
- User/agent bazlı key structure

Requirements: REQ-5.1
"""

import logging
from typing import List, Optional

from backend.validators.base_response_validator import AgentResponse

logger = logging.getLogger(__name__)


class ResponseHistoryManager:
    """
    AI yanıt geçmişi yöneticisi.

    Redis kullanarak kullanıcı ve agent bazlı yanıt geçmişini saklar.
    """

    # Varsayılan limitler
    MAX_HISTORY_SIZE = 50  # Kullanıcı başına maksimum yanıt
    DEFAULT_TTL = 30 * 24 * 60 * 60  # 30 gün (saniye)

    def __init__(
        self,
        redis_client=None,
        redis_url: Optional[str] = None,
        key_prefix: str = "response_history",
        max_history_size: int = 50,
        ttl_seconds: int = 30 * 24 * 60 * 60,
    ):
        """
        Args:
            redis_client: Redis client instance
            redis_url: Redis URL (client yoksa)
            key_prefix: Redis key prefix
            max_history_size: Maksimum geçmiş boyutu
            ttl_seconds: TTL (saniye)
        """
        self.redis_client = redis_client
        self.redis_url = redis_url or "redis://localhost:6379"
        self.key_prefix = key_prefix
        self.max_history_size = max_history_size
        self.ttl_seconds = ttl_seconds

        # Fallback: In-memory storage (Redis yoksa)
        self._memory_store: dict = {}

    async def initialize(self) -> bool:
        """
        Redis bağlantısını başlat.

        Returns:
            bool: Başarılı mı
        """
        if self.redis_client:
            return True

        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
            return True
        except ImportError:
            logger.warning("redis package not installed, using memory storage")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using memory storage")
            return False

    def _get_key(self, user_id: str, agent_type: str) -> str:
        """
        Redis key oluştur.

        Args:
            user_id: Kullanıcı ID
            agent_type: Agent tipi

        Returns:
            str: Redis key
        """
        return f"{self.key_prefix}:{user_id}:{agent_type}"

    async def save_response(self, response: AgentResponse) -> bool:
        """
        Yanıtı geçmişe kaydet.

        Args:
            response: Kaydedilecek yanıt

        Returns:
            bool: Başarılı mı
        """
        key = self._get_key(response.user_id, response.agent_type)

        # JSON serialize
        response_json = response.model_dump_json()

        if self.redis_client:
            try:
                # Liste başına ekle
                await self.redis_client.lpush(key, response_json)

                # Listeyi sınırla
                await self.redis_client.ltrim(key, 0, self.max_history_size - 1)

                # TTL ayarla
                await self.redis_client.expire(key, self.ttl_seconds)

                logger.debug(f"Response saved to history: {response.response_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to save response to Redis: {e}")
                # Fallback to memory
                return self._save_to_memory(key, response_json)
        else:
            return self._save_to_memory(key, response_json)

    def _save_to_memory(self, key: str, response_json: str) -> bool:
        """
        Yanıtı memory'ye kaydet (fallback).

        Args:
            key: Storage key
            response_json: JSON response

        Returns:
            bool: Başarılı mı
        """
        if key not in self._memory_store:
            self._memory_store[key] = []

        self._memory_store[key].insert(0, response_json)

        # Sınırla
        self._memory_store[key] = self._memory_store[key][:self.max_history_size]

        return True

    async def get_recent_responses(
        self,
        user_id: str,
        agent_type: str,
        limit: int = 10,
    ) -> List[AgentResponse]:
        """
        Son yanıtları al.

        Args:
            user_id: Kullanıcı ID
            agent_type: Agent tipi
            limit: Maksimum sonuç sayısı

        Returns:
            List[AgentResponse]: Yanıt listesi
        """
        key = self._get_key(user_id, agent_type)

        responses = []

        if self.redis_client:
            try:
                # Redis'ten al
                items = await self.redis_client.lrange(key, 0, limit - 1)

                for item in items:
                    try:
                        if isinstance(item, bytes):
                            item = item.decode('utf-8')
                        response = AgentResponse.model_validate_json(item)
                        responses.append(response)
                    except Exception as e:
                        logger.warning(f"Failed to parse response: {e}")
                        continue

            except Exception as e:
                logger.error(f"Failed to get responses from Redis: {e}")
                # Fallback to memory
                responses = self._get_from_memory(key, limit)
        else:
            responses = self._get_from_memory(key, limit)

        return responses

    def _get_from_memory(
        self, key: str, limit: int
    ) -> List[AgentResponse]:
        """
        Memory'den yanıtları al (fallback).

        Args:
            key: Storage key
            limit: Limit

        Returns:
            List[AgentResponse]: Yanıt listesi
        """
        responses = []

        items = self._memory_store.get(key, [])[:limit]

        for item in items:
            try:
                response = AgentResponse.model_validate_json(item)
                responses.append(response)
            except Exception:
                continue

        return responses

    async def get_response_count(
        self, user_id: str, agent_type: str
    ) -> int:
        """
        Yanıt sayısını al.

        Args:
            user_id: Kullanıcı ID
            agent_type: Agent tipi

        Returns:
            int: Yanıt sayısı
        """
        key = self._get_key(user_id, agent_type)

        if self.redis_client:
            try:
                return await self.redis_client.llen(key)
            except Exception:
                pass

        return len(self._memory_store.get(key, []))

    async def clear_history(
        self, user_id: str, agent_type: str
    ) -> bool:
        """
        Geçmişi temizle.

        Args:
            user_id: Kullanıcı ID
            agent_type: Agent tipi

        Returns:
            bool: Başarılı mı
        """
        key = self._get_key(user_id, agent_type)

        if self.redis_client:
            try:
                await self.redis_client.delete(key)
                return True
            except Exception:
                pass

        if key in self._memory_store:
            del self._memory_store[key]

        return True

    async def get_all_user_history(
        self, user_id: str
    ) -> dict:
        """
        Kullanıcının tüm agent geçmişlerini al.

        Args:
            user_id: Kullanıcı ID

        Returns:
            dict: Agent tipi -> yanıt listesi
        """
        agent_types = ["learning_path", "study_buddy", "exam"]
        history = {}

        for agent_type in agent_types:
            responses = await self.get_recent_responses(
                user_id, agent_type, limit=10
            )
            if responses:
                history[agent_type] = responses

        return history
