"""
CLAUDE.md Self-Improvement Cache Layer Unit Tests.

Bu modül cache.py için kapsamlı testler içerir:
- REQ-10.6: Redis cache entegrasyonu
- InMemoryCache fallback mekanizması
- TTL ve eviction politikaları

Boris Cherny Standards - Verification Feedback Loops
"""

import os
import sys

# Backend dizinini Python path'e ekle (import öncesi)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from hooks.claude_md_improvement.cache import (
    CacheConfig,
    CacheKeyPrefix,
    ImprovementCache,
    InMemoryCache,
    create_cache,
)

# =============================================================================
# CACHE CONFIG TESTLERİ
# =============================================================================

class TestCacheConfig:
    """CacheConfig dataclass testleri."""

    def test_default_values(self):
        """Default değerler doğru."""
        config = CacheConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None

    def test_ttl_defaults(self):
        """TTL default değerleri."""
        config = CacheConfig()
        assert config.rule_effectiveness_ttl == 3600  # 1 saat
        assert config.pattern_ttl == 7200  # 2 saat
        assert config.feedback_ttl == 86400  # 24 saat

    def test_redis_url_without_password(self):
        """Password olmadan Redis URL."""
        config = CacheConfig(host="myhost", port=6380, db=1)
        assert config.redis_url == "redis://myhost:6380/1"

    def test_redis_url_with_password(self):
        """Password ile Redis URL."""
        config = CacheConfig(password="secret123")
        assert "secret123" in config.redis_url
        assert config.redis_url.startswith("redis://:")

    def test_custom_config(self):
        """Özel konfigürasyon."""
        config = CacheConfig(
            host="redis.example.com",
            port=6380,
            db=5,
            password="mypassword",
            max_connections=20,
        )
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.max_connections == 20


class TestCacheKeyPrefix:
    """CacheKeyPrefix enum testleri."""

    def test_all_prefixes_defined(self):
        """Tüm prefix'ler tanımlı."""
        assert CacheKeyPrefix.RULE_EFFECTIVENESS.value == "claude_md:rule_eff"
        assert CacheKeyPrefix.PATTERN.value == "claude_md:pattern"
        assert CacheKeyPrefix.FEEDBACK.value == "claude_md:feedback"
        assert CacheKeyPrefix.AB_TEST.value == "claude_md:ab_test"


# =============================================================================
# IN-MEMORY CACHE TESTLERİ
# =============================================================================

class TestInMemoryCache:
    """InMemoryCache testleri."""

    def test_basic_set_get(self):
        """Temel set/get operasyonu."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Olmayan key None döner."""
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """TTL süresi dolunca değer silinir."""
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl=1)  # 1 saniye

        # Hemen erişim
        assert cache.get("key1") == "value1"

        # TTL simulasyonu için expires_at'ı değiştir
        cache._cache["key1"].expires_at = datetime.now(UTC) - timedelta(seconds=1)

        # Artık None döner
        assert cache.get("key1") is None

    def test_delete_key(self):
        """Key silme."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_nonexistent_key(self):
        """Olmayan key silme."""
        cache = InMemoryCache()
        assert cache.delete("nonexistent") is False

    def test_clear_all(self):
        """Tüm cache'i temizle."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_max_size_eviction(self):
        """Max size aşılınca eviction."""
        cache = InMemoryCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # key1 silinmeli

        # En az bir key silinmiş olmalı
        assert len(cache._cache) <= 3

    def test_complex_values(self):
        """Karmaşık değerler saklanabilir."""
        cache = InMemoryCache()

        # Dict
        cache.set("dict_key", {"nested": {"value": 123}})
        assert cache.get("dict_key")["nested"]["value"] == 123

        # List
        cache.set("list_key", [1, 2, 3])
        assert cache.get("list_key") == [1, 2, 3]


# =============================================================================
# IMPROVEMENT CACHE TESTLERİ
# =============================================================================

class TestImprovementCache:
    """ImprovementCache async testleri."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.close = AsyncMock()
        redis.ping = AsyncMock(return_value=True)
        return redis

    def test_initialization(self):
        """Cache initialization."""
        cache = ImprovementCache()
        assert cache.config is not None
        assert cache.is_connected is False

    def test_custom_config(self):
        """Özel config ile initialization."""
        config = CacheConfig(host="custom-host", port=6380)
        cache = ImprovementCache(config=config)
        assert cache.config.host == "custom-host"
        assert cache.config.port == 6380

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_redis):
        """Başarılı bağlantı simülasyonu."""
        cache = ImprovementCache()
        # Simüle bağlantı
        cache._redis = mock_redis
        cache._connected = True

        assert cache.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_redis):
        """Cache bağlantısını kapatma."""
        cache = ImprovementCache()
        cache._redis = mock_redis
        cache._connected = True

        await cache.disconnect()

        mock_redis.close.assert_called_once()
        assert cache.is_connected is False

    def test_make_key(self):
        """Cache key oluşturma."""
        cache = ImprovementCache()
        key = cache._make_key(CacheKeyPrefix.RULE_EFFECTIVENESS, "rule-001")
        assert key == "claude_md:rule_eff:rule-001"

    def test_hash_content(self):
        """İçerik hash'i."""
        cache = ImprovementCache()
        hash1 = cache._hash_content("test content")
        hash2 = cache._hash_content("test content")
        hash3 = cache._hash_content("different content")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 12

    @pytest.mark.asyncio
    async def test_get_rule_effectiveness_not_connected(self):
        """Bağlı değilken get None döner."""
        cache = ImprovementCache()
        cache._connected = False

        result = await cache.get_rule_effectiveness("rule-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_rule_effectiveness_not_connected(self):
        """Bağlı değilken set False döner."""
        cache = ImprovementCache()
        cache._connected = False

        result = await cache.set_rule_effectiveness("rule-001", 0.9)
        assert result is False


# =============================================================================
# CREATE_CACHE FABRİKA FONKSİYONU TESTLERİ
# =============================================================================

class TestCreateCache:
    """create_cache() factory fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_create_without_redis(self):
        """Redis olmadan InMemoryCache oluştur."""
        cache = await create_cache(use_redis=False)
        assert isinstance(cache, InMemoryCache)

    @pytest.mark.asyncio
    async def test_create_with_custom_config(self):
        """Özel config ile oluştur."""
        config = CacheConfig(host="custom-host")
        cache = await create_cache(use_redis=False, config=config)
        assert isinstance(cache, InMemoryCache)


# =============================================================================
# EDGE CASE TESTLERİ
# =============================================================================

class TestCacheEdgeCases:
    """Edge case testleri."""

    def test_empty_key(self):
        """Boş key."""
        cache = InMemoryCache()
        cache.set("", "value")
        assert cache.get("") == "value"

    def test_none_value(self):
        """None değer saklanabilir."""
        cache = InMemoryCache()
        cache.set("key", None)
        # None değer get'te None döner ama key var
        assert "key" in cache._cache

    def test_unicode_key(self):
        """Unicode key."""
        cache = InMemoryCache()
        cache.set("türkçe-key", "değer")
        assert cache.get("türkçe-key") == "değer"

    def test_unicode_value(self):
        """Unicode değer."""
        cache = InMemoryCache()
        cache.set("key", "Türkçe içerik: şğüöçı")
        assert "Türkçe" in cache.get("key")

    def test_large_value(self):
        """Büyük değer."""
        cache = InMemoryCache()
        large_value = "x" * 1000000  # 1MB
        cache.set("key", large_value)
        assert len(cache.get("key")) == 1000000


# =============================================================================
# INTEGRATION SİMÜLASYON TESTLERİ
# =============================================================================

class TestCacheIntegration:
    """Cache integration simülasyon testleri."""

    @pytest.mark.asyncio
    async def test_rule_effectiveness_workflow(self):
        """Rule effectiveness cache workflow."""
        # InMemoryCache kullan (Redis mocklamadan)
        cache = InMemoryCache()

        # Set
        cache.set("claude_md:rule_eff:rule-001", "0.85")

        # Get
        value = cache.get("claude_md:rule_eff:rule-001")
        assert value == "0.85"

    @pytest.mark.asyncio
    async def test_pattern_cache_workflow(self):
        """Pattern cache workflow."""
        cache = InMemoryCache()

        pattern_data = {
            "pattern_id": "p-001",
            "frequency": 10,
            "rules": ["r1", "r2"],
        }
        cache.set("claude_md:pattern:p-001", pattern_data)

        result = cache.get("claude_md:pattern:p-001")
        assert result["frequency"] == 10

    @pytest.mark.asyncio
    async def test_feedback_batch_cache(self):
        """Feedback batch cache."""
        cache = InMemoryCache()

        feedbacks = [
            {"task_id": "t1", "success": True},
            {"task_id": "t2", "success": False},
        ]
        cache.set("claude_md:feedback:batch-001", feedbacks, ttl=86400)

        result = cache.get("claude_md:feedback:batch-001")
        assert len(result) == 2
