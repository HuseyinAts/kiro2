"""
Redis Health Checker Unit Tests

Bu modul, RedisHealthChecker sinifinin unit testlerini icerir.
Task 6.3b - Optional tests for api-endpoint-saglik spec.

Requirements Tested:
    REQ-6.1: PING komutu ile health check
    REQ-6.2: Hit rate, miss rate, eviction rate olcumu
    REQ-6.3: Hit rate %70 altinda -> cache stratejisi onerisi
    REQ-6.4: Memory usage %90 ustunde -> eviction uyarisi
    REQ-6.5: Redis unreachable -> cache bypass mode
    REQ-6.6: Cache recovery -> cache warming baslat
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.health.dependencies.redis_health import RedisHealthChecker, RedisHealthMetrics


class TestRedisHealthMetrics:
    """RedisHealthMetrics dataclass testleri."""

    def test_metrics_default_timestamp(self):
        """Timestamp varsayilan olarak simdi olmali."""
        before = datetime.now(UTC)
        metrics = RedisHealthMetrics(is_healthy=True, response_time_ms=5.0)
        after = datetime.now(UTC)

        assert metrics.timestamp is not None
        assert before <= metrics.timestamp <= after

    def test_metrics_all_fields_populated(self):
        """Tum alanlar dogru degerlerle doldurulmali."""
        metrics = RedisHealthMetrics(
            is_healthy=True,
            response_time_ms=2.5,
            hit_rate=0.85,
            miss_rate=0.15,
            eviction_rate=0.01,
            memory_used_bytes=100 * 1024 * 1024,
            memory_max_bytes=256 * 1024 * 1024,
            memory_usage_percent=39.06,
            connected_clients=10,
            timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
            error_message=None
        )

        assert metrics.is_healthy is True
        assert metrics.response_time_ms == 2.5
        assert metrics.hit_rate == 0.85
        assert metrics.miss_rate == 0.15
        assert metrics.eviction_rate == 0.01
        assert metrics.memory_used_bytes == 100 * 1024 * 1024
        assert metrics.memory_max_bytes == 256 * 1024 * 1024
        assert metrics.connected_clients == 10
        assert metrics.error_message is None

    def test_metrics_with_error_message(self):
        """Hata mesaji dogru saklanmali."""
        metrics = RedisHealthMetrics(
            is_healthy=False,
            response_time_ms=0.0,
            error_message="Connection refused"
        )

        assert metrics.is_healthy is False
        assert metrics.error_message == "Connection refused"


class TestRedisHealthCheckerInit:
    """RedisHealthChecker initialization testleri."""

    def test_initialization_defaults(self):
        """Varsayilan degerlerle baslatilmali."""
        mock_client = MagicMock()

        checker = RedisHealthChecker(redis_client=mock_client)

        assert checker.redis_client == mock_client
        assert checker.hit_rate_threshold == 0.70
        assert checker.memory_warning_threshold == 90.0
        assert checker._bypass_mode is False
        assert checker._warming_callbacks == []

    def test_initialization_custom_thresholds(self):
        """Ozel esiklerle baslatilmali."""
        mock_client = MagicMock()

        checker = RedisHealthChecker(
            redis_client=mock_client,
            hit_rate_threshold=0.80,
            memory_warning_threshold=85.0
        )

        assert checker.hit_rate_threshold == 0.80
        assert checker.memory_warning_threshold == 85.0


class TestRedisHealthCheckerCheckHealth:
    """check_health method testleri."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        client = AsyncMock()
        client.ping = AsyncMock(return_value=True)
        client.info = AsyncMock(side_effect=self._mock_info)
        client.dbsize = AsyncMock(return_value=1000)
        client.hset = AsyncMock(return_value=True)
        client.expire = AsyncMock(return_value=True)
        client.lpush = AsyncMock(return_value=1)
        client.ltrim = AsyncMock(return_value=True)
        client.set = AsyncMock(return_value=True)
        return client

    @staticmethod
    def _mock_info(section):
        """Mock Redis info response."""
        if section == "stats":
            return {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 10
            }
        if section == "clients":
            return {"connected_clients": 5}
        if section == "memory":
            return {
                "used_memory": 100 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 120 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.1
            }
        return {}

    @pytest.mark.asyncio
    async def test_check_health_ping_success(self, mock_redis_client):
        """
        Basarili PING ile health check testi.
        REQ-6.1: PING komutu ile health check
        """
        checker = RedisHealthChecker(redis_client=mock_redis_client)

        metrics = await checker.check_health()

        assert metrics.is_healthy is True
        assert metrics.response_time_ms >= 0
        assert metrics.error_message is None
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health_ping_failure(self):
        """PING basarisiz olursa healthy=False donmeli."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=False)

        checker = RedisHealthChecker(redis_client=mock_client)

        metrics = await checker.check_health()

        assert metrics.is_healthy is False
        assert "PING failed" in str(metrics.error_message)

    @pytest.mark.asyncio
    async def test_check_health_connection_error(self):
        """Baglanti hatasi durumunda healthy=False donmeli."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))

        checker = RedisHealthChecker(redis_client=mock_client)

        metrics = await checker.check_health()

        assert metrics.is_healthy is False
        assert "Connection refused" in metrics.error_message

    @pytest.mark.asyncio
    async def test_response_time_measurement(self, mock_redis_client):
        """Response time dogru olculur."""
        checker = RedisHealthChecker(redis_client=mock_redis_client)

        metrics = await checker.check_health()

        # Response time pozitif olmali
        assert metrics.response_time_ms >= 0
        assert metrics.response_time_ms < 10000  # 10 saniyeden az


class TestRedisHealthCheckerCacheMetrics:
    """Cache metrikleri testleri."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client with cache metrics."""
        client = AsyncMock()
        client.ping = AsyncMock(return_value=True)
        client.dbsize = AsyncMock(return_value=1000)
        client.hset = AsyncMock(return_value=True)
        client.expire = AsyncMock(return_value=True)
        return client

    @pytest.mark.asyncio
    async def test_get_cache_metrics_success(self, mock_redis_client):
        """
        Cache metrikleri dogru alinir.
        REQ-6.2: Hit rate, miss rate, eviction rate olcumu
        """
        mock_redis_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 10
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 100 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 120 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.1
            }
        }.get(s, {}))

        checker = RedisHealthChecker(redis_client=mock_redis_client)

        metrics = await checker.check_health()

        # 8000 / 10000 = 0.8 hit rate
        assert metrics.hit_rate == 0.8
        # 2000 / 10000 = 0.2 miss rate
        assert metrics.miss_rate == 0.2
        # 10 / 1000 = 0.01 eviction rate
        assert metrics.eviction_rate == 0.01

    @pytest.mark.asyncio
    async def test_hit_rate_calculation_zero_total(self, mock_redis_client):
        """Total 0 iken hit rate 0 olmali."""
        mock_redis_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {"keyspace_hits": 0, "keyspace_misses": 0, "evicted_keys": 0},
            "clients": {"connected_clients": 1},
            "memory": {
                "used_memory": 10 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 10 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.0
            }
        }.get(s, {}))

        checker = RedisHealthChecker(redis_client=mock_redis_client)

        metrics = await checker.check_health()

        assert metrics.hit_rate == 0.0
        assert metrics.miss_rate == 0.0


class TestRedisHealthCheckerHitRateWarning:
    """Hit rate uyarisi testleri."""

    @pytest.fixture
    def mock_redis_client_low_hit_rate(self):
        """Mock Redis client with low hit rate."""
        client = AsyncMock()
        client.ping = AsyncMock(return_value=True)
        client.dbsize = AsyncMock(return_value=1000)
        client.hset = AsyncMock(return_value=True)
        client.expire = AsyncMock(return_value=True)
        client.lpush = AsyncMock(return_value=1)
        client.ltrim = AsyncMock(return_value=True)

        # Low hit rate: 50%
        client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 5000,
                "keyspace_misses": 5000,
                "evicted_keys": 10
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 100 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 120 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.1
            }
        }.get(s, {}))

        return client

    @pytest.mark.asyncio
    async def test_low_hit_rate_warning_triggered(self, mock_redis_client_low_hit_rate):
        """
        Dusuk hit rate'de uyari tetiklenmeli.
        REQ-6.3: Hit rate %70 altinda -> cache stratejisi onerisi
        """
        checker = RedisHealthChecker(
            redis_client=mock_redis_client_low_hit_rate,
            hit_rate_threshold=0.70
        )

        metrics = await checker.check_health()

        # Hit rate 0.5 < 0.7 threshold
        assert metrics.hit_rate < 0.70
        # Alert kaydedilmeli
        mock_redis_client_low_hit_rate.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_no_warning_above_threshold(self):
        """Hit rate threshold ustunde uyari olmamali."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.dbsize = AsyncMock(return_value=1000)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.lpush = AsyncMock(return_value=1)

        # High hit rate: 90%
        mock_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 9000,
                "keyspace_misses": 1000,
                "evicted_keys": 5
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 50 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 60 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.0
            }
        }.get(s, {}))

        checker = RedisHealthChecker(
            redis_client=mock_client,
            hit_rate_threshold=0.70
        )

        await checker.check_health()

        # lpush alert icin cagrilmamali (sadece metrics icin hset cagrilir)
        # lpush'un alert key'i ile cagrilip cagrilmadigini kontrol et
        lpush_calls = mock_client.lpush.call_args_list
        alert_calls = [c for c in lpush_calls if "alerts:redis" in str(c)]
        assert len(alert_calls) == 0


class TestRedisHealthCheckerMemoryWarning:
    """Memory uyarisi testleri."""

    @pytest.mark.asyncio
    async def test_high_memory_usage_warning(self):
        """
        Yuksek memory kullanimi uyarisi tetiklenmeli.
        REQ-6.4: Memory usage %90 ustunde -> eviction uyarisi
        """
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.dbsize = AsyncMock(return_value=1000)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.lpush = AsyncMock(return_value=1)

        # High memory: 95%
        mock_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 100
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 243 * 1024 * 1024,  # ~95% of 256MB
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 250 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.2
            }
        }.get(s, {}))

        checker = RedisHealthChecker(
            redis_client=mock_client,
            memory_warning_threshold=90.0
        )

        metrics = await checker.check_health()

        # Memory usage > 90%
        assert metrics.memory_usage_percent > 90.0
        # Critical alert kaydedilmeli
        mock_client.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_memory_percentage_calculation(self):
        """Memory yuzde hesaplamasi dogru yapilmali."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.dbsize = AsyncMock(return_value=1000)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.expire = AsyncMock(return_value=True)

        # 128MB used / 256MB max = 50%
        mock_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 10
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 128 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 130 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.0
            }
        }.get(s, {}))

        checker = RedisHealthChecker(redis_client=mock_client)

        metrics = await checker.check_health()

        # 50% memory usage
        assert 49.0 <= metrics.memory_usage_percent <= 51.0


class TestRedisHealthCheckerBypassMode:
    """Bypass mode testleri."""

    @pytest.mark.asyncio
    async def test_bypass_mode_activated_on_unavailable(self):
        """
        Redis unavailable olunca bypass mode aktif olmali.
        REQ-6.5: Redis unreachable -> cache bypass mode
        """
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))

        checker = RedisHealthChecker(redis_client=mock_client)

        assert checker.is_bypass_mode() is False

        await checker.check_health()

        assert checker.is_bypass_mode() is True

    @pytest.mark.asyncio
    async def test_is_redis_available_in_bypass_mode(self):
        """Bypass mode'da is_redis_available False donmeli."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))

        checker = RedisHealthChecker(redis_client=mock_client)

        # Bypass mode'a sok
        await checker.check_health()

        result = await checker.is_redis_available()

        assert result is False
        # Bypass mode'da ping bile cagrilmamali (2. kez)
        assert mock_client.ping.call_count == 1  # Sadece check_health'den

    @pytest.mark.asyncio
    async def test_is_redis_available_ping_check(self):
        """Bypass mode degilken ping ile kontrol yapilmali."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        checker = RedisHealthChecker(redis_client=mock_client)

        result = await checker.is_redis_available()

        assert result is True
        mock_client.ping.assert_called()


class TestRedisHealthCheckerCacheWarming:
    """Cache warming testleri."""

    @pytest.mark.asyncio
    async def test_cache_warming_triggered_on_recovery(self):
        """
        Cache recovery'de warming callback'leri cagrilmali.
        REQ-6.6: Cache recovery -> cache warming baslat
        """
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.dbsize = AsyncMock(return_value=1000)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.set = AsyncMock(return_value=True)

        mock_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 10
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 100 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 120 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.1
            }
        }.get(s, {}))

        checker = RedisHealthChecker(redis_client=mock_client)

        # Warming callback kaydet
        warming_callback = AsyncMock()
        checker.register_warming_callback(warming_callback)

        # Bypass mode'a sok
        checker._bypass_mode = True

        # Recovery - check_health bypass'tan cikarir
        await checker.check_health()

        # Bypass mode kapanmali
        assert checker.is_bypass_mode() is False
        # Warming callback cagrilmali
        warming_callback.assert_called_once()

    def test_register_warming_callback(self):
        """Warming callback dogru kaydedilmeli."""
        mock_client = MagicMock()

        checker = RedisHealthChecker(redis_client=mock_client)

        callback1 = MagicMock()
        callback2 = MagicMock()

        checker.register_warming_callback(callback1)
        checker.register_warming_callback(callback2)

        assert len(checker._warming_callbacks) == 2
        assert callback1 in checker._warming_callbacks
        assert callback2 in checker._warming_callbacks

    @pytest.mark.asyncio
    async def test_warming_callback_error_handled(self):
        """Warming callback hatasi diger callback'leri etkilememeli."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.dbsize = AsyncMock(return_value=1000)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.set = AsyncMock(return_value=True)

        mock_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 10
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 100 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 120 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.1
            }
        }.get(s, {}))

        checker = RedisHealthChecker(redis_client=mock_client)

        # Hata veren callback
        failing_callback = AsyncMock(side_effect=Exception("Warming failed"))
        # Normal callback
        success_callback = AsyncMock()

        checker.register_warming_callback(failing_callback)
        checker.register_warming_callback(success_callback)

        # Bypass mode'a sok
        checker._bypass_mode = True

        # Recovery - hata olsa bile devam etmeli
        await checker.check_health()

        # Her iki callback da cagrilmali
        failing_callback.assert_called_once()
        success_callback.assert_called_once()


class TestRedisHealthCheckerMetricsStorage:
    """Metrics storage testleri."""

    @pytest.mark.asyncio
    async def test_store_metrics_to_redis(self):
        """Metrikler Redis'e dogru kaydedilmeli."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.dbsize = AsyncMock(return_value=1000)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.expire = AsyncMock(return_value=True)

        mock_client.info = AsyncMock(side_effect=lambda s: {
            "stats": {
                "keyspace_hits": 8000,
                "keyspace_misses": 2000,
                "evicted_keys": 10
            },
            "clients": {"connected_clients": 5},
            "memory": {
                "used_memory": 100 * 1024 * 1024,
                "maxmemory": 256 * 1024 * 1024,
                "total_system_memory": 8 * 1024 * 1024 * 1024,
                "used_memory_peak": 120 * 1024 * 1024,
                "mem_fragmentation_ratio": 1.1
            }
        }.get(s, {}))

        checker = RedisHealthChecker(redis_client=mock_client)

        await checker.check_health()

        # hset cagrilmali
        mock_client.hset.assert_called()
        # expire cagrilmali
        mock_client.expire.assert_called()

        # Dogru key kullanilmali
        hset_call = mock_client.hset.call_args
        assert "kiro2:health:redis:metrics" in str(hset_call)

    @pytest.mark.asyncio
    async def test_store_metrics_not_called_when_unhealthy(self):
        """Unhealthy durumda metrikler kaydedilmemeli."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.hset = AsyncMock(return_value=True)

        checker = RedisHealthChecker(redis_client=mock_client)

        await checker.check_health()

        # Unhealthy durumda hset cagrilmamali
        mock_client.hset.assert_not_called()
