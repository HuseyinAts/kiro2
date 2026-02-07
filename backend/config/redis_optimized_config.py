# Optimized Redis Configuration for KIRO2
# Target: Sub-millisecond latency

import logging
import os
import pickle
import zlib
from typing import Optional, Any

import redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)


class OptimizedRedisConfig:
    REDIS_CONFIG = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "max_connections": 50,
        "socket_keepalive": True,
        "socket_timeout": 5,
        "decode_responses": False
    }
    
    TTL_STRATEGIES = {
        "hot": 300,
        "warm": 3600,
        "cold": 86400,
        "session": 1800
    }


class RedisConnectionPool:
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            if cls._pool is None:
                cls._pool = ConnectionPool(**OptimizedRedisConfig.REDIS_CONFIG)
            cls._client = redis.Redis(connection_pool=cls._pool)
        return cls._client


class CompressedRedisCache:
    def __init__(self, compression_threshold: int = 1024):
        self.client = RedisConnectionPool.get_client()
        self.compression_threshold = compression_threshold
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, compress: bool = True) -> bool:
        try:
            serialized = pickle.dumps(value)
            
            if compress and len(serialized) > self.compression_threshold:
                compressed = zlib.compress(serialized, level=6)
                data = b'C' + compressed
            else:
                data = b'U' + serialized
            
            if ttl:
                return self.client.setex(key, ttl, data)
            else:
                return self.client.set(key, data)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if not data:
                return None
            
            if data[0:1] == b'C':
                return pickle.loads(zlib.decompress(data[1:]))
            else:
                return pickle.loads(data[1:])
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def delete(self, *keys: str) -> int:
        try:
            return self.client.delete(*keys)
        except (ConnectionError, OSError) as e:
            logger.debug(f"Redis delete failed: {e}")
            return 0
    
    def pipeline(self):
        return self.client.pipeline()
